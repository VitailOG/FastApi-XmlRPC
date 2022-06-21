from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import Response
from starlette.datastructures import Headers

from fastapi_xmlrpc.parser.exceptions import XMLRPCError, MethodNotFound, InvalidData
from fastapi_xmlrpc.responses import XMLRPCResponse


def sp(number: int, singular: str, plural: str):
    if str(number)[-1] == "1" and number != 11:
        return singular
    return plural


async def xmlrpc_error_handler(
        request: Request,
        exc: XMLRPCError,
):
    return XMLRPCResponse(exc)


async def request_validation_error_handler(
        request: Request,
        exc: RequestValidationError,
):
    headers = Headers(raw=request.scope['headers'])

    errors = exc.errors()
    errors_str = ", ".join([f"{e['loc'][0]}: {e['msg']}" for e in errors])
    errors_num = len(errors)

    if headers.get("request-content-type"):
        return XMLRPCResponse(
            InvalidData(f"Invalid data. {errors_num} {sp(errors_num, 'error', 'errors')} found. {errors_str}")
        )

    return JSONResponse(content=errors)


async def global_error_handler(
        request: Request,
        exc: Exception,
):
    return Response("Internal Server Error", status_code=500)


async def http_error_handler(
        request: Request,
        exc: HTTPException,
):
    if exc.status_code == 404:

        return XMLRPCResponse(MethodNotFound("Method not found"))

    return Response(exc.detail, status_code=exc.status_code)
