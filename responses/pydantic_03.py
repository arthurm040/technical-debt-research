from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, Optional, Set, Union

from .typing import AnyType, display_as_type

__all__ = (
    "PydanticErrorMixin",
    "PydanticTypeError",
    "PydanticValueError",
    # ... (rest of the exports remain the same)
)


class PydanticErrorMixin:
    """
    Pydantic V2 style error mixin.
    Uses explicit code (type) and message templates.
    """

    code: str
    msg_template: str

    def __init__(self, **ctx: Any) -> None:
        self.ctx = ctx

    def __str__(self) -> str:
        # Pydantic v2 uses python-style formatting for templates
        return self.msg_template.format(**self.ctx)

    def error_dict(self) -> Dict[str, Any]:
        """Provides a structured dictionary representation similar to V2's error output."""
        return {
            "type": self.code,
            "msg": str(self),
            "ctx": self.ctx,
        }


class PydanticTypeError(PydanticErrorMixin, TypeError):
    pass


class PydanticValueError(PydanticErrorMixin, ValueError):
    pass


class ConfigError(RuntimeError):
    pass


# --- Implementation of Specific Errors ---


class MissingError(PydanticValueError):
    code = "missing"
    msg_template = "Field required"


class ExtraError(PydanticValueError):
    code = "extra_forbidden"
    msg_template = "Extra fields not permitted"


class NoneIsNotAllowedError(PydanticTypeError):
    code = "none_is_not_allowed"
    msg_template = "None is not an allowed value"


class WrongConstantError(PydanticValueError):
    code = "greater_than"
    msg_template = "Unexpected value; permitted: {permitted}"

    def __init__(self, *, permitted: Any) -> None:
        # Convert permitted values to a readable string during init
        permitted_str = ", ".join(repr(v) for v in permitted)
        super().__init__(permitted=permitted_str)


class UrlSchemePermittedError(PydanticValueError):
    code = "url_scheme"
    msg_template = "URL scheme not permitted; allowed schemes: {allowed_schemes}"

    def __init__(self, allowed_schemes: Set[str]):
        super().__init__(allowed_schemes=allowed_schemes)


class EnumError(PydanticTypeError):
    code = "enum"
    msg_template = "Input should be {permitted}"

    def __init__(self, *, enum_values: Any) -> None:
        permitted = ", ".join(repr(v.value) for v in enum_values)
        super().__init__(permitted=permitted)


class _PathValueError(PydanticValueError):
    def __init__(self, *, path: Path) -> None:
        super().__init__(path=str(path))


class PathNotExistsError(_PathValueError):
    code = "path_not_exists"
    msg_template = 'File or directory at path "{path}" does not exist'


class TupleLengthError(PydanticValueError):
    code = "tuple_type"
    msg_template = "Tuple should have at most {expected_length} items after validation, not {actual_length}"

    def __init__(self, *, actual_length: int, expected_length: int) -> None:
        super().__init__(actual_length=actual_length, expected_length=expected_length)


class UUIDVersionError(PydanticValueError):
    code = "uuid_version"
    msg_template = "UUID version {required_version} expected"

    def __init__(self, *, required_version: int) -> None:
        super().__init__(required_version=required_version)


class ArbitraryTypeError(PydanticTypeError):
    code = "is_instance_of"
    msg_template = "Input should be an instance of {expected_arbitrary_type}"

    def __init__(self, *, expected_arbitrary_type: AnyType) -> None:
        super().__init__(expected_arbitrary_type=display_as_type(expected_arbitrary_type))


# ... Follow the same pattern for remaining classes
