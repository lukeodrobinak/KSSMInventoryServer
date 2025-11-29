from fastapi import FastAPI, HTTPException, Query, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from typing import List, Optional
import uvicorn
import logging

from database import InventoryDatabase
from models import (
    ItemCreate, ItemUpdate, ItemResponse, CheckoutRequest,
    CheckinRequest, HistoryEntry, MessageResponse,
    UserCreate, UserUpdate, UserResponse, LoginRequest, LoginResponse,
    PasswordResetRequest, ItemRequestCreate, ItemRequestUpdate, ItemRequestResponse
)
from auth import (
    create_access_token, get_current_user, get_current_active_user,
    require_role, user_dict_to_response
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Inventory Management System API",
    description="REST API for managing inventory items with check in/out functionality",
    version="1.0.0"
)

# Add CORS middleware to allow iOS app to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your iOS app's origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database
db = InventoryDatabase()

# Custom validation error handler for better debugging
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    body = await request.body()
    logger.error(f"Validation error on {request.url.path}")
    logger.error(f"Request body: {body.decode()}")
    logger.error(f"Validation errors: {errors}")
    return JSONResponse(
        status_code=422,
        content={
            "detail": errors,
            "body": body.decode()
        }
    )

@app.get("/")
async def root():
    """Root endpoint - API health check"""
    return {
        "message": "Inventory Management System API",
        "version": "1.0.0",
        "status": "running"
    }

# MARK: - Authentication Endpoints

@app.post("/api/auth/login", response_model=LoginResponse)
async def login(login_request: LoginRequest):
    """Authenticate user and return access token"""
    # Get user by username
    user = db.get_user_by_username(login_request.username)

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password"
        )

    # Verify password
    if not db.verify_password(login_request.password, user['password_hash']):
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password"
        )

    # Check if user is active
    if not user.get('is_active', 0):
        raise HTTPException(
            status_code=403,
            detail="User account is inactive"
        )

    # Update last login
    db.update_last_login(user['id'])

    # Create access token
    access_token = create_access_token(data={"sub": str(user['id'])})

    # Convert user to response model
    user_response = user_dict_to_response(user)

    return LoginResponse(
        access_token=access_token,
        user=user_response
    )

@app.get("/api/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current authenticated user information"""
    return user_dict_to_response(current_user)

@app.get("/api/items", response_model=List[ItemResponse])
async def get_all_items(current_user: dict = Depends(get_current_user)):
    """Get all items in the inventory (All authenticated users)"""
    try:
        items = db.get_all_items()
        return items
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/items/{item_id}", response_model=ItemResponse)
async def get_item(item_id: int, current_user: dict = Depends(get_current_user)):
    """Get a specific item by ID (All authenticated users)"""
    item = db.get_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@app.post("/api/items", response_model=ItemResponse)
async def create_item(
    item: ItemCreate,
    current_user: dict = Depends(require_role(["quartermaster"]))
):
    """Create a new inventory item (Quartermaster only - Admins must use requests)"""
    try:
        item_id = db.add_item(item.dict())
        new_item = db.get_item(item_id)
        return new_item
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/api/items/{item_id}", response_model=ItemResponse)
async def update_item(
    item_id: int,
    item: ItemUpdate,
    current_user: dict = Depends(require_role(["admin", "quartermaster"]))
):
    """Update an existing item (Admin and Quartermaster only)"""
    # Check if item exists
    existing_item = db.get_item(item_id)
    if not existing_item:
        raise HTTPException(status_code=404, detail="Item not found")

    # Only update fields that are provided
    update_data = {k: v for k, v in item.dict().items() if v is not None}

    # If no fields to update, return existing item
    if not update_data:
        return existing_item

    # Merge with existing data
    for key, value in existing_item.items():
        if key not in update_data:
            update_data[key] = value

    try:
        success = db.update_item(item_id, update_data)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to update item")

        updated_item = db.get_item(item_id)
        return updated_item
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/api/items/{item_id}", response_model=MessageResponse)
async def delete_item(
    item_id: int,
    current_user: dict = Depends(require_role(["quartermaster"]))
):
    """Delete an item from the inventory (Quartermaster only - Admins must use requests)"""
    success = db.delete_item(item_id)
    if not success:
        raise HTTPException(status_code=404, detail="Item not found")

    return MessageResponse(message="Item deleted successfully", success=True)

@app.post("/api/items/{item_id}/checkout", response_model=MessageResponse)
async def checkout_item(
    item_id: int,
    checkout: CheckoutRequest,
    current_user: dict = Depends(get_current_user)
):
    """Check out an item to a person (All authenticated users)"""
    # Check if item exists
    item = db.get_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    # Check if already checked out
    if item['is_checked_out']:
        raise HTTPException(
            status_code=400,
            detail=f"Item is already checked out to {item['checked_out_by']}"
        )

    success = db.checkout_item(item_id, checkout.person_name, checkout.notes)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to check out item")

    return MessageResponse(
        message=f"Item checked out to {checkout.person_name}",
        success=True
    )

@app.post("/api/items/{item_id}/checkin", response_model=MessageResponse)
async def checkin_item(
    item_id: int,
    checkin: CheckinRequest,
    current_user: dict = Depends(get_current_user)
):
    """Check in an item (All authenticated users)"""
    # Check if item exists
    item = db.get_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    # Check if actually checked out
    if not item['is_checked_out']:
        raise HTTPException(status_code=400, detail="Item is not checked out")

    success = db.checkin_item(item_id, checkin.person_name, checkin.notes)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to check in item")

    return MessageResponse(
        message="Item checked in successfully",
        success=True
    )

@app.get("/api/items/{item_id}/history", response_model=List[HistoryEntry])
async def get_item_history(item_id: int, current_user: dict = Depends(get_current_user)):
    """Get the checkout/checkin history for an item (All authenticated users)"""
    # Check if item exists
    item = db.get_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    history = db.get_item_history(item_id)
    return history

@app.get("/api/items/search/", response_model=List[ItemResponse])
async def search_items(
    q: str = Query(..., min_length=1, description="Search query"),
    current_user: dict = Depends(get_current_user)
):
    """Search for items by name, description, or barcode (All authenticated users)"""
    try:
        items = db.search_items(q)
        return items
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats")
async def get_stats(current_user: dict = Depends(require_role(["admin", "quartermaster"]))):
    """Get inventory statistics (Admin and Quartermaster only)"""
    try:
        all_items = db.get_all_items()

        total_items = len(all_items)
        checked_out = sum(1 for item in all_items if item['is_checked_out'])
        available = total_items - checked_out

        # Get categories
        categories = {}
        for item in all_items:
            cat = item.get('category', 'Uncategorized') or 'Uncategorized'
            categories[cat] = categories.get(cat, 0) + 1

        return {
            "total_items": total_items,
            "checked_out": checked_out,
            "available": available,
            "categories": categories
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# MARK: - User Management Endpoints

@app.post("/api/users", response_model=UserResponse)
async def create_user(
    user: UserCreate,
    current_user: dict = Depends(require_role(["quartermaster"]))
):
    """Create a new user (Quartermaster only)"""
    # Check if username already exists
    existing_user = db.get_user_by_username(user.username)
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")

    try:
        user_id = db.create_user(
            username=user.username,
            password=user.password,
            full_name=user.full_name,
            role=user.role.value
        )
        new_user = db.get_user_by_id(user_id)
        return user_dict_to_response(new_user)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/users", response_model=List[UserResponse])
async def get_all_users(current_user: dict = Depends(require_role(["quartermaster"]))):
    """Get all users (Quartermaster only)"""
    try:
        users = db.get_all_users()
        return [user_dict_to_response(user) for user in users]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user: dict = Depends(require_role(["quartermaster"]))
):
    """Get a specific user by ID (Quartermaster only)"""
    user = db.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user_dict_to_response(user)

@app.put("/api/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    current_user: dict = Depends(require_role(["quartermaster"]))
):
    """Update a user (Quartermaster only)"""
    # Check if user exists
    existing_user = db.get_user_by_id(user_id)
    if not existing_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Build update data
    update_data = {}
    if user_update.username is not None:
        # Check if new username is already taken by another user
        username_check = db.get_user_by_username(user_update.username)
        if username_check and username_check['id'] != user_id:
            raise HTTPException(status_code=400, detail="Username already in use")
        update_data['username'] = user_update.username

    if user_update.full_name is not None:
        update_data['full_name'] = user_update.full_name

    if user_update.role is not None:
        update_data['role'] = user_update.role.value

    if user_update.password is not None:
        update_data['password'] = user_update.password

    try:
        success = db.update_user(user_id, update_data)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to update user")

        updated_user = db.get_user_by_id(user_id)
        return user_dict_to_response(updated_user)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/api/users/{user_id}", response_model=MessageResponse)
async def delete_user(
    user_id: int,
    current_user: dict = Depends(require_role(["quartermaster"]))
):
    """Deactivate a user (Quartermaster only)"""
    # Prevent deleting yourself
    if user_id == current_user['id']:
        raise HTTPException(status_code=400, detail="Cannot deactivate your own account")

    success = db.delete_user(user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")

    return MessageResponse(message="User deactivated successfully", success=True)

@app.post("/api/users/reset-password", response_model=MessageResponse)
async def reset_password(
    reset_request: PasswordResetRequest,
    current_user: dict = Depends(require_role(["quartermaster"]))
):
    """Reset a user's password (Quartermaster only - admin-assisted password recovery)"""
    user = db.get_user_by_id(reset_request.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        success = db.update_user(reset_request.user_id, {'password': reset_request.new_password})
        if not success:
            raise HTTPException(status_code=400, detail="Failed to reset password")

        return MessageResponse(message="Password reset successfully", success=True)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# MARK: - Item Request Endpoints

@app.post("/api/requests", response_model=ItemRequestResponse)
async def create_request(
    request: ItemRequestCreate,
    current_user: dict = Depends(require_role(["admin"]))
):
    """Create a new item request (Admin only)"""
    try:
        # Validate item exists if it's a remove request
        if request.request_type.value == "remove_item":
            if not request.item_id:
                raise HTTPException(status_code=400, detail="item_id is required for remove requests")
            item = db.get_item(request.item_id)
            if not item:
                raise HTTPException(status_code=404, detail="Item not found")

        request_id = db.create_item_request(
            requester_id=current_user['id'],
            request_type=request.request_type.value,
            item_name=request.item_name,
            description=request.description,
            item_id=request.item_id
        )

        new_request = db.get_request_by_id(request_id)
        return new_request
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/requests", response_model=List[ItemRequestResponse])
async def get_all_requests(current_user: dict = Depends(require_role(["quartermaster"]))):
    """Get all item requests (Quartermaster only)"""
    try:
        requests = db.get_all_requests()
        return requests
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/requests/pending", response_model=List[ItemRequestResponse])
async def get_pending_requests(current_user: dict = Depends(require_role(["quartermaster"]))):
    """Get all pending item requests (Quartermaster only)"""
    try:
        requests = db.get_pending_requests()
        return requests
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/requests/my", response_model=List[ItemRequestResponse])
async def get_my_requests(current_user: dict = Depends(require_role(["admin"]))):
    """Get all requests created by the current user (Admin only)"""
    try:
        requests = db.get_requests_by_user(current_user['id'])
        return requests
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/requests/{request_id}", response_model=ItemRequestResponse)
async def update_request_status(
    request_id: int,
    status_update: ItemRequestUpdate,
    current_user: dict = Depends(require_role(["quartermaster"]))
):
    """Approve or deny an item request (Quartermaster only)"""
    # Get the request
    request = db.get_request_by_id(request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")

    # Check if already reviewed
    if request['status'] != 'pending':
        raise HTTPException(status_code=400, detail="Request has already been reviewed")

    # Validate denial reason
    if status_update.status.value == "denied" and not status_update.denial_reason:
        raise HTTPException(status_code=400, detail="Denial reason is required when denying a request")

    try:
        # Update request status
        success = db.update_request_status(
            request_id=request_id,
            status=status_update.status.value,
            reviewed_by_id=current_user['id'],
            denial_reason=status_update.denial_reason
        )

        if not success:
            raise HTTPException(status_code=400, detail="Failed to update request")

        # If approved and it's an add request, create the item
        if status_update.status.value == "approved" and request['request_type'] == "add_item":
            # Create item with basic info from request
            item_data = {
                'name': request['item_name'],
                'description': request['description']
            }
            db.add_item(item_data)

        # If approved and it's a remove request, delete the item
        elif status_update.status.value == "approved" and request['request_type'] == "remove_item":
            if request['item_id']:
                db.delete_item(request['item_id'])

        updated_request = db.get_request_by_id(request_id)
        return updated_request
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    print("=" * 60)
    print("Inventory Management System Server")
    print("=" * 60)
    print(f"Starting server on http://0.0.0.0:8000")
    print(f"API Documentation: http://localhost:8000/docs")
    print(f"Alternative Docs: http://localhost:8000/redoc")
    print("=" * 60)
    print("\nPress CTRL+C to stop the server")
    print()
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
