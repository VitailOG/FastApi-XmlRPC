from pydantic import BaseModel

from fastapi_xmlrpc.routing import XmlRpcAPIRouter

router = XmlRpcAPIRouter()


class Test(BaseModel):
    id: int
    name: str


@router.xml_rpc(
    namespace='eps',
    function_name='test',
)
def test(
        item: Test
):
    return item.dict()
