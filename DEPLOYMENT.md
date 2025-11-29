# Deployment Guide

This guide covers deploying the KSSM Inventory Management System for production use.

## Table of Contents
1. [Backend Deployment](#backend-deployment)
2. [iOS App Distribution](#ios-app-distribution)
3. [Security Hardening](#security-hardening)
4. [Database Migration](#database-migration)

---

## Backend Deployment

### Option 1: Railway (Recommended - Easy & Free Tier Available)

Railway is a modern deployment platform with excellent Python support.

1. **Create Railway Account**
   - Visit [railway.app](https://railway.app)
   - Sign up with GitHub

2. **Deploy from GitHub**
   - Click "New Project" → "Deploy from GitHub repo"
   - Select `KSSMInventoryServer` repository
   - Railway auto-detects Python and requirements.txt

3. **Configure Environment Variables**
   In Railway dashboard, add these variables:
   ```
   PORT=8000
   SECRET_KEY=<generate-secure-random-key>
   ENVIRONMENT=production
   ```

4. **Generate SECRET_KEY** (run locally):
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

5. **Database Configuration**
   - Railway provides persistent volumes
   - Add volume: `/app/data` to persist `inventory.db`
   - Or migrate to PostgreSQL (see Database Migration below)

6. **Deploy**
   - Railway automatically deploys on push to main
   - You'll get a URL like: `https://your-app.railway.app`

**Cost:** Free tier available with 500 hours/month

---

### Option 2: Render (Alternative - Free Tier Available)

1. **Create Render Account**
   - Visit [render.com](https://render.com)
   - Sign up with GitHub

2. **Create Web Service**
   - Click "New +" → "Web Service"
   - Connect `KSSMInventoryServer` repository
   - Configure:
     - **Name:** kssm-inventory-api
     - **Runtime:** Python 3
     - **Build Command:** `pip install -r requirements.txt`
     - **Start Command:** `uvicorn server:app --host 0.0.0.0 --port $PORT`

3. **Environment Variables**
   ```
   SECRET_KEY=<generate-secure-random-key>
   ENVIRONMENT=production
   ```

4. **Persistent Disk** (for SQLite)
   - Add disk at `/app/data`
   - Update database path in code to use this mount

**Cost:** Free tier available (spins down after inactivity)

---

### Option 3: DigitalOcean App Platform

1. **Create DigitalOcean Account**
   - Visit [digitalocean.com](https://digitalocean.com)

2. **Create App**
   - Go to Apps → Create App
   - Connect GitHub repository
   - Auto-detected as Python app

3. **Configure**
   - Environment variables (same as above)
   - Add managed PostgreSQL database (recommended)

**Cost:** Starts at $5/month

---

### Option 4: Self-Hosted (VPS)

For complete control, deploy on your own server.

**Requirements:**
- Ubuntu 22.04 LTS or similar
- Minimum 1GB RAM
- Python 3.9+
- nginx (reverse proxy)
- systemd (process management)

**Setup Steps:**

1. **Install Dependencies**
   ```bash
   sudo apt update
   sudo apt install python3-pip python3-venv nginx
   ```

2. **Clone Repository**
   ```bash
   cd /opt
   sudo git clone https://github.com/lukeodrobinak/KSSMInventoryServer.git
   cd KSSMInventoryServer
   ```

3. **Create Virtual Environment**
   ```bash
   sudo python3 -m venv venv
   sudo venv/bin/pip install -r requirements.txt
   ```

4. **Create Systemd Service**
   Create `/etc/systemd/system/kssm-inventory.service`:
   ```ini
   [Unit]
   Description=KSSM Inventory API
   After=network.target

   [Service]
   Type=simple
   User=www-data
   WorkingDirectory=/opt/KSSMInventoryServer
   Environment="SECRET_KEY=your-secret-key-here"
   ExecStart=/opt/KSSMInventoryServer/venv/bin/uvicorn server:app --host 127.0.0.1 --port 8000
   Restart=always
   RestartSec=10

   [Install]
   WantedBy=multi-user.target
   ```

5. **Configure nginx**
   Create `/etc/nginx/sites-available/kssm-inventory`:
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;

       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

6. **Enable and Start**
   ```bash
   sudo ln -s /etc/nginx/sites-available/kssm-inventory /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl restart nginx
   sudo systemctl enable kssm-inventory
   sudo systemctl start kssm-inventory
   ```

7. **Setup SSL with Let's Encrypt**
   ```bash
   sudo apt install certbot python3-certbot-nginx
   sudo certbot --nginx -d your-domain.com
   ```

---

## iOS App Distribution

### Option 1: TestFlight (Beta Testing)

Best for internal testing with up to 10,000 users.

1. **Prepare App**
   - Open Xcode project
   - Update `Info.plist` with production server URL
   - Set version and build number

2. **Archive App**
   - In Xcode: Product → Archive
   - Wait for archive to complete

3. **Upload to App Store Connect**
   - Window → Organizer → Archives
   - Select archive → Distribute App
   - Choose "App Store Connect"
   - Select "Upload"

4. **Configure TestFlight**
   - Log in to [App Store Connect](https://appstoreconnect.apple.com)
   - Go to TestFlight tab
   - Add internal testers (up to 100)
   - Add external testers (requires beta review)

5. **Invite Testers**
   - Testers receive email invitation
   - They install TestFlight app
   - Install your app through TestFlight

**Requirements:**
- Apple Developer Account ($99/year)
- Valid provisioning profile

---

### Option 2: App Store (Public Release)

For public distribution.

1. **Prepare for Submission**
   - Complete all App Store Connect information
   - Screenshots (required sizes for all devices)
   - App description, keywords, category
   - Privacy policy URL

2. **Archive and Upload**
   - Same as TestFlight steps 2-3

3. **Submit for Review**
   - Select build in App Store Connect
   - Answer review questions
   - Submit for review

4. **Review Process**
   - Typically 1-3 days
   - May require changes
   - Approved apps go live

---

### Option 3: Enterprise Distribution (Internal Only)

For organizations with Apple Developer Enterprise Program.

1. **Create In-House Distribution Certificate**
   - Developer portal → Certificates
   - Create In-House distribution cert

2. **Archive with Enterprise Profile**
   - Use enterprise provisioning profile
   - Archive in Xcode

3. **Export for Enterprise**
   - Distribute App → Enterprise
   - Export IPA file

4. **Distribute**
   - Host IPA on web server
   - Create manifest.plist
   - Distribute download link to users

**Requirements:**
- Apple Developer Enterprise Program ($299/year)
- Only for internal employee distribution

---

## Security Hardening

### Backend Security

1. **Update `server.py` for Production**

   Add CORS configuration for production:
   ```python
   from fastapi.middleware.cors import CORSMiddleware
   import os

   # Get environment
   ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
   SECRET_KEY = os.getenv("SECRET_KEY")

   if ENVIRONMENT == "production":
       if not SECRET_KEY:
           raise ValueError("SECRET_KEY must be set in production")

       # Strict CORS for production
       app.add_middleware(
           CORSMiddleware,
           allow_origins=["https://your-domain.com"],  # Update with your domain
           allow_credentials=True,
           allow_methods=["GET", "POST", "PUT", "DELETE"],
           allow_headers=["*"],
       )
   else:
       # Development CORS
       app.add_middleware(
           CORSMiddleware,
           allow_origins=["*"],
           allow_credentials=True,
           allow_methods=["*"],
           allow_headers=["*"],
       )
   ```

2. **Update `auth.py` to Use Environment SECRET_KEY**
   ```python
   import os

   SECRET_KEY = os.getenv("SECRET_KEY", "your-default-dev-key")
   ```

3. **Enable HTTPS Only**
   - All production deployments MUST use HTTPS
   - Railway/Render provide automatic HTTPS
   - For self-hosted, use Let's Encrypt (see above)

4. **Secure Headers**
   Add security headers to `server.py`:
   ```python
   from fastapi.middleware.trustedhost import TrustedHostMiddleware

   if ENVIRONMENT == "production":
       app.add_middleware(
           TrustedHostMiddleware,
           allowed_hosts=["your-domain.com", "*.your-domain.com"]
       )
   ```

5. **Rate Limiting**
   Install slowapi:
   ```bash
   pip install slowapi
   ```

   Add to `server.py`:
   ```python
   from slowapi import Limiter, _rate_limit_exceeded_handler
   from slowapi.util import get_remote_address
   from slowapi.errors import RateLimitExceeded

   limiter = Limiter(key_func=get_remote_address)
   app.state.limiter = limiter
   app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

   @app.post("/api/auth/login")
   @limiter.limit("5/minute")  # 5 login attempts per minute
   async def login(request: Request, login_request: LoginRequest):
       # existing code
   ```

### iOS Security

1. **Update Server URL**
   In `NetworkService.swift`, use production URL:
   ```swift
   @AppStorage("serverURL") private var serverURL = "https://your-api.railway.app"
   ```

2. **Certificate Pinning** (Optional but recommended)
   Prevent man-in-the-middle attacks by pinning SSL certificate.

3. **Keychain Storage** (Enhanced security)
   Consider moving token storage from UserDefaults to Keychain:
   ```swift
   import Security

   // Store token in Keychain instead of UserDefaults
   // More secure for sensitive data
   ```

---

## Database Migration

### SQLite Limitations in Production

SQLite works for small deployments (<1000 concurrent users), but has limitations:
- Single writer at a time
- No built-in replication
- File-based (harder to backup in cloud)

### Migrate to PostgreSQL (Recommended for Production)

1. **Install PostgreSQL Locally** (for testing migration)
   ```bash
   # macOS
   brew install postgresql

   # Ubuntu
   sudo apt install postgresql postgresql-contrib
   ```

2. **Update `requirements.txt`**
   ```
   sqlalchemy>=2.0.0
   psycopg2-binary>=2.9.0
   ```

3. **Update `database.py`**

   Replace SQLite connection with SQLAlchemy:
   ```python
   from sqlalchemy import create_engine, text
   import os

   DATABASE_URL = os.getenv(
       "DATABASE_URL",
       "sqlite:///./inventory.db"  # fallback to SQLite
   )

   # Convert postgres:// to postgresql:// (Railway uses old format)
   if DATABASE_URL.startswith("postgres://"):
       DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

   engine = create_engine(DATABASE_URL)

   def get_connection(self):
       return engine.connect()
   ```

4. **Update Schema for PostgreSQL**

   Change `INTEGER PRIMARY KEY` to `SERIAL PRIMARY KEY`:
   ```sql
   CREATE TABLE IF NOT EXISTS users (
       id SERIAL PRIMARY KEY,
       -- rest of schema
   )
   ```

5. **Migration Script**

   Create `migrate_to_postgres.py`:
   ```python
   import sqlite3
   import psycopg2
   import os

   # Connect to SQLite
   sqlite_conn = sqlite3.connect('inventory.db')
   sqlite_conn.row_factory = sqlite3.Row

   # Connect to PostgreSQL
   pg_conn = psycopg2.connect(os.getenv('DATABASE_URL'))
   pg_cursor = pg_conn.cursor()

   # Migrate each table
   tables = ['users', 'items', 'item_requests', 'checkouts']

   for table in tables:
       # Read from SQLite
       sqlite_cursor = sqlite_conn.execute(f"SELECT * FROM {table}")
       rows = sqlite_cursor.fetchall()

       # Insert into PostgreSQL
       for row in rows:
           columns = ','.join(row.keys())
           placeholders = ','.join(['%s'] * len(row))
           query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
           pg_cursor.execute(query, tuple(row))

   pg_conn.commit()
   print("Migration complete!")
   ```

6. **Configure Database in Cloud Platform**

   **Railway:**
   - Add PostgreSQL plugin
   - Automatically sets `DATABASE_URL` environment variable

   **Render:**
   - Create PostgreSQL database
   - Copy connection string to environment variables

   **DigitalOcean:**
   - Add managed PostgreSQL database
   - Use connection string in environment

---

## Production Checklist

### Before Deployment

- [ ] Change default Quartermaster password
- [ ] Generate secure SECRET_KEY
- [ ] Update CORS allowed origins
- [ ] Enable HTTPS
- [ ] Test authentication flow
- [ ] Test all API endpoints
- [ ] Setup database backups
- [ ] Configure error monitoring (Sentry, etc.)
- [ ] Setup logging
- [ ] Add rate limiting
- [ ] Review security headers

### iOS App

- [ ] Update server URL to production
- [ ] Test with production API
- [ ] Increment version/build number
- [ ] Test on multiple iOS versions
- [ ] Test on multiple device sizes
- [ ] Create app screenshots
- [ ] Write App Store description
- [ ] Prepare privacy policy

### Monitoring

- [ ] Setup uptime monitoring (UptimeRobot, etc.)
- [ ] Configure error alerting
- [ ] Setup application logs
- [ ] Monitor API response times
- [ ] Track authentication errors

---

## Estimated Costs

| Option | Monthly Cost | Best For |
|--------|--------------|----------|
| Railway (Free) | $0 | Testing, small teams |
| Railway (Hobby) | $5 | Small production |
| Render (Free) | $0 | Testing (sleeps when idle) |
| Render (Starter) | $7 | Small production |
| DigitalOcean | $12+ | Medium production |
| Self-hosted VPS | $5+ | Full control |
| Apple Developer | $99/year | Required for iOS |

---

## Support & Troubleshooting

### Common Issues

**502 Bad Gateway**
- Check if backend is running
- Verify port configuration
- Check logs for errors

**Authentication Fails**
- Verify SECRET_KEY is set
- Check token expiration
- Verify HTTPS is enabled

**Database Locked**
- SQLite limitation with concurrent writes
- Consider migrating to PostgreSQL

**iOS App Can't Connect**
- Verify server URL is HTTPS
- Check CORS configuration
- Verify API is accessible

### Logs

**Railway/Render:**
- View logs in dashboard

**Self-hosted:**
```bash
# View service logs
sudo journalctl -u kssm-inventory -f

# View nginx logs
sudo tail -f /var/log/nginx/error.log
```

---

## Next Steps

1. Choose deployment platform (Railway recommended for easiest setup)
2. Deploy backend
3. Test API endpoints
4. Update iOS app with production URL
5. Submit to TestFlight or App Store
6. Monitor and iterate

Good luck with your deployment! 🚀
