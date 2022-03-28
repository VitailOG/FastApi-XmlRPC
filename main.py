from fastapi import FastAPI

from app.endpoints.eps import router as eps_router
from middleware import XmlRpcMiddleware
from settings import settings


def get_application() -> FastAPI:
    application = FastAPI()

    application.include_router(eps_router)

    application.add_middleware(
        XmlRpcMiddleware,
        access_url="/rpc/v1/"
    )

    return application


app = get_application()
