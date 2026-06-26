#!/bin/bash
set -e

echo "🚀 Starting HOD AI System Backend"
echo "=================================="

# Check .env file
if [ ! -f ".env" ]; then
  echo "⚠️  .env file not found. Copying from .env.example..."
  cp .env.example .env
  echo "📝 Please edit .env and add your GROQ_API_KEY and LANGCHAIN_API_KEY"
fi

# Create virtual environment if not exists
if [ ! -d "venv" ]; then
  echo "📦 Creating Python virtual environment..."
  python3 -m venv venv
fi

source venv/bin/activate

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt -q

echo "✅ Starting FastAPI server on http://localhost:8000"
echo "📖 API Docs: http://localhost:8000/api/docs"
echo ""

uvicorn main:app --host 0.0.0.0 --port 8000 --reload
