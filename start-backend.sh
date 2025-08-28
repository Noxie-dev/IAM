#!/bin/bash

# IAM App Backend Server Starter
echo "📦 Starting Flask backend server..."

cd iam-backend
source venv/bin/activate
python src/main.py
