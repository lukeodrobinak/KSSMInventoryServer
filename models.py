from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from enum import Enum

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

# MARK: - User Models

class UserRole(str, Enum):
    MEMBER = "member"
    ADMIN = "admin"
    QUARTERMASTER = "quartermaster"

class UserCreate(BaseModel):
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password")
    full_name: str = Field(..., description="User's full name")
    role: UserRole = Field(UserRole.MEMBER, description="User role")

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    password: Optional[str] = Field(None, min_length=8)

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    created_date: str
    last_login: Optional[str]
    is_active: int

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class PasswordResetRequest(BaseModel):
    user_id: int
    new_password: str = Field(..., min_length=8)

# MARK: - Request Models (for item add/remove requests)

class RequestType(str, Enum):
    ADD_ITEM = "add_item"
    REMOVE_ITEM = "remove_item"

class RequestStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"

class ItemRequestCreate(BaseModel):
    request_type: RequestType
    item_name: str = Field(..., description="Name of the item")
    description: str = Field(..., description="Description/reason for the request")
    item_id: Optional[int] = Field(None, description="Item ID (for remove requests)")

class ItemRequestUpdate(BaseModel):
    status: RequestStatus
    denial_reason: Optional[str] = Field(None, description="Reason for denial (required if denied)")

class ItemRequestResponse(BaseModel):
    id: int
    requester_id: int
    requester_name: str
    request_type: str
    item_name: str
    description: str
    item_id: Optional[int]
    status: str
    denial_reason: Optional[str]
    created_date: str
    reviewed_date: Optional[str]
    reviewed_by_id: Optional[int]
    reviewed_by_name: Optional[str]
