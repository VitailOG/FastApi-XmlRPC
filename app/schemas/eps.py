from pydantic import BaseModel


class TestSchema(BaseModel):
    id: int
    name: str


class TestResponseSchema(BaseModel):
    name: str
