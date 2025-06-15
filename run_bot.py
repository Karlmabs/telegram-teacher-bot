#!/usr/bin/env python3
"""
Simple script to run the Telegram Teacher Bot
Run this file to start your bot!
"""

import os
import sys
from pathlib import Path

def check_requirements():
    """Check if all required packages are installed"""
    required_packages = [
        'telegram',
        'anthropic', 
        'dotenv'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Missing required packages:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\n💡 Install them with:")
        print("   pip install python-telegram-bot anthropic python-dotenv")
        return False
    
    return True

def check_env_file():
    """Check if .env file exists and has required variables"""
    env_file = Path(".env")
    
    if not env_file.exists():
        print("❌ .env file not found!")
        print("\n💡 Create a .env file with your tokens:")
        print("   TELEGRAM_BOT_TOKEN=your_telegram_token")
        print("   ANTHROPIC_API_KEY=your_anthropic_key")
        return False
    
    # Check if file has content
    content = env_file.read_text()
    if "TELEGRAM_BOT_TOKEN" not in content or "ANTHROPIC_API_KEY" not in content:
        print("❌ .env file missing required tokens!")
        print("\n💡 Add these lines to your .env file:")
        print("   TELEGRAM_BOT_TOKEN=your_telegram_token")
        print("   ANTHROPIC_API_KEY=your_anthropic_key")
        return False
    
    return True

def main():
    """Main function to run the bot with checks"""
    print("🎓 Starting Telegram Teacher Bot...")
    print("=" * 50)
    
    # Check requirements
    print("📦 Checking Python packages...")
    if not check_requirements():
        return
    print("✅ All packages found!")
    
    # Check environment file
    print("🔑 Checking environment variables...")
    if not check_env_file():
        return
    print("✅ Environment file configured!")
    
    # Check if main bot file exists
    if not Path("teacher_bot.py").exists():
        print("❌ teacher_bot.py not found!")
        print("💡 Make sure you have the main bot file in this directory")
        return
    
    print("✅ Bot file found!")
    print("\n🚀 Starting your AI teacher bot...")
    print("💬 Go to Telegram and message your bot!")
    print("🛑 Press Ctrl+C to stop the bot")
    print("=" * 50)
    
    # Import and run the main bot
    try:
        from teacher_bot import main as run_teacher_bot
        run_teacher_bot()
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"\n❌ Error starting bot: {e}")
        print("💡 Check your tokens and try again")

if __name__ == "__main__":
    main()
