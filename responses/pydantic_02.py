import re
from typing import Annotated, Any, Dict, List, Optional, Pattern, Type, TypeVar, Union, cast

T = TypeVar("T")

# --- 1. Constraint Metadata Classes ---
# These replace the dynamic class attributes from v1.


class BytesConstraints:
    def __init__(self, strip_whitespace: bool = False, min_length: int = None, max_length: int = None):
        self.strip_whitespace = strip_whitespace
        self.min_length = min_length
        self.max_length = max_length


class ListConstraints:
    def __init__(self, item_type: Any, min_items: int = None, max_items: int = None):
        self.item_type = item_type
        self.min_items = min_items
        self.max_items = max_items


class StringConstraints:
    def __init__(
        self,
        strip_whitespace: bool = False,
        strict: bool = False,
        min_length: int = None,
        max_length: int = None,
        curtail_length: int = None,
        regex: Optional[Union[str, Pattern[str]]] = None,
    ):
        self.strip_whitespace = strip_whitespace
        self.strict = strict
        self.min_length = min_length
        self.max_length = max_length
        self.curtail_length = curtail_length
        self.regex = re.compile(regex) if isinstance(regex, str) else regex


class NumberConstraints:
    def __init__(
        self,
        strict: bool = False,
        gt: float = None,
        ge: float = None,
        lt: float = None,
        le: float = None,
        multiple_of: float = None,
    ):
        if gt is not None and ge is not None:
            raise ValueError("bounds gt and ge cannot be specified at the same time")
        if lt is not None and le is not None:
            raise ValueError("bounds lt and le cannot be specified at the same time")
        self.strict = strict
        self.gt, self.ge, self.lt, self.le = gt, ge, lt, le
        self.multiple_of = multiple_of


# --- 2. V2 Implementation of Helper Functions ---


def conbytes(*, strip_whitespace: bool = False, min_length: int = None, max_length: int = None) -> Type[bytes]:
    return Annotated[
        bytes, BytesConstraints(strip_whitespace=strip_whitespace, min_length=min_length, max_length=max_length)
    ]


def conlist(item_type: Type[T], *, min_items: int = None, max_items: int = None) -> Type[List[T]]:
    return Annotated[List[item_type], ListConstraints(item_type=item_type, min_items=min_items, max_items=max_items)]


def constr(
    *,
    strip_whitespace: bool = False,
    strict: bool = False,
    min_length: int = None,
    max_length: int = None,
    curtail_length: int = None,
    regex: str = None,
) -> Type[str]:
    return Annotated[
        str,
        StringConstraints(
            strip_whitespace=strip_whitespace,
            strict=strict,
            min_length=min_length,
            max_length=max_length,
            curtail_length=curtail_length,
            regex=regex,
        ),
    ]


def conint(
    *, strict: bool = False, gt: int = None, ge: int = None, lt: int = None, le: int = None, multiple_of: int = None
) -> Type[int]:
    return Annotated[int, NumberConstraints(strict=strict, gt=gt, ge=ge, lt=lt, le=le, multiple_of=multiple_of)]


# --- 3. Pre-defined Constrained Types (V2 Style) ---

PositiveInt = Annotated[int, NumberConstraints(gt=0)]
NegativeInt = Annotated[int, NumberConstraints(lt=0)]
StrictInt = Annotated[int, NumberConstraints(strict=True)]
StrictStr = Annotated[str, StringConstraints(strict=True)]
