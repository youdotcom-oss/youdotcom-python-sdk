

from datetime import datetime
from pydantic import ConfigDict, Field, model_serializer
from pydantic import BaseModel as PydanticBaseModel
from pydantic_core import core_schema
from typing import TYPE_CHECKING, Any, Literal, Optional, TypeVar, Union
from typing_extensions import Annotated, TypeAliasType, TypeAlias


class BaseModel(PydanticBaseModel):
    model_config = ConfigDict(
        populate_by_name=True, arbitrary_types_allowed=True, protected_namespaces=()
    )


class Unset(BaseModel):
    @model_serializer(mode="plain")
    def serialize_model(self):
        return UNSET_SENTINEL

    def __bool__(self) -> Literal[False]:
        return False


UNSET = Unset()
UNSET_SENTINEL = "~?~unset~?~sentinel~?~"


T = TypeVar("T")
if TYPE_CHECKING:
    Nullable: TypeAlias = Union[T, None]
    OptionalNullable: TypeAlias = Union[Optional[Nullable[T]], Unset]
else:
    Nullable = TypeAliasType("Nullable", Union[T, None], type_params=(T,))
    OptionalNullable = TypeAliasType(
        "OptionalNullable", Union[Optional[Nullable[T]], Unset], type_params=(T,)
    )


class UnrecognizedStr(str):
    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type: Any, _handler: Any) -> core_schema.CoreSchema:
        # Make UnrecognizedStr only work in lax mode, not strict mode
        # This makes it a "fallback" option when more specific types (like Literals) don't match
        def validate_lax(v: Any) -> 'UnrecognizedStr':
            if isinstance(v, cls):
                return v
            return cls(str(v))

        # Use lax_or_strict_schema where strict always fails
        # This forces Pydantic to prefer other union members in strict mode
        # and only fall back to UnrecognizedStr in lax mode
        return core_schema.lax_or_strict_schema(
            lax_schema=core_schema.chain_schema([
                core_schema.str_schema(),
                core_schema.no_info_plain_validator_function(validate_lax)
            ]),
            strict_schema=core_schema.none_schema(),  # Always fails in strict mode
        )


class UnrecognizedInt(int):
    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type: Any, _handler: Any) -> core_schema.CoreSchema:
        # Make UnrecognizedInt only work in lax mode, not strict mode
        # This makes it a "fallback" option when more specific types (like Literals) don't match
        def validate_lax(v: Any) -> 'UnrecognizedInt':
            if isinstance(v, cls):
                return v
            return cls(int(v))
        return core_schema.lax_or_strict_schema(
            lax_schema=core_schema.chain_schema([
                core_schema.int_schema(),
                core_schema.no_info_plain_validator_function(validate_lax)
            ]),
            strict_schema=core_schema.none_schema(),  # Always fails in strict mode
        )


# Non-ISO values reach us, so `page_age` accepts either. Left-to-right so an
# ISO string parses to a `datetime`; anything else stays the string it came as.
# Do not add format parsing: it only covers shapes already seen, and it has to
# guess on ambiguous input (`5/6/2024` is May 6 or 6 May depending on the
# producer), which can be wrong by months with no signal to the caller.
LenientDateTime = Annotated[
    Union[datetime, str, None], Field(union_mode="left_to_right")
]
