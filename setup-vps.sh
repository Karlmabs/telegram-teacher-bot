#!/bin/bash

# VPS Setup Script for Telegram Teacher Bot
# Run this script on your VPS after deployment

set -e

PROJECT_NAME="telegram-teacher-bot"
PROJECT_PATH="/opt/$PROJECT_NAME"

echo "🔧 Setting up $PROJECT_NAME on VPS..."

# Create project directory and set permissions
echo "📁 Creating directories..."
mkdir -p $PROJECT_PATH/data
chown -R $USER:$USER $PROJECT_PATH

# Copy systemd service file
echo "📋 Setting up systemd service..."
cp $PROJECT_PATH/telegram-teacher-bot.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable telegram-teacher-bot.service

# Setup firewall (optional - uncomment if needed)
# echo "🔥 Configuring firewall..."
# ufw allow ssh
# ufw allow 8080/tcp
# ufw --force enable

echo "✅ VPS setup completed!"
echo "📋 Next steps:"
echo "1. Configure environment: cd $PROJECT_PATH && cp .env.example .env && nano .env"
echo "2. Start the service: systemctl start telegram-teacher-bot"
echo "3. Check status: systemctl status telegram-teacher-bot"
echo "4. View logs: docker-compose logs -f"
echo "5. Restart service: systemctl restart telegram-teacher-bot"