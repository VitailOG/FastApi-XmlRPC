from pydantic import Extra, BaseModel


class XMLRPCBaseModel(BaseModel):

    class Config:
        extra = Extra.forbid
