from routing import XmlRpcAPIRouter
from app.schemas.eps import Test


router = XmlRpcAPIRouter()


@router.xml_rpc(namespace='eps', function_name='test')
def test(t: Test):
    return {"res": t.id * 10, "in": t.name}
