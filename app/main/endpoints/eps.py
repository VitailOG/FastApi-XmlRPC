from pydantic import BaseModel

from fastapi_xmlrpc.routing import XmlRpcAPIRouter


router = XmlRpcAPIRouter()


class Test(BaseModel):
    id: int
    name: str


@router.xml_rpc(
    namespace='eps',
    function_name='test'
)
def test(
        item: Test
):
    return item.dict()


 # openapi_extra={
    #     "requestBody": {
    #         "content": {
    #             "application/xml": {
    #                 "schema": SchemaGenerator()(
    #                     [
    #                         list[str]
    #                     ]
    #                 ).schema(ref_template="#/components/schemas/{model}")
    #             }
    #         },
    #         "required": True,
    #     }
    # }