from fastapi import Body, Depends
from routing import XmlRpcAPIRouter
from app.schemas.eps import TestSchema, TestResponseSchema
from app.endpoints.dependencies.common import test

router = XmlRpcAPIRouter()


@router.xml_rpc(
    namespace='eps',
    function_name='test',
    response_model=TestResponseSchema
)
def test(
        t: TestSchema,
        f: str = Depends(test)
        # t2: TestResponseSchema,
):
    print(f)
    return t.dict()
