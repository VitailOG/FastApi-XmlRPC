from starlette.requests import Request
from starlette.responses import JSONResponse
from fastapi.exceptions import HTTPException

from fastapi_xmlrpc.parser import XMLHandler


async def global_error_handler(
        _: Request,
        exc: HTTPException
):
    xml_error = XMLHandler().build_xml(await XMLHandler().format_error(exc))
    return JSONResponse({"errors": xml_error.decode()}, status_code=402)


async def global_error_handler_sub(
        _: Request,
        exc: HTTPException
):
    return JSONResponse({"errors": ["sub"]}, status_code=402)
