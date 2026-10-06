from pydantic import BaseModel, Field

class PhotoMetadataSchema(BaseModel):
    description: str | None = Field(default=None, max_length=255)
    is_cover: bool = False
