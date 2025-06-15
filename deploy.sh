#!/bin/bash

# Deployment script for Telegram Teacher Bot
# Usage: ./deploy.sh [VPS_HOST] [VPS_USER]

set -e

VPS_HOST=${1:-"your-vps-ip"}
VPS_USER=${2:-"root"}
PROJECT_NAME="telegram-teacher-bot"
REMOTE_PATH="/opt/$PROJECT_NAME"

echo "🚀 Deploying $PROJECT_NAME to $VPS_USER@$VPS_HOST"

# Create deployment directory on VPS
echo "📁 Setting up directories on VPS..."
ssh $VPS_USER@$VPS_HOST "mkdir -p $REMOTE_PATH/data"

# Copy project files to VPS
echo "📤 Copying project files..."
rsync -avz --exclude='teacher_bot_env' --exclude='__pycache__' --exclude='*.pyc' --exclude='.git' \
    ./ $VPS_USER@$VPS_HOST:$REMOTE_PATH/

# Install Docker and Docker Compose if not present
echo "🐳 Installing Docker and Docker Compose..."
ssh $VPS_USER@$VPS_HOST << 'EOF'
# Install Docker if not present
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    systemctl enable docker
    systemctl start docker
fi

# Install Docker Compose if not present
if ! command -v docker-compose &> /dev/null; then
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi
EOF

# Deploy the application
echo "🔧 Deploying application..."
ssh $VPS_USER@$VPS_HOST << EOF
cd $REMOTE_PATH

# Stop existing containers
docker-compose down 2>/dev/null || true

# Build and start the application
docker-compose up -d --build

# Show status
docker-compose ps
EOF

echo "✅ Deployment completed!"
echo "📋 Next steps:"
echo "1. SSH to your VPS: ssh $VPS_USER@$VPS_HOST"
echo "2. Navigate to project: cd $REMOTE_PATH"
echo "3. Copy .env.example to .env and configure: cp .env.example .env && nano .env"
echo "4. Restart the bot: docker-compose restart"
echo "5. View logs: docker-compose logs -f"