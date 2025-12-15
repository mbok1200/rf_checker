#!/bin/bash
set -e

echo "🚀 Initializing DynamoDB tables..."
python -m backend.services.init_dynamodb

echo "🌐 Starting FastAPI server..."
exec uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload