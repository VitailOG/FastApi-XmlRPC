# @app.post(
#     "/item/create",
#     openapi_extra={
#         "requestBody": {
#             "content": {
#                 "application/xml": {
#                     "schema": SchemaGenerator()(
#                         [
#                             list[Union[int, str]]
#                         ]
#                     ).schema(ref_template="#/components/schemas/{model}")
#                 }
#             },
#             "required": True,
#         }
#     }
# )
# async def test():
#     return {}
#
# app.openapi = custom_openapi





# def gen_schema(types: list):
#
#     def unpack(types: list):
#         s = tuple([XMLRPCValue[create_schemas(_)] for _ in types])
#         param = create_schema(
#             'param',
#             param=(list[Union[s]], ...)
#         )
#         schema = create_schema(
#             'MethodCall',
#             MethodName=(str, ...),
#             params=(param, ...)
#         )
#         return schema
#
#     def array(obj):
#         if obj is list:
#             return XMLRPCArrayT[IntT]
#
#         t = []
#         for i in get_args(obj):
#
#             if get_origin(i) is not Union:
#                 return XMLRPCArrayT[create_schemas(i)]
#
#             for j in get_args(i):
#                 t.append(create_schemas(j))
#
#         return XMLRPCArrayT[list[Union[tuple(t)]]]
#
#     def struct(obj):
#         if not isinstance(obj, ModelMetaclass):
#             return XMLRPCStructT[IntT]
#
#         members = []
#         for field, attribute in obj.__fields__.items():
#             data = create_schema(
#                 f'data_{uuid4()}',
#                 name=(str, field),
#                 value=(create_schemas(attribute.outer_type_), ...)
#             )
#             members.append(data)
#
#         member = create_schema(
#             f'member_{uuid4()}',
#             member=(list[Union[tuple(members)]], ...)
#         )
#
#         struct_s = create_schema(
#             f'struct_{uuid4()}',
#             member=(member, ...)
#         )
#
#         return struct_s
#
#     def create_schemas(obj):
#         if check_type(obj, 'struct'):
#             return struct(obj)
#
#         if check_type(obj, 'array'):
#             return array(obj)
#
#         if obj in SINGLE_TYPES:
#             return SINGLE_TYPES[obj]
#
#         return XMLRPCArrayT[IntT]
#
#     def check_type(obj, xml_type: str):
#         is_instance_obj = {
#             'array': (GenericAlias, _GenericAlias, list),
#             'struct': (ModelMetaclass, dict),
#         }
#         obj = obj() if any(obj is _ for _ in (dict, list)) else obj
#         return isinstance(obj, is_instance_obj.get(xml_type))
#
#     return unpack(types=types)
