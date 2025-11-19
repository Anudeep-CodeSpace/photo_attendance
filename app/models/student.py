from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# ----------------------------------------------------
# Base model (shared attributes)
# ----------------------------------------------------
class StudentBase(BaseModel):
    roll_no: str = Field(..., description="Roll number, must match filename")
    name: Optional[str] = Field(None, description="Student name")
    class_name: Optional[str] = Field(None, alias="class", description="Class")
    section: Optional[str] = Field(None, description="Section")

    class Config:
        orm_mode = True
        allow_population_by_field_name = True


# ----------------------------------------------------
# DB model (includes timestamp)
# ----------------------------------------------------
class StudentDB(StudentBase):
    added_on: datetime


# ----------------------------------------------------
# Request model for registration
# (metadata is optional since batch upload uses filenames)
# ----------------------------------------------------
class StudentCreate(BaseModel):
    name: Optional[str] = None
    class_name: Optional[str] = Field(None, alias="class")
    section: Optional[str] = None

    class Config:
        allow_population_by_field_name = True


# ----------------------------------------------------
# API Response model
# ----------------------------------------------------
class StudentResponse(StudentBase):
    added_on: datetime
    