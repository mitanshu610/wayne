from pydantic import BaseModel, Field, constr, validator
from typing import Optional, Dict
from slugify import slugify

from features.models import BackendService


class FeatureSchema(BaseModel):
    """
    Schema for creating a new feature.
    """
    name: constr(min_length=1) = Field(
        ...,
        description="Name of the feature"
    )
    slug: Optional[constr(min_length=1)] = Field(
        None,
        description="Unique identifier for the feature (slug)"
    )
    description: constr(min_length=1) = Field(
        ...,
        description="Description of the feature"
    )
    meta_data: Optional[Dict] = Field(
        None,
        description="Optional metadata for the feature"
    )
    be_service: BackendService = Field(
        ...,
        description="Backend service for the feature"
    )

    @validator('slug', pre=True, always=True)
    def set_slug(cls, v, values):
        if v is None:
            name = values.get('name')
            if name:
                return slugify(name)
        return v


class FeatureUpdateSchema(BaseModel):
    """
    Schema for updating an existing feature.
    """
    name: Optional[constr(min_length=1)] = Field(
        None,
        description="Name of the feature"
    )
    description: Optional[constr(min_length=1)] = Field(
        None,
        description="Description of the feature"
    )
    meta_data: Optional[Dict] = Field(
        None,
        description="Optional metadata for the feature"
    )

