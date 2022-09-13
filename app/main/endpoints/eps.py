from fastapi import Body

from fastapi_xmlrpc.routing import XmlRpcAPIRouter
from fastapi_xmlrpc.schemas import XMLRPCBaseModel

router = XmlRpcAPIRouter()


class Test(XMLRPCBaseModel):
    id: int


@router.xml_rpc(
    namespace='eps',
    function_name='test',
)
def test(
        # item: Test,
        name: str = Body(...)
):
    # print(item.dict())
    return name

