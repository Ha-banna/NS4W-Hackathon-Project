# Backend Setup Guide

This is a FastAPI backend application for the Busted CV Evaluation Platform.

## Prerequisites

- Python 3.8 or higher
- MongoDB database (local or Atlas)
- SuperTokens account (for authentication)

## Setup Instructions

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

Or if you prefer using a virtual environment (recommended):

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file in the `backend` directory:

```bash
cp .env.example .env
```

Then edit `.env` with your actual values:

- **MONGODB_URI**: Your MongoDB connection string
- **MONGODB_DB**: Your database name
- **SUPERTOKENS_CONNECTION_URI**: Your SuperTokens connection URI
- **SUPERTOKENS_API_KEY**: Your SuperTokens API key
- **API_DOMAIN**: Your backend URL (default: http://localhost:8000)
- **API_BASE_PATH**: API base path (default: /auth)
- **WEBSITE_DOMAIN**: Your frontend URL (default: http://localhost:5173)
- **WEBSITE_BASE_PATH**: Website base path (default: /auth)

### 3. Run the Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The server will start on `http://localhost:8000`

### 4. API Documentation

Once the server is running, you can access:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Development

For development with auto-reload:

```bash
uvicorn app.main:app --reload
```

## Production

For production, use a production ASGI server like:

```bash
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```
