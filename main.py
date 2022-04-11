from fastapi import (
    FastAPI,
    exceptions,
    responses
)
from aiohttp_xmlrpc.exceptions import register_exception

from app.main.endpoints.eps import router as eps_router
from app.errors import global_error_handler, global_error_handler_sub
from app.sub.endpoints.sub import router as sub_router
from middleware import XmlRpcMiddleware


def get_application() -> FastAPI:

    # register_exception(HTTPException, 402)

    application = FastAPI(default_response_class=responses.ORJSONResponse)

    application.include_router(eps_router)

    application.add_middleware(
        XmlRpcMiddleware,
        access_url="/rpc/v1/"
    )
    application.add_exception_handler(exceptions.HTTPException, global_error_handler)

    sub_application = FastAPI()

    sub_application.include_router(sub_router)
    sub_application.add_exception_handler(exceptions.HTTPException, global_error_handler_sub)

    application.mount("/subapi", sub_application)

    return application


app = get_application()
