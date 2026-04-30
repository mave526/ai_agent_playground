# TR Online Sales - Backend

Multi-sided marketplace backend built with FastAPI + MongoDB.

## Tech Stack

- **API Framework**: FastAPI
- **Database**: MongoDB (via motor async driver)
- **Authentication**: JWT with refresh tokens
- **Validation**: Pydantic v2
- **Password Hashing**: bcrypt

## Project Structure

```
backend/
├── app/
│   ├── api/              # API routes/endpoints
│   │   └── v1/
│   │       ├── auth.py   # Authentication endpoints
│   │       └── users.py  # User management endpoints
│   ├── core/             # Core configuration
│   │   ├── config.py    # Settings management
│   │   ├── security.py  # JWT, password hashing
│   │   └── database.py  # MongoDB connection
│   ├── models/           # Pydantic models (schemas)
│   │   ├── user.py      # User schemas
│   │   ├── product.py   # Product schemas
│   │   └── order.py     # Order schemas
│   ├── services/         # Business logic
│   │   └── auth_service.py
│   └── main.py           # Application entry point
├── requirements.txt
└── .env.example
```

## Quick Start

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and update values:

```bash
cp .env.example .env
```

### 3. Run the Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Access API Docs

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/v1/auth/register | Register new user |
| POST | /api/v1/auth/login | Login user |
| POST | /api/v1/auth/refresh | Refresh access token |
| GET | /api/v1/users/me | Get current user |
| PUT | /api/v1/users/me | Update current user |
| GET | /api/v1/users/{id} | Get user by ID (admin) |

## User Roles

| Role | Description |
|------|-------------|
| consumer | Buyer/customer |
| merchant | Product seller |
| delivery_agent | Fulfillment partner |
| influencer | Affiliate marketer |
| advertiser | Ad campaign manager |
| admin | Platform administrator |

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| MONGODB_URL | MongoDB connection string | mongodb://localhost:27017 |
| DATABASE_NAME | MongoDB database name | tr_online_sales |
| SECRET_KEY | JWT signing key | change-me-in-production |
| ACCESS_TOKEN_EXPIRE_MINUTES | Access token expiry | 30 |
| REFRESH_TOKEN_EXPIRE_DAYS | Refresh token expiry | 7 |
| ALGORITHM | JWT algorithm | HS256 |

## License

MIT