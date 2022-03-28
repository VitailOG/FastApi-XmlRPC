from pydantic import BaseModel


class Test(BaseModel):
    id: int
    name: str


class Test2(BaseModel):
    age: int
