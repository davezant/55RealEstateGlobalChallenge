from enum import Enum
from pydantic import BaseModel, Field, SecretStr

class UserRole(str, Enum):
    USERADMIN = "admin"
    USEREDITOR = "editor"

class UserSchema(BaseModel):
    email: str = Field(..., min_length=5)
    password: SecretStr = Field(..., min_length=5)

class UserLoginSchema(UserSchema):
    pass   

class UserRegistrationSchema(UserSchema):
    username: str = Field(..., min_length=5)
    role: UserRole

class UserEditSchema(UserSchema):
    username: str = Field(..., min_length=5)
    new_password: SecretStr = Field(..., min_length=5)
    
