from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import uvicorn

from database import InventoryDatabase
from models import (
    ItemCreate, ItemUpdate, ItemResponse, CheckoutRequest, 
    CheckinRequest, HistoryEntry, MessageResponse
)

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

@app.get("/")
async def root():
    """Root endpoint - API health check"""
    return {
        "message": "Inventory Management System API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/api/items", response_model=List[ItemResponse])
async def get_all_items():
    """Get all items in the inventory"""
    try:
        items = db.get_all_items()
        return items
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/items/{item_id}", response_model=ItemResponse)
async def get_item(item_id: int):
    """Get a specific item by ID"""
    item = db.get_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@app.post("/api/items", response_model=ItemResponse)
async def create_item(item: ItemCreate):
    """Create a new inventory item"""
    try:
        item_id = db.add_item(item.dict())
        new_item = db.get_item(item_id)
        return new_item
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/api/items/{item_id}", response_model=ItemResponse)
async def update_item(item_id: int, item: ItemUpdate):
    """Update an existing item"""
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
async def delete_item(item_id: int):
    """Delete an item from the inventory"""
    success = db.delete_item(item_id)
    if not success:
        raise HTTPException(status_code=404, detail="Item not found")
    
    return MessageResponse(message="Item deleted successfully", success=True)

@app.post("/api/items/{item_id}/checkout", response_model=MessageResponse)
async def checkout_item(item_id: int, checkout: CheckoutRequest):
    """Check out an item to a person"""
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
async def checkin_item(item_id: int, checkin: CheckinRequest):
    """Check in an item"""
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
async def get_item_history(item_id: int):
    """Get the checkout/checkin history for an item"""
    # Check if item exists
    item = db.get_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    history = db.get_item_history(item_id)
    return history

@app.get("/api/items/search/", response_model=List[ItemResponse])
async def search_items(q: str = Query(..., min_length=1, description="Search query")):
    """Search for items by name, description, or barcode"""
    try:
        items = db.search_items(q)
        return items
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats")
async def get_stats():
    """Get inventory statistics"""
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
