# Complete Backend Setup Guide

This guide will walk you through setting up MongoDB, SuperTokens, and configuring your environment variables.

## Table of Contents
1. [MongoDB Setup](#mongodb-setup)
2. [SuperTokens Setup](#supertokens-setup)
3. [Environment Variables Configuration](#environment-variables-configuration)
4. [Running the Backend](#running-the-backend)

---

## MongoDB Setup

You have two options: **MongoDB Atlas (Cloud)** or **Local MongoDB**

### Option 1: MongoDB Atlas (Recommended for Development)

1. **Create a MongoDB Atlas Account**
   - Go to https://www.mongodb.com/cloud/atlas/register
   - Sign up for a free account (M0 Free Tier)

2. **Create a Cluster**
   - After logging in, click "Build a Database"
   - Choose the **FREE** (M0) tier
   - Select a cloud provider and region (choose closest to you)
   - Click "Create"

3. **Create Database User**
   - Go to "Database Access" in the left sidebar
   - Click "Add New Database User"
   - Choose "Password" authentication
   - Enter a username and generate a secure password (save this!)
   - Set user privileges to "Atlas admin" or "Read and write to any database"
   - Click "Add User"

4. **Configure Network Access**
   - Go to "Network Access" in the left sidebar
   - Click "Add IP Address"
   - For development, click "Allow Access from Anywhere" (0.0.0.0/0)
   - Click "Confirm"

5. **Get Connection String**
   - Go to "Database" in the left sidebar
   - Click "Connect" on your cluster
   - Choose "Connect your application"
   - Copy the connection string (looks like: `mongodb+srv://<username>:<password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority`)
   - Replace `<username>` and `<password>` with your database user credentials
   - This is your `MONGODB_URI`

### Option 2: Local MongoDB

1. **Install MongoDB**
   ```bash
   # Ubuntu/Debian
   sudo apt-get update
   sudo apt-get install -y mongodb

   # macOS (using Homebrew)
   brew tap mongodb/brew
   brew install mongodb-community

   # Windows
   # Download from https://www.mongodb.com/try/download/community
   ```

2. **Start MongoDB Service**
   ```bash
   # Ubuntu/Debian
   sudo systemctl start mongod
   sudo systemctl enable mongod

   # macOS
   brew services start mongodb-community

   # Windows
   # MongoDB runs as a service automatically after installation
   ```

3. **Connection String**
   - For local MongoDB, use: `mongodb://localhost:27017`
   - This is your `MONGODB_URI`

---

## SuperTokens Setup

1. **Create SuperTokens Account**
   - Go to https://supertokens.com
   - Click "Get Started" or "Sign Up"
   - Sign up with your email or GitHub

2. **Create a New App**
   - After logging in, click "Create New App"
   - App Name: `Busted` (or any name you prefer)
   - Framework: Select "FastAPI" or "Other"
   - Click "Create"

3. **Get Your Credentials**
   - After creating the app, you'll see your dashboard
   - Find your **Connection URI** (looks like: `https://try.supertokens.com` or similar)
   - Find your **API Key** (you may need to generate one)
   - Save both of these values

4. **Configure Core Location**
   - In SuperTokens dashboard, go to "Core" settings
   - Note the connection URI (usually `https://try.supertokens.com` for free tier)
   - If you need to set up a self-hosted core, follow their documentation

**Note:** For development, you can use the free tier which provides:
- Connection URI: `https://try.supertokens.com`
- You'll need to generate an API key in the dashboard

---

## Environment Variables Configuration

1. **Create `.env` file**
   ```bash
   cd /home/husam/Hamza/hackathon/backend
   touch .env
   ```

2. **Add the following content to `.env`:**

   ```env
   # MongoDB Configuration
   # For Atlas: mongodb+srv://username:password@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
   # For Local: mongodb://localhost:27017
   MONGODB_URI=mongodb+srv://your-username:your-password@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
   MONGODB_DB=busted_db

   # SuperTokens Configuration
   # Get these from your SuperTokens dashboard
   SUPERTOKENS_CONNECTION_URI=https://try.supertokens.com
   SUPERTOKENS_API_KEY=your-super-tokens-api-key-here

   # API Configuration
   API_DOMAIN=http://localhost:8000
   API_BASE_PATH=/auth

   # Website Configuration (Frontend URL)
   WEBSITE_DOMAIN=http://localhost:5173
   WEBSITE_BASE_PATH=/auth

   # Backend URL
   BACKEND_URL=http://localhost:8000
   ```

3. **Replace the placeholder values:**
   - `MONGODB_URI`: Your MongoDB connection string from step 1
   - `MONGODB_DB`: Database name (e.g., `busted_db`)
   - `SUPERTOKENS_CONNECTION_URI`: From your SuperTokens dashboard
   - `SUPERTOKENS_API_KEY`: From your SuperTokens dashboard
   - `API_DOMAIN`: API domain for SuperTokens (default: `http://localhost:8000`)
   - `WEBSITE_DOMAIN`: Frontend URL (default: `http://localhost:5173`)
   - `BACKEND_URL`: Backend server URL (default: `http://localhost:8000`)

4. **Verify `.env` file is in `.gitignore`**
   - The `.env` file should already be ignored (check `.gitignore`)
   - Never commit `.env` to version control!

---

## Running the Backend

1. **Install Python Dependencies**
   ```bash
   cd /home/husam/Hamza/hackathon/backend
   pip3 install -r requirements.txt
   ```

   Or use a virtual environment (recommended):
   ```bash
   cd /home/husam/Hamza/hackathon/backend
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Verify `.env` file exists and is configured**
   ```bash
   ls -la .env  # Should show the file exists
   ```

3. **Run the server**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

4. **Test the server**
   - Open http://localhost:8000 in your browser
   - You should see: `{"status": "ok"}`
   - API docs: http://localhost:8000/docs

---

## Troubleshooting

### MongoDB Connection Issues
- Verify your connection string is correct
- Check that your IP is whitelisted in MongoDB Atlas
- Ensure MongoDB service is running (for local setup)
- Test connection: `mongosh "your-connection-string"`

### SuperTokens Issues
- Verify your API key is correct
- Check that your connection URI matches your SuperTokens dashboard
- Ensure CORS is properly configured

### Environment Variables Not Loading
- Ensure `.env` file is in the `backend` directory
- Check that variable names match exactly (case-sensitive)
- Restart the server after changing `.env`

---

## Quick Reference

**MongoDB Atlas:**
- Sign up: https://www.mongodb.com/cloud/atlas/register
- Free tier: M0 (512MB storage)

**SuperTokens:**
- Sign up: https://supertokens.com
- Free tier available for development

**Backend URL:** http://localhost:8000
**API Docs:** http://localhost:8000/docs
