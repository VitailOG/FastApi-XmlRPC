from fastapi import Body, Depends, exceptions
from routing import XmlRpcAPIRouter
from fastapi_xmlrpc.exceptions import HttpError
from app.main.schemas.eps import TestSchema, TestResponseSchema
from app.main.endpoints.dependencies.common import test

router = XmlRpcAPIRouter()


@router.xml_rpc(
    namespace='eps',
    function_name='test',
    response_model=TestResponseSchema
)
def test(
        t: TestSchema
        # f: str = Depends(test)
        # t2: TestResponseSchema,
):
    raise exceptions.HTTPException(status_code=402)
    return t.dict()
