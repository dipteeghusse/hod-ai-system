#!/bin/bash
set -e

echo "🎨 Starting HOD AI System Frontend"
echo "==================================="

# Create .env.local if missing
if [ ! -f ".env.local" ]; then
  cat > .env.local << 'EOF'
NEXT_PUBLIC_API_URL=http://localhost:8000/api
NEXT_PUBLIC_WS_URL=ws://localhost:8000/api/ws
EOF
  echo "✅ Created .env.local"
fi

# Install dependencies
if [ ! -d "node_modules" ]; then
  echo "📦 Installing npm packages..."
  npm install
fi

echo "✅ Starting Next.js on http://localhost:3000"
echo ""
npm run dev
