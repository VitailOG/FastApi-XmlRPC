from fastapi import FastAPI, exceptions, HTTPException

from app.main.endpoints.eps import router as eps_router
from app.errors import global_error_handler, global_error_handler_sub
from app.sub.endpoints.sub import router as sub_router
from fastapi_xmlrpc.exceptions import HttpError
from middleware import XmlRpcMiddleware


def get_application() -> FastAPI:
    application = FastAPI()

    application.include_router(eps_router)
    ######
    application.add_middleware(
        XmlRpcMiddleware,
        access_url="/rpc/v1/"
    )
    application.add_exception_handler(HTTPException, global_error_handler)

    sub_application = FastAPI()

    sub_application.include_router(sub_router)
    sub_application.add_exception_handler(exceptions.HTTPException, global_error_handler_sub)

    application.mount("/subapi", sub_application)

    return application


app = get_application()
