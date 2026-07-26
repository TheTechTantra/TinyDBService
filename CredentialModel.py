from pydantic import BaseModel

class Credential(BaseModel):
    key: str
    value: str


# Tokenization mode (SERVICE_MODE=tokenization)
class TokenizeRequest(BaseModel):
    value: str


class TokenizeResponse(BaseModel):
    token: str


class DetokenizeRequest(BaseModel):
    token: str


class DetokenizeResponse(BaseModel):
    value: str
