"""
Configuration settings for the Inventory Management System Server
"""

# Server Configuration
SERVER_HOST = "0.0.0.0"  # Listen on all network interfaces
SERVER_PORT = 8000       # Port number for the server

# Database Configuration
DATABASE_PATH = "inventory.db"  # Path to SQLite database file

# CORS Configuration
# In production, replace "*" with your specific iOS app origin
ALLOWED_ORIGINS = ["*"]

# API Configuration
API_TITLE = "Inventory Management System API"
API_DESCRIPTION = "REST API for managing inventory items with check in/out functionality"
API_VERSION = "1.0.0"

# Logging Configuration
LOG_LEVEL = "info"  # Options: debug, info, warning, error, critical
