from uuid import uuid4
from types import GenericAlias
from typing import (
    Union,
    _GenericAlias,
    get_args,
    get_origin, Literal
)

from pydantic.main import ModelMetaclass

from .schemas import (
    IntT,
    StrT,
    BoolT,
    create_schema,
    XMLRPCValue,
    XMLRPCArrayT,
    XMLRPCStructT
)

ALLOWED_TYPES = Literal[
    'array',
    'struct'
]


class SchemaGenerator:
    SINGLE_TYPES = {
        int: IntT,
        str: StrT,
        bool: BoolT,
    }

    IS_OBJECT_INSTANCE = {
        'array': (GenericAlias, _GenericAlias, list),
        'struct': (ModelMetaclass, dict),
    }

    def __call__(self, types: list):
        s = tuple([XMLRPCValue[self.create_schemas(_)] for _ in types])
        param = create_schema(
            'param',
            param=(list[Union[s]], ...)
        )
        schema = create_schema(
            'MethodCall',
            MethodName=(str, ...),
            params=(param, ...)
        )
        return schema

    def create_schemas(self, obj):
        if self.check_type(obj, 'struct'):
            return self.struct(obj)

        if self.check_type(obj):
            return self.array(obj)

        if obj in self.SINGLE_TYPES:
            return self.SINGLE_TYPES[obj]

        return XMLRPCArrayT[IntT]

    def check_type(self, obj, xml_type: ALLOWED_TYPES = 'array'):
        obj = obj() if any(obj is _ for _ in (dict, list)) else obj
        return isinstance(obj, self.IS_OBJECT_INSTANCE.get(xml_type))

    def array(self, obj):
        if obj is list:
            return XMLRPCArrayT[IntT]

        t = []
        for i in get_args(obj):

            if get_origin(i) is not Union:
                return XMLRPCArrayT[self.create_schemas(i)]

            for j in get_args(i):
                t.append(self.create_schemas(j))

        return XMLRPCArrayT[list[Union[tuple(t)]]]

    def struct(self, obj):

        if not isinstance(obj, ModelMetaclass):
            return XMLRPCStructT[IntT]

        members = []
        for field, attribute in obj.__fields__.items():
            data = create_schema(
                f'data_{uuid4()}',
                name=(str, field),
                value=(self.create_schemas(attribute.outer_type_), ...)
            )
            members.append(data)

        member = create_schema(
            f'member_{uuid4()}',
            member=(list[Union[tuple(members)]], ...)
        )

        struct_s = create_schema(
            f'struct_{uuid4()}',
            member=(member, ...)
        )

        return struct_s
