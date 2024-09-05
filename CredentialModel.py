from pydantic import BaseModel

class Credential(BaseModel):
    key: str
    value: str
