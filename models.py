from pydantic import BaseModel, Field
from typing import Optional
# from datetime import datetime

class ItemCreate(BaseModel):
    name: str = Field(..., description="Name of the item")
    description: Optional[str] = Field(None, description="Description of the item")
    category: Optional[str] = Field(None, description="Category of the item")
    barcode: Optional[str] = Field(None, description="Barcode or QR code")
    serial_number: Optional[str] = Field(None, description="Serial number")
    storage_location: Optional[str] = Field(None, description="Where the item is stored")
    image_url: Optional[str] = Field(None, description="URL to item image")
    notes: Optional[str] = Field(None, description="Additional notes")

class ItemUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    barcode: Optional[str] = None
    serial_number: Optional[str] = None
    storage_location: Optional[str] = None
    image_url: Optional[str] = None
    notes: Optional[str] = None

class ItemResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    category: Optional[str]
    barcode: Optional[str]
    serial_number: Optional[str]
    storage_location: Optional[str]
    is_checked_out: int
    checked_out_by: Optional[str]
    checked_out_date: Optional[str]
    image_url: Optional[str]
    notes: Optional[str]
    created_date: str
    last_modified_date: str

class CheckoutRequest(BaseModel):
    person_name: str = Field(..., description="Name of person checking out the item")
    notes: Optional[str] = Field("", description="Optional notes")

class CheckinRequest(BaseModel):
    person_name: str = Field(..., description="Name of person checking in the item")
    notes: Optional[str] = Field("", description="Optional notes")

class HistoryEntry(BaseModel):
    id: int
    item_id: int
    action: str
    person_name: str
    timestamp: str
    notes: Optional[str]

class MessageResponse(BaseModel):
    message: str
    success: bool = True
