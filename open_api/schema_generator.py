from types import GenericAlias
from typing import Union, get_args, get_origin, Any, _GenericAlias, Literal
from uuid import uuid4

from pydantic.main import ModelMetaclass

from open_api.schemas import XMLRPCStructT, IntT, XMLRPCArrayT, XMLRPCValue, StrT, BoolT, create_schema


ALLOWED_TYPES = Literal[
    'array',
    'struct'
]


class SchemaGenerator:

    DEFAULT_VALUE = {}

    SINGLE_TYPES = {
        int: IntT,
        str: StrT,
        bool: BoolT
    }

    IS_OBJECT_INSTANCE = {
        'array': (GenericAlias, _GenericAlias, list),
        'struct': (ModelMetaclass, dict),
    }

    def __call__(
            self,
            types: list,
            method_name: str = None,
            res: bool = False,
            is_fault: bool = False
    ):
        s = tuple([XMLRPCValue[self.create_schemas(_)] for _ in types])

        param = create_schema(
            f'param_{uuid4()}',
            param=(list[Union[s]], ...)
        )

        if res:

            if is_fault:
                schema = create_schema(
                    f'methodResponse_{uuid4()}',
                    fault=(s[0], ...)
                )

            else:
                schema = create_schema(
                    f'methodResponse_{uuid4()}',
                    params=(param, ...)
                )

        else:
            schema = create_schema(
                f'methodCall_{uuid4()}',
                methodName=(str, method_name),
                params=(param, ...),
            )

        return schema

    def create_schemas(self, obj: Any):
        if self.check_type(obj, 'struct'):
            return self.struct(obj)

        if self.check_type(obj):
            return self.array(obj)

        if obj in self.SINGLE_TYPES:
            return self.SINGLE_TYPES[obj]

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
                f'element_{uuid4()}',
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
            struct=(member, ...)
        )

        return struct_s
