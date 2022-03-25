from fastapi import FastAPI

from app.endpoints.eps import router as eps_router
from middleware import XmlRpcMiddleware


app = FastAPI()

app.include_router(eps_router)
app.add_middleware(XmlRpcMiddleware)
