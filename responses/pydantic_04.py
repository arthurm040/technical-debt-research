import re
from ipaddress import (
    IPv4Address,
    IPv4Interface,
    IPv4Network,
    IPv6Address,
    IPv6Interface,
    IPv6Network,
    _BaseAddress,
    _BaseNetwork,
)
from typing import TYPE_CHECKING, Any, Dict, Generator, Optional, Set, Tuple, Type, Union, cast, no_type_check

from . import errors
from .utils import Representation
from .validators import constr_length_validator, str_validator

if TYPE_CHECKING:
    from .fields import ModelField
    from .main import BaseConfig
    from .typing import AnyCallable

    CallableGenerator = Generator[AnyCallable, None, None]

# Regex and Constants
host_part_names = ("domain", "ipv4", "ipv6")
url_regex = re.compile(
    r"(?:(?P<scheme>[a-z0-9]+?)://)?"
    r"(?:(?P<user>[^\s:]+)(?::(?P<password>\S*))?@)?"
    r"(?:"
    r"(?P<ipv4>(?:\d{1,3}\.){3}\d{1,3})|"
    r"(?P<ipv6>\[[A-F0-9]*:[A-F0-9:]+\])|"
    r"(?P<domain>[^\s/:?#]+)"
    r")?"
    r"(?::(?P<port>\d+))?"
    r"(?P<path>/[^\s?]*)?"
    r"(?:\?(?P<query>[^\s#]+))?"
    r"(?:#(?P<fragment>\S+))?",
    re.IGNORECASE,
)
_ascii_chunk = r"[_0-9a-z](?:[-_0-9a-z]{0,61}[_0-9a-z])?"
_domain_ending = r"(?P<tld>\.[a-z]{2,63})?\.?"
ascii_domain_regex = re.compile(rf"(?:{_ascii_chunk}\.)*?{_ascii_chunk}{_domain_ending}", re.IGNORECASE)

_int_chunk = r"[_0-9a-\U00040000](?:[-_0-9a-\U00040000]{0,61}[_0-9a-\U00040000])?"
int_domain_regex = re.compile(rf"(?:{_int_chunk}\.)*?{_int_chunk}{_domain_ending}", re.IGNORECASE)


### The New Architecture


class UrlConstraints(Representation):
    """
    A single configurable class to handle all URL validation parameters.
    """

    __slots__ = ("max_length", "allowed_schemes", "host_required", "tld_required", "user_required", "strip_whitespace")

    def __init__(
        self,
        max_length: int = 2**16,
        allowed_schemes: Optional[Set[str]] = None,
        host_required: bool = True,
        tld_required: bool = False,
        user_required: bool = False,
        strip_whitespace: bool = True,
    ) -> None:
        self.max_length = max_length
        self.allowed_schemes = allowed_schemes
        self.host_required = host_required
        self.tld_required = tld_required
        self.user_required = user_required
        self.strip_whitespace = strip_whitespace


class AnyUrl(str):
    __slots__ = ("scheme", "user", "password", "host", "tld", "host_type", "port", "path", "query", "fragment")

    @no_type_check
    def __new__(cls, url: Optional[str], **kwargs) -> object:
        return str.__new__(cls, cls.build(**kwargs) if url is None else url)

    def __init__(self, url: str, **parts: Any) -> None:
        str.__init__(url)
        for key, value in parts.items():
            setattr(self, key, value)

    @classmethod
    def build(cls, *, scheme: str, host: str, **kwargs: Any) -> str:
        user_info = f"{kwargs.get('user', '')}"
        if kwargs.get("password"):
            user_info += f":{kwargs['password']}"
        user_info = f"{user_info}@" if user_info else ""

        port = f":{kwargs['port']}" if kwargs.get("port") else ""
        url = f"{scheme}://{user_info}{host}{port}{kwargs.get('path', '')}"
        if kwargs.get("query"):
            url += f"?{kwargs['query']}"
        if kwargs.get("fragment"):
            url += f"#{kwargs['fragment']}"
        return url

    @classmethod
    def __get_validators__(cls) -> "CallableGenerator":
        yield cls.validate

    @classmethod
    def validate(
        cls, value: Any, field: "ModelField", config: "BaseConfig", constraints: Optional[UrlConstraints] = None
    ) -> "AnyUrl":
        if isinstance(value, cls):
            return value

        # Use field-level constraints or default
        constraints = constraints or getattr(field.type_, "constraints", UrlConstraints())

        value = str_validator(value)
        if constraints.strip_whitespace:
            value = value.strip()

        url: str = cast(str, constr_length_validator(value, field, config))
        if len(url) > constraints.max_length:
            raise errors.UrlLengthError(limit=constraints.max_length)

        m = url_regex.match(url)
        assert m, "URL regex failed unexpectedly"
        parts = m.groupdict()

        # Scheme Validation
        scheme = parts["scheme"]
        if not scheme:
            raise errors.UrlSchemeError()
        if constraints.allowed_schemes and scheme.lower() not in constraints.allowed_schemes:
            raise errors.UrlSchemePermittedError(constraints.allowed_schemes)

        # User Validation
        if constraints.user_required and parts["user"] is None:
            raise errors.UrlUserInfoError()

        # Host Validation
        host, tld, host_type, rebuild = cls.validate_host(parts, constraints)

        return cls(
            None if rebuild else url,
            scheme=scheme,
            user=parts["user"],
            password=parts["password"],
            host=host,
            tld=tld,
            host_type=host_type,
            port=parts["port"],
            path=parts["path"],
            query=parts["query"],
            fragment=parts["fragment"],
        )

    @classmethod
    def validate_host(cls, parts: Dict[str, str], constraints: UrlConstraints) -> Tuple[str, Optional[str], str, bool]:
        host, tld, host_type, rebuild = None, None, None, False
        for f in host_part_names:
            if parts[f]:
                host, host_type = parts[f], f
                break

        if host is None and constraints.host_required:
            raise errors.UrlHostError()

        if host_type == "domain":
            d = ascii_domain_regex.fullmatch(host) or int_domain_regex.fullmatch(host)
            if not d:
                raise errors.UrlHostError()

            if not host.isascii():
                host_type, rebuild = "int_domain", True
                host = host.encode("idna").decode("ascii")

            tld = d.group("tld")[1:] if d.group("tld") else None
            if not tld and constraints.tld_required:
                raise errors.UrlHostTldError()

        return host, tld, host_type, rebuild  # type: ignore


### Simplified Type Definitions


# Helper to generate constrained types
def create_url_type(name: str, **kwargs: Any) -> Type[AnyUrl]:
    return type(name, (AnyUrl,), {"constraints": UrlConstraints(**kwargs)})


# Standard URL types
HttpUrl = create_url_type("HttpUrl", allowed_schemes={"http", "https"}, tld_required=True, max_length=2083)
PostgresDsn = create_url_type("PostgresDsn", allowed_schemes={"postgres", "postgresql"}, user_required=True)
RedisDsn = create_url_type("RedisDsn", allowed_schemes={"redis"}, user_required=True)


# stricturl is now just a wrapper for create_url_type
def stricturl(**kwargs: Any) -> Type[AnyUrl]:
    return create_url_type("UrlValue", **kwargs)
