"""
Sample Data Generator for Inventory Management System

Run this script to populate your database with sample inventory items.
"""

from database import InventoryDatabase

def add_sample_data():
    db = InventoryDatabase()
    
    sample_items = [
        {
            "name": "MacBook Pro 16\"",
            "description": "2023 MacBook Pro 16-inch, M3 Max, 64GB RAM",
            "category": "Laptops",
            "serial_number": "C02XD0AHJGH5",
            "storage_location": "Tech Cabinet A, Shelf 2",
            "barcode": "LAPTOP-001",
            "notes": "Includes USB-C charger and carrying case"
        },
        {
            "name": "Dell XPS 15",
            "description": "Dell XPS 15 9520, Intel i7, 32GB RAM",
            "category": "Laptops",
            "serial_number": "DXPS-2023-456",
            "storage_location": "Tech Cabinet A, Shelf 2",
            "barcode": "LAPTOP-002",
            "notes": "Includes charger"
        },
        {
            "name": "iPad Pro 12.9\"",
            "description": "iPad Pro 12.9-inch (6th generation) with Apple Pencil",
            "category": "Tablets",
            "serial_number": "DMQX3LL/A",
            "storage_location": "Mobile Devices Drawer",
            "barcode": "TABLET-001",
            "notes": "Includes Magic Keyboard and Apple Pencil 2"
        },
        {
            "name": "Sony A7 III Camera",
            "description": "Full-frame mirrorless camera with 24-70mm lens",
            "category": "Cameras",
            "serial_number": "1234567890",
            "storage_location": "Camera Equipment Case 1",
            "barcode": "CAM-001",
            "notes": "Includes 2 batteries, charger, and lens cap"
        },
        {
            "name": "Rode NT-USB Microphone",
            "description": "Professional USB condenser microphone",
            "category": "Audio Equipment",
            "serial_number": "NT-USB-789",
            "storage_location": "Audio Cabinet, Shelf 1",
            "barcode": "AUDIO-001",
            "notes": "Includes pop filter and desk stand"
        },
        {
            "name": "LG 27\" 4K Monitor",
            "description": "27-inch 4K UHD IPS Display",
            "category": "Monitors",
            "serial_number": "LG27UK850-W-123",
            "storage_location": "Monitor Storage Rack, Position 3",
            "barcode": "MON-001",
            "notes": "Includes HDMI and USB-C cables"
        },
        {
            "name": "Logitech MX Master 3",
            "description": "Wireless ergonomic mouse",
            "category": "Peripherals",
            "serial_number": "MXM3-456",
            "storage_location": "Peripherals Bin A",
            "barcode": "MOUSE-001",
            "notes": "Includes USB receiver"
        },
        {
            "name": "Anker PowerCore 20000",
            "description": "Portable charger, 20000mAh capacity",
            "category": "Power & Charging",
            "serial_number": "ANK-PC-789",
            "storage_location": "Charging Station",
            "barcode": "BATTERY-001",
            "notes": "Fully charged and tested"
        },
        {
            "name": "Elgato Stream Deck",
            "description": "15-key customizable LCD control deck",
            "category": "Streaming Equipment",
            "serial_number": "ELG-SD-321",
            "storage_location": "Streaming Gear Box",
            "barcode": "STREAM-001",
            "notes": "Includes USB cable"
        },
        {
            "name": "Projector - Epson Home Cinema",
            "description": "3LCD 1080p projector with 3400 lumens",
            "category": "Presentation Equipment",
            "serial_number": "EPSON-HC-654",
            "storage_location": "AV Equipment Cabinet",
            "barcode": "PROJ-001",
            "notes": "Includes remote, HDMI cable, and carrying case"
        }
    ]
    
    print("Adding sample data to database...")
    print("=" * 60)
    
    for item in sample_items:
        try:
            item_id = db.add_item(item)
            print(f"✓ Added: {item['name']} (ID: {item_id})")
        except Exception as e:
            print(f"✗ Failed to add {item['name']}: {e}")
    
    print("=" * 60)
    print(f"\nSuccessfully added {len(sample_items)} sample items!")
    
    # Check out a couple of items for demonstration
    print("\nChecking out some items for demonstration...")
    db.checkout_item(1, "John Smith", "Testing the system")
    db.checkout_item(3, "Jane Doe", "Taking to client presentation")
    print("✓ Checked out 2 items")
    
    print("\nSample data setup complete!")
    print("Start the server with: python server.py")
    print("Or double-click: start_server.bat")

if __name__ == "__main__":
    add_sample_data()
