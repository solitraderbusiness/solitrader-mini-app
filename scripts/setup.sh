#!/bin/bash
set -e

echo "🚀 Setting up TG-Trade Suite (Optimized for 2GB RAM)..."

# Create .env from example if it doesn't exist
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✅ Created .env file. Please edit it with your credentials."
fi

# Make scripts executable
chmod +x scripts/*.sh

# Create temp directory for image processing
mkdir -p temp

echo "✅ Setup complete!"
echo "📝 Next steps:"
echo "1. Edit .env file with your API keys"
echo "2. Run: docker-compose up -d"
