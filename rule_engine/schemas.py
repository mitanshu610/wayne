from slugify import slugify
from enum import Enum
from typing import Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, validator, ConfigDict, field_validator


class ScopeEnum(str, Enum):
    ORGANISATION = "organisation"
    USER = "user"


class BackendService(str, Enum):
    CEREBRUM = "cerebrum"
    REVIEW_PILOT = "review-pilot"


class RuleSchema(BaseModel):
    """
    Schema for rules, including dynamic conditions as a dictionary.
    """
    name: str = Field(..., description="The name of the rule")
    description: Optional[str] = Field(None, description="The description of the rule")
    scope: ScopeEnum = Field(..., description="The scope of the rule (e.g., 'organization', 'user')")
    enabled: bool = Field(True, description="Whether the rule is enabled")
    meta_data: Optional[dict] = Field(None, description="Additional metadata for the rule")
    rule_slug: str = Field(None, description="A unique slug identifier for the rule")
    rule_class_name: str = Field(..., description="The class name of the rule")
    service_slug: BackendService = Field(..., description="The backend service associated with the rule")
    conditions: Optional[Dict] = None

    @field_validator('rule_slug', mode='before')
    def set_slug(cls, v, values):
        if v is None:
            name = values.get('name')
            if name:
                return slugify(name)
        return v


class ConditionDataSchema(BaseModel):
    request_limit: Optional[int] = None
    reset_period: Optional[str] = None

    class Config:
        extra = "ignore"


class RuleDetailsSchema(BaseModel):
    id: UUID
    name: str
    description: str
    enabled: bool
    service_slug: str
    condition_data: ConditionDataSchema

    model_config = ConfigDict(from_attributes=True)