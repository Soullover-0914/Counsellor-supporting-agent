from pydantic import BaseModel, Field


class ResourceType:
    COUNSELLING = "counselling"
    WELLBEING = "wellbeing"
    EMERGENCY = "emergency"
    ACADEMIC = "academic"


class WellbeingResource(BaseModel):
    resource_id: str

    name: str = Field(
        ...,
        min_length=1,
    )

    resource_type: str

    description: str = Field(
        ...,
        min_length=1,
    )

    contact: str | None = None
    availability: str | None = None
    location: str | None = None

    emergency: bool = False
    active: bool = True


class CreateResourceRequest(BaseModel):
    name: str = Field(
        ...,
        min_length=1,
    )

    resource_type: str

    description: str = Field(
        ...,
        min_length=1,
    )

    contact: str | None = None
    availability: str | None = None
    location: str | None = None

    emergency: bool = False