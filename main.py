from functools import partial
from typing import Dict, Any

from fastapi import (
    FastAPI,
    routing
)
from fastapi.openapi.utils import get_openapi

from app.main.endpoints.eps import router as eps_router
from open_api.schemas import default_ref_template
from fastapi_xmlrpc.middleware import XMLRPCMiddleware
from fastapi_xmlrpc.errors import *


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    definitions: Dict[str, Dict[str, Any]] = {}

    for route in app.routes:
        if isinstance(route, routing.APIRoute) and hasattr(route, "openapi_extra"):
            try:
                for content in route.openapi_extra["requestBody"]["content"].values():
                    content["schema"]['xml'] = {"name": "methodResponse"}

                    definitions |= content["schema"].pop("definitions", {})
                    definitions[content["schema"]["title"]] = content["schema"]
                    content["schema"] = {"$ref": default_ref_template.format(model=content["schema"]["title"])}

                for _ in route.responses.values():
                    for content in _['content'].values():
                        content["schema"]['xml'] = {"name": "methodResponse"}

                        definitions |= content["schema"].pop("definitions", {})
                        definitions[content["schema"]["title"]] = content["schema"]
                        content["schema"] = {"$ref": default_ref_template.format(model=content["schema"]["title"])}

            except KeyError:
                continue
            except TypeError:
                continue

    openapi_schema = get_openapi(
        title="Custom title",
        version="2.5.0",
        description="This is a very custom OpenAPI schema",
        routes=app.routes
    )

    openapi_schema.setdefault("components", {}).setdefault("schemas", {}).update(definitions)

    app.openapi_schema = openapi_schema

    return app.openapi_schema


def get_application() -> FastAPI:
    application = FastAPI()

    application.add_middleware(
        XMLRPCMiddleware,
        router=eps_router
    )

    #  required after add_middleware
    application.include_router(eps_router)

    application.add_exception_handler(RequestValidationError, request_validation_error_handler)
    application.add_exception_handler(XMLRPCError, xmlrpc_error_handler)
    application.add_exception_handler(HTTPException, http_error_handler)
    application.add_exception_handler(Exception, global_error_handler)

    ###################
    application.add_exception_handler(TypeError, global_error_handler)
    application.add_exception_handler(TabError, global_error_handler)
    application.add_exception_handler(ZeroDivisionError, global_error_handler)
    application.add_exception_handler(KeyError, global_error_handler)

    application.openapi = custom_openapi
    return application


app = get_application()
