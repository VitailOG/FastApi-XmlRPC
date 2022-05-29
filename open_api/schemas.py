from decimal import Decimal
from typing import (
    Dict,
    Any,
    Type,
    Optional,
    Tuple,
    Union,
    TypeVar,
    Generic
)

from pydantic import BaseModel, create_model, BaseConfig
from pydantic.generics import GenericModel


default_ref_template = "#/components/schemas/{model}"
ValueType = TypeVar("ValueType")


class TestSchema(BaseModel):
    ...

    @classmethod
    def schema(cls, by_alias: bool = True, ref_template: str = default_ref_template) -> Dict[str, Any]:
        return super().schema(by_alias=by_alias, ref_template=ref_template)


def create_schema(
    __model_name: str,
    *,
    __config__: Optional[Type[BaseConfig]] = None,
    __base__: Union[None, Type['Model'], Tuple[Type['Model'], ...]] = TestSchema,
    __module__: str = __name__,
    __validators__: Dict[str, 'AnyClassMethod'] = None,
    **field_definitions: Any,
) -> Type['Model']:
    return create_model(
        __model_name,
        __config__=__config__,
        __base__=__base__,
        __module__=__module__,
        __validators__=__validators__,
        **field_definitions
    )


IntT = create_schema("IntT", int=(int, ...))
StrT = create_schema("StrT", string=(str, ...))
BoolT = create_schema("BoolT", boolean=(bool, ...))
DoubleT = create_schema("DoubleT", double=(Decimal, ...))


class BaseGen(GenericModel, Generic[ValueType]):
    pass


# Generic value
class XMLRPCValue(GenericModel, Generic[ValueType]):
    value: ValueType


# Array
class XMLRPCArrayData(GenericModel, Generic[ValueType]):
    data: XMLRPCValue[ValueType]


class XMLRPCArrayT(GenericModel, Generic[ValueType]):
    array: XMLRPCArrayData[ValueType]


# Struct
class XMLRPCStructMemberData(GenericModel, Generic[ValueType]):
    name: str
    data: XMLRPCValue[ValueType]


class XMLRPCStructMember(GenericModel, Generic[ValueType]):
    member: XMLRPCStructMemberData[ValueType]


class XMLRPCStructT(GenericModel, Generic[ValueType]):
    struct: XMLRPCStructMember[ValueType]


MethodCallSchema = create_schema(
    'MethodCall',
    methodName=(str, ...),
    params=(list, ...),
)
