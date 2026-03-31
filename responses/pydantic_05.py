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
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Generator,
    Optional,
    Set,
    Tuple,
    Type,
    Union,
    cast,
    no_type_check,
)

from . import errors
from .utils import Representation
from .validators import constr_length_validator, str_validator

if TYPE_CHECKING:
    from .fields import ModelField
    from .main import BaseConfig
    from .typing import AnyCallable

    CallableGenerator = Generator[AnyCallable, None, None]

try:
    import email_validator
except ImportError:
    email_validator = None

NetworkType = Union[str, bytes, int, Tuple[Union[str, bytes, int], Union[str, int]]]

__all__ = [
    "AnyUrl",
    "AnyHttpUrl",
    "HttpUrl",
    "stricturl",
    "EmailStr",
    "NameEmail",
    "IPvAnyAddress",
    "IPvAnyInterface",
    "IPvAnyNetwork",
    "PostgresDsn",
    "RedisDsn",
    "validate_email",
]

# Regex for initial structural parsing
url_regex = re.compile(
    r"(?:(?P<scheme>[a-z0-9]+?)://)?"  # scheme
    r"(?:(?P<user>[^\s:]+)(?::(?P<password>\S*))?@)?"  # user info
    r"(?:"
    r"(?P<ipv4>(?:\d{1,3}\.){3}\d{1,3})|"  # ipv4
    r"(?P<ipv6>\[[A-F0-9]*:[A-F0-9:]+\])|"  # ipv6
    r"(?P<domain>[^\s/:?#]+)"  # domain
    r")?"
    r"(?::(?P<port>\d+))?"  # port
    r"(?P<path>/[^\s?]*)?"  # path
    r"(?:\?(?P<query>[^\s#]+))?"  # query
    r"(?:#(?P<fragment>\S+))?",  # fragment
    re.IGNORECASE,
)

_ascii_chunk = r"[_0-9a-z](?:[-_0-9a-z]{0,61}[_0-9a-z])?"
_domain_ending = r"(?P<tld>\.[a-z]{2,63})?\.?"
ascii_domain_regex = re.compile(rf"(?:{_ascii_chunk}\.)*?{_ascii_chunk}{_domain_ending}", re.IGNORECASE)

_int_chunk = r"[_0-9a-\U00040000](?:[-_0-9a-\U00040000]{0,61}[_0-9a-\U00040000])?"
int_domain_regex = re.compile(rf"(?:{_int_chunk}\.)*?{_int_chunk}{_domain_ending}", re.IGNORECASE)

pretty_email_regex = re.compile(r"([\w ]*?) *<(.*)> *")


class AnyUrl(str):
    strip_whitespace = True
    min_length = 1
    max_length = 2**16
    allowed_schemes: Optional[Set[str]] = None
    tld_required: bool = False
    user_required: bool = False

    __slots__ = ("scheme", "user", "password", "host", "tld", "host_type", "port", "path", "query", "fragment")

    @no_type_check
    def __new__(cls, url: Optional[str], **kwargs) -> object:
        return str.__new__(cls, cls.build(**kwargs) if url is None else url)

    def __init__(
        self,
        url: str,
        *,
        scheme: str,
        user: Optional[str] = None,
        password: Optional[str] = None,
        host: str,
        tld: Optional[str] = None,
        host_type: str = "domain",
        port: Optional[str] = None,
        path: Optional[str] = None,
        query: Optional[str] = None,
        fragment: Optional[str] = None,
    ) -> None:
        str.__init__(url)
        self.scheme = scheme
        self.user = user
        self.password = password
        self.host = host
        self.tld = tld
        self.host_type = host_type
        self.port = port
        self.path = path
        self.query = query
        self.fragment = fragment

    @classmethod
    def build(
        cls,
        *,
        scheme: str,
        user: Optional[str] = None,
        password: Optional[str] = None,
        host: str,
        port: Optional[str] = None,
        path: Optional[str] = None,
        query: Optional[str] = None,
        fragment: Optional[str] = None,
        **kwargs: str,
    ) -> str:
        url = scheme + "://"
        if user:
            url += user
            if password:
                url += ":" + password
            url += "@"
        url += host
        if port:
            url += ":" + port
        if path:
            url += path
        if query:
            url += "?" + query
        if fragment:
            url += "#" + fragment
        return url

    @classmethod
    def __get_validators__(cls) -> "CallableGenerator":
        yield cls.validate

    @classmethod
    def validate(cls, value: Any, field: "ModelField", config: "BaseConfig") -> "AnyUrl":
        if isinstance(value, cls):
            return value
        value = str_validator(value)
        if cls.strip_whitespace:
            value = value.strip()
        url: str = cast(str, constr_length_validator(value, field, config))

        m = url_regex.match(url)
        assert m, "URL regex failed unexpectedly"

        parts = m.groupdict()

        # Modular Validation Pipeline
        scheme = cls._validate_scheme(parts["scheme"])
        user, password = cls._validate_user_info(parts["user"], parts["password"])
        host, tld, host_type, rebuild = cls.validate_host(parts)
        port = cls._validate_port(parts["port"])
        path = cls._validate_path(parts["path"])

        if m.end() != len(url):
            raise errors.UrlExtraError(extra=url[m.end() :])

        return cls(
            None if rebuild else url,
            scheme=scheme,
            user=user,
            password=password,
            host=host,
            tld=tld,
            host_type=host_type,
            port=port,
            path=path,
            query=parts["query"],
            fragment=parts["fragment"],
        )

    @classmethod
    def _validate_scheme(cls, scheme: Optional[str]) -> str:
        if scheme is None:
            raise errors.UrlSchemeError()
        scheme = scheme.lower()
        if cls.allowed_schemes and scheme not in cls.allowed_schemes:
            raise errors.UrlSchemePermittedError(cls.allowed_schemes)
        return scheme

    @classmethod
    def _validate_user_info(cls, user: Optional[str], password: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
        if cls.user_required and user is None:
            raise errors.UrlUserInfoError()
        return user, password

    @classmethod
    def _validate_port(cls, port: Optional[str]) -> Optional[str]:
        if port is None:
            return None
        try:
            p = int(port)
            if 0 < p <= 65535:
                return port
        except ValueError:
            pass
        raise errors.UrlPortError()

    @classmethod
    def _validate_path(cls, path: Optional[str]) -> Optional[str]:
        if path is not None and not path.startswith("/"):
            return "/" + path
        return path

    @classmethod
    def validate_host(cls, parts: Dict[str, Any]) -> Tuple[str, Optional[str], str, bool]:
        host, tld, host_type, rebuild = None, None, None, False
        for f in ("domain", "ipv4", "ipv6"):
            host = parts[f]
            if host:
                host_type = f
                break

        if host is None:
            raise errors.UrlHostError()
        elif host_type == "domain":
            d = ascii_domain_regex.fullmatch(host)
            if d is None:
                d = int_domain_regex.fullmatch(host)
                if not d:
                    raise errors.UrlHostError()
                host_type = "int_domain"
                rebuild = True
                host = host.encode("idna").decode("ascii")

            tld = d.group("tld")
            if tld is not None:
                tld = tld[1:]
            elif cls.tld_required:
                raise errors.UrlHostTldError()
        return host, tld, host_type, rebuild  # type: ignore

    def __repr__(self) -> str:
        extra = ", ".join(f"{n}={getattr(self, n)!r}" for n in self.__slots__ if getattr(self, n) is not None)
        return f"{self.__class__.__name__}({super().__repr__()}, {extra})"


# Specialized URL Types
class AnyHttpUrl(AnyUrl):
    allowed_schemes = {"http", "https"}


class HttpUrl(AnyUrl):
    allowed_schemes = {"http", "https"}
    tld_required = True
    max_length = 2083


class PostgresDsn(AnyUrl):
    allowed_schemes = {"postgres", "postgresql"}
    user_required = True


class RedisDsn(AnyUrl):
    allowed_schemes = {"redis"}
    user_required = True


def stricturl(
    *,
    strip_whitespace: bool = True,
    min_length: int = 1,
    max_length: int = 2**16,
    tld_required: bool = True,
    allowed_schemes: Optional[Set[str]] = None,
) -> Type[AnyUrl]:
    namespace = dict(
        strip_whitespace=strip_whitespace,
        min_length=min_length,
        max_length=max_length,
        tld_required=tld_required,
        allowed_schemes=allowed_schemes,
    )
    return type("UrlValue", (AnyUrl,), namespace)


# Email Validation
class EmailStr(str):
    @classmethod
    def __get_validators__(cls) -> "CallableGenerator":
        if email_validator is None:
            raise ImportError("email-validator is not installed, run `pip install pydantic[email]`")
        yield str_validator
        yield cls.validate

    @classmethod
    def validate(cls, value: str) -> str:
        return validate_email(value)[1]


class NameEmail(Representation):
    __slots__ = "name", "email"

    def __init__(self, name: str, email: str):
        self.name = name
        self.email = email

    @classmethod
    def __get_validators__(cls) -> "CallableGenerator":
        if email_validator is None:
            raise ImportError("email-validator is not installed, run `pip install pydantic[email]`")
        yield str_validator
        yield cls.validate

    @classmethod
    def validate(cls, value: str) -> "NameEmail":
        return cls(*validate_email(value))

    def __str__(self) -> str:
        return f"{self.name} <{self.email}>"


def validate_email(value: str) -> Tuple[str, str]:
    if email_validator is None:
        raise ImportError("email-validator is not installed, run `pip install pydantic[email]`")

    m = pretty_email_regex.fullmatch(value)
    name: Optional[str] = None
    if m:
        name, value = m.groups()

    email = value.strip()
    try:
        parts = email_validator.validate_email(email, check_deliverability=False)
        email = parts.normalized
    except email_validator.EmailNotValidError as e:
        raise errors.EmailError() from e

    at_index = email.rindex("@")
    local_part = email[:at_index]
    domain_part = email[at_index:].lower()

    return name or local_part, local_part + domain_part


# IP Address Validation
class IPvAnyAddress(_BaseAddress):
    @classmethod
    def __get_validators__(cls) -> "CallableGenerator":
        yield cls.validate

    @classmethod
    def validate(cls, value: Union[str, bytes, int]) -> Union[IPv4Address, IPv6Address]:
        try:
            return IPv4Address(value)
        except ValueError:
            pass
        try:
            return IPv6Address(value)
        except ValueError:
            raise errors.IPvAnyAddressError()


class IPvAnyInterface(_BaseAddress):
    @classmethod
    def __get_validators__(cls) -> "CallableGenerator":
        yield cls.validate

    @classmethod
    def validate(cls, value: NetworkType) -> Union[IPv4Interface, IPv6Interface]:
        try:
            return IPv4Interface(value)
        except ValueError:
            pass
        try:
            return IPv6Interface(value)
        except ValueError:
            raise errors.IPvAnyInterfaceError()


class IPvAnyNetwork(_BaseNetwork):
    @classmethod
    def __get_validators__(cls) -> "CallableGenerator":
        yield cls.validate

    @classmethod
    def validate(cls, value: NetworkType) -> Union[IPv4Network, IPv6Network]:
        try:
            return IPv4Network(value)
        except ValueError:
            pass
        try:
            return IPv6Network(value)
        except ValueError:
            raise errors.IPvAnyNetworkError()
