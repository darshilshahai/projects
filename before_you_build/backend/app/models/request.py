from pydantic import BaseModel, Field, field_validator


class AnalyzeRequest(BaseModel):
    idea: str = Field(..., max_length=3000)
    context: str | None = Field(default=None, max_length=3000)

    @field_validator("idea")
    @classmethod
    def validate_idea(cls, value: str) -> str:
        trimmed = value.strip()
        if len(trimmed) < 10:
            raise ValueError("idea must be at least 10 characters after trimming whitespace")
        return trimmed

    @field_validator("context")
    @classmethod
    def validate_context(cls, value: str | None) -> str | None:
        if value is None:
            return None
        trimmed = value.strip()
        return trimmed or None
