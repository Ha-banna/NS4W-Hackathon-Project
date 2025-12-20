#!/bin/bash

# Backend Environment Setup Script
# This script helps you create the .env file interactively

echo "=========================================="
echo "Backend Environment Setup"
echo "=========================================="
echo ""

# Check if .env already exists
if [ -f .env ]; then
    echo "⚠️  .env file already exists!"
    read -p "Do you want to overwrite it? (y/N): " overwrite
    if [ "$overwrite" != "y" ] && [ "$overwrite" != "Y" ]; then
        echo "Setup cancelled."
        exit 0
    fi
fi

echo "Please provide the following information:"
echo ""

# MongoDB Configuration
echo "--- MongoDB Configuration ---"
read -p "MongoDB URI (mongodb+srv://... or mongodb://localhost:27017): " mongodb_uri
read -p "MongoDB Database Name [busted_db]: " mongodb_db
mongodb_db=${mongodb_db:-busted_db}

# SuperTokens Configuration
echo ""
echo "--- SuperTokens Configuration ---"
read -p "SuperTokens Connection URI [https://try.supertokens.com]: " supertokens_uri
supertokens_uri=${supertokens_uri:-https://try.supertokens.com}
read -p "SuperTokens API Key: " supertokens_key

# API Configuration
echo ""
echo "--- API Configuration ---"
read -p "API Domain [http://localhost:8000]: " api_domain
api_domain=${api_domain:-http://localhost:8000}
read -p "API Base Path [/auth]: " api_base_path
api_base_path=${api_base_path:-/auth}

# Website Configuration
echo ""
echo "--- Website Configuration ---"
read -p "Website Domain [http://localhost:5173]: " website_domain
website_domain=${website_domain:-http://localhost:5173}
read -p "Website Base Path [/auth]: " website_base_path
website_base_path=${website_base_path:-/auth}

# Backend URL (same as API Domain)
backend_url=$api_domain

# Create .env file
cat > .env << EOF
# MongoDB Configuration
MONGODB_URI=$mongodb_uri
MONGODB_DB=$mongodb_db

# SuperTokens Configuration
SUPERTOKENS_CONNECTION_URI=$supertokens_uri
SUPERTOKENS_API_KEY=$supertokens_key

# API Configuration
API_DOMAIN=$api_domain
API_BASE_PATH=$api_base_path

# Website Configuration
WEBSITE_DOMAIN=$website_domain
WEBSITE_BASE_PATH=$website_base_path

# Backend URL
BACKEND_URL=$backend_url
EOF

echo ""
echo "✅ .env file created successfully!"
echo ""
echo "Next steps:"
echo "1. Install dependencies: pip3 install -r requirements.txt"
echo "2. Run the server: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
echo ""
