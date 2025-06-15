import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import anthropic
from datetime import datetime
import json
import asyncio
import sqlite3
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class TeacherBot:
    def __init__(self, telegram_token, anthropic_api_key=None):
        self.telegram_token = telegram_token
        self.anthropic_client = None
        if anthropic_api_key:
            self.anthropic_client = anthropic.Anthropic(api_key=anthropic_api_key)
        
        # Initialize SQLite database for user data
        self.init_database()
        
    def init_database(self):
        """Initialize SQLite database for persistent storage"""
        db_path = Path("teacher_bot.db")
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        
        # Create tables if they don't exist
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                first_name TEXT,
                learning_goals TEXT,
                difficulty_level TEXT DEFAULT 'beginner',
                learning_style TEXT DEFAULT 'balanced',
                conversation_history TEXT,
                progress TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.conn.commit()
    
    def get_user_context(self, user_id):
        """Get or create user context from database"""
        cursor = self.conn.execute(
            'SELECT * FROM users WHERE user_id = ?', (user_id,)
        )
        user_row = cursor.fetchone()
        
        if user_row:
            # Parse stored JSON data
            return {
                'user_id': user_row[0],
                'first_name': user_row[1],
                'learning_goals': json.loads(user_row[2] or '[]'),
                'difficulty_level': user_row[3],
                'learning_style': user_row[4],
                'conversation_history': json.loads(user_row[5] or '[]'),
                'progress': json.loads(user_row[6] or '{}'),
                'created_at': user_row[7],
                'last_active': user_row[8]
            }
        else:
            # Create new user
            default_context = {
                'user_id': user_id,
                'first_name': '',
                'learning_goals': [],
                'difficulty_level': 'beginner',
                'learning_style': 'balanced',
                'conversation_history': [],
                'progress': {'total_interactions': 0, 'achievements': []},
                'created_at': datetime.now().isoformat(),
                'last_active': datetime.now().isoformat()
            }
            return default_context
    
    def save_user_context(self, user_context):
        """Save user context to database"""
        self.conn.execute('''
            INSERT OR REPLACE INTO users 
            (user_id, first_name, learning_goals, difficulty_level, learning_style, 
             conversation_history, progress, last_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_context['user_id'],
            user_context['first_name'],
            json.dumps(user_context['learning_goals']),
            user_context['difficulty_level'],
            user_context['learning_style'],
            json.dumps(user_context['conversation_history'][-50:]),  # Keep last 50 messages
            json.dumps(user_context['progress']),
            datetime.now().isoformat()
        ))
        self.conn.commit()
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        user_context = self.get_user_context(user.id)
        
        welcome_message = f"""
🎓 Hello {user.first_name}! I'm your personal AI teacher!

I'm here to help you learn anything you want. I can:
• Explain complex topics in simple terms
• Create custom lessons based on your goals
• Adapt to your learning style and pace
• Track your progress
• Provide quizzes and exercises
• Answer your questions anytime

Let's start by setting up your learning profile!

What would you like to learn today?
        """
        
        keyboard = [
            [InlineKeyboardButton("📚 Set Learning Goals", callback_data='set_goals')],
            [InlineKeyboardButton("🎯 Choose Difficulty Level", callback_data='set_difficulty')],
            [InlineKeyboardButton("🧠 Learning Style Quiz", callback_data='learning_style')],
            [InlineKeyboardButton("📖 Start Learning Now", callback_data='start_learning')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(welcome_message, reply_markup=reply_markup)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = """
🔧 **Available Commands:**

/start - Initialize your learning journey
/goals - Set or view your learning goals
/progress - Check your learning progress
/quiz - Take a quick quiz on current topic
/explain [topic] - Get explanation of any topic
/difficulty [level] - Set difficulty (beginner/intermediate/advanced)
/topic [subject] - Switch to a new learning topic
/help - Show this help message

💡 **Tips:**
• Just send me any question to get started
• I adapt explanations to your level
• Ask for examples, analogies, or deeper explanations
• Request practice problems or quizzes anytime
        """
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def goals_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /goals command"""
        user_context = self.get_user_context(update.effective_user.id)
        
        if not user_context['learning_goals']:
            message = "🎯 You haven't set any learning goals yet!\n\nTell me what you'd like to learn. Examples:\n• Learn Python programming\n• Understand calculus\n• Master Spanish conversation\n• Study world history"
        else:
            goals_list = '\n'.join([f"• {goal}" for goal in user_context['learning_goals']])
            message = f"🎯 **Your Learning Goals:**\n\n{goals_list}\n\nSend me a new goal to add it, or ask questions about any of these topics!"
        
        await update.message.reply_text(message, parse_mode='Markdown')
    
    async def progress_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /progress command"""
        user_context = self.get_user_context(update.effective_user.id)
        
        total_interactions = len(user_context['conversation_history'])
        current_topic = user_context.get('current_topic', 'No topic selected')
        difficulty = user_context.get('difficulty_level', 'beginner').title()
        
        progress_message = f"""
📊 **Your Learning Progress:**

🎯 Current Topic: {current_topic}
📈 Difficulty Level: {difficulty}
💬 Total Interactions: {total_interactions}
📚 Learning Goals: {len(user_context['learning_goals'])}

🏆 **Achievements:**
{'🥇 Active Learner' if total_interactions > 10 else '🥉 Getting Started'}
{'📖 Goal Setter' if user_context['learning_goals'] else ''}

Keep up the great work! Ask me anything to continue learning.
        """
        
        await update.message.reply_text(progress_message, parse_mode='Markdown')
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button callbacks"""
        query = update.callback_query
        await query.answer()
        
        user_context = self.get_user_context(query.from_user.id)
        
        if query.data == 'set_goals':
            await query.edit_message_text(
                "🎯 **Set Your Learning Goals**\n\n"
                "Tell me what you want to learn! You can mention:\n"
                "• Subjects (Math, Physics, Programming)\n"
                "• Skills (Writing, Problem-solving)\n"
                "• Languages (Spanish, French, Japanese)\n"
                "• Hobbies (Guitar, Photography)\n\n"
                "Just type your goal and I'll add it to your profile!"
            )
        
        elif query.data == 'set_difficulty':
            keyboard = [
                [InlineKeyboardButton("🌱 Beginner", callback_data='diff_beginner')],
                [InlineKeyboardButton("🌿 Intermediate", callback_data='diff_intermediate')],
                [InlineKeyboardButton("🌳 Advanced", callback_data='diff_advanced')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "🎯 **Choose Your Difficulty Level:**\n\n"
                "🌱 **Beginner** - New to the topic, need basic explanations\n"
                "🌿 **Intermediate** - Some knowledge, ready for deeper concepts\n"
                "🌳 **Advanced** - Strong foundation, want challenging material",
                reply_markup=reply_markup
            )
        
        elif query.data.startswith('diff_'):
            level = query.data.replace('diff_', '')
            user_context['difficulty_level'] = level
            await query.edit_message_text(
                f"✅ Difficulty level set to **{level.title()}**!\n\n"
                "I'll adapt my explanations accordingly. What would you like to learn about?"
            )
        
        elif query.data == 'learning_style':
            keyboard = [
                [InlineKeyboardButton("📖 Visual", callback_data='style_visual')],
                [InlineKeyboardButton("🎧 Auditory", callback_data='style_auditory')],
                [InlineKeyboardButton("✋ Hands-on", callback_data='style_kinesthetic')],
                [InlineKeyboardButton("🔄 Mixed", callback_data='style_mixed')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "🧠 **What's Your Learning Style?**\n\n"
                "📖 **Visual** - Learn best with diagrams, charts, images\n"
                "🎧 **Auditory** - Prefer explanations and discussions\n"
                "✋ **Hands-on** - Learn by doing and practicing\n"
                "🔄 **Mixed** - Combination of all styles",
                reply_markup=reply_markup
            )
        
        elif query.data.startswith('style_'):
            style = query.data.replace('style_', '')
            user_context['learning_style'] = style
            await query.edit_message_text(
                f"✅ Learning style set to **{style.title()}**!\n\n"
                "I'll tailor my teaching methods to match your preferences. Ready to start learning?"
            )
        
        elif query.data == 'start_learning':
            await query.edit_message_text(
                "🚀 **Let's Start Learning!**\n\n"
                "Ask me anything you want to learn about. I can:\n"
                "• Explain concepts step by step\n"
                "• Provide examples and analogies\n"
                "• Create practice exercises\n"
                "• Answer follow-up questions\n\n"
                "What's your first question?"
            )
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle regular messages"""
        user_id = update.effective_user.id
        user_context = self.get_user_context(user_id)
        message_text = update.message.text
        
        # Update user info
        user_context['first_name'] = update.effective_user.first_name
        
        # Add to conversation history
        user_context['conversation_history'].append({
            'timestamp': datetime.now().isoformat(),
            'user_message': message_text,
            'type': 'user_question'
        })
        
        # Update progress
        user_context['progress']['total_interactions'] = user_context['progress'].get('total_interactions', 0) + 1
        
        # Check if user is setting a goal
        if any(word in message_text.lower() for word in ['learn', 'study', 'understand', 'master', 'teach me']):
            if len(user_context['learning_goals']) < 10:  # Limit goals
                user_context['learning_goals'].append(message_text)
                await update.message.reply_text(
                    f"✅ Added to your learning goals: **{message_text}**\n\n"
                    "Great! I'll help you achieve this goal. What specific aspect would you like to start with?",
                    parse_mode='Markdown'
                )
                self.save_user_context(user_context)
                return
        
        # Generate educational response
        response = await self.generate_educational_response(message_text, user_context)
        
        # Add response to history
        user_context['conversation_history'].append({
            'timestamp': datetime.now().isoformat(),
            'bot_response': response,
            'type': 'teaching_response'
        })
        
        # Check for achievements
        total_interactions = user_context['progress']['total_interactions']
        achievements = user_context['progress'].get('achievements', [])
        
        if total_interactions == 1 and 'First Question!' not in achievements:
            achievements.append('First Question!')
            response += "\n\n🏆 **Achievement Unlocked:** First Question!"
        elif total_interactions == 10 and 'Active Learner!' not in achievements:
            achievements.append('Active Learner!')
            response += "\n\n🏆 **Achievement Unlocked:** Active Learner!"
        elif len(user_context['learning_goals']) >= 3 and 'Goal Setter!' not in achievements:
            achievements.append('Goal Setter!')
            response += "\n\n🏆 **Achievement Unlocked:** Goal Setter!"
        
        user_context['progress']['achievements'] = achievements
        
        # Save updated context
        self.save_user_context(user_context)
        
        await update.message.reply_text(response, parse_mode='Markdown')
    
    async def generate_educational_response(self, question, user_context):
        """Generate educational response using Anthropic Claude"""
        difficulty = user_context.get('difficulty_level', 'beginner')
        learning_style = user_context.get('learning_style', 'balanced')
        goals = user_context.get('learning_goals', [])
        
        # Use Anthropic Claude if available
        if self.anthropic_client:
            try:
                system_prompt = f"""You are an expert teacher and tutor. Your student has these characteristics:
- Difficulty level: {difficulty}
- Learning style: {learning_style}
- Learning goals: {', '.join(goals)}

Provide educational responses that:
1. Match the student's difficulty level ({difficulty})
2. Use their preferred learning style ({learning_style})
3. Include examples and analogies appropriate for their level
4. Break down complex concepts into digestible parts
5. Encourage questions and curiosity
6. Offer practice opportunities when relevant
7. Use emojis strategically for engagement
8. Keep responses concise but comprehensive for Telegram

For difficulty levels:
- Beginner: Use simple language, analogies, step-by-step explanations
- Intermediate: Balance detail with clarity, provide examples
- Advanced: Use technical language, explore deeper concepts

For learning styles:
- Visual: Use descriptions, step-by-step lists, structured formatting
- Auditory: Conversational tone, explanations through dialogue
- Kinesthetic: Hands-on examples, practical applications
- Balanced: Mix of all approaches

Be encouraging, patient, and adapt your explanations accordingly."""
                
                message = self.anthropic_client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=1000,
                    temperature=0.7,
                    system=system_prompt,
                    messages=[
                        {
                            "role": "user",
                            "content": question
                        }
                    ]
                )
                
                return message.content[0].text
                
            except Exception as e:
                logger.error(f"Anthropic API error: {e}")
                # Fall back to rule-based response
        
        # Rule-based educational response
        return self.generate_rule_based_response(question, user_context)
    
    def generate_rule_based_response(self, question, user_context):
        """Generate educational response using rules"""
        difficulty = user_context.get('difficulty_level', 'beginner')
        
        # Basic educational response template
        if 'what is' in question.lower() or 'explain' in question.lower():
            if difficulty == 'beginner':
                return f"""
📚 **Great question!** Let me explain this in simple terms:

{question} is a concept that... 

🔍 **Simple explanation:**
Think of it like... (analogy)

📝 **Key points to remember:**
• Point 1
• Point 2  
• Point 3

❓ **Want to explore more?** Ask me:
• "Can you give me an example?"
• "How is this used in real life?"
• "What's the next step to learn?"
                """
            else:
                return f"""
🎓 **Excellent question!** Here's a detailed explanation:

{question} involves several important concepts...

🧠 **Core principles:**
The fundamental idea is...

🔬 **Advanced concepts:**
This connects to...

💡 **Practical applications:**
You'll see this used in...

🚀 **Ready for the next level?** Try asking about related topics or request practice problems!
                """
        
        # Default encouraging response
        return """
🤔 **Interesting question!** I'd love to help you learn about this.

Could you be more specific about what aspect you'd like to understand? For example:
• Are you looking for a basic explanation?
• Do you want to see examples?
• Are you trying to solve a specific problem?

The more details you give me, the better I can tailor my explanation to your needs!

💡 **Tip:** Try starting your questions with phrases like "Explain...", "How does...", or "What is..."
        """
    
    async def quiz_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Generate a quiz question"""
        user_context = self.get_user_context(update.effective_user.id)
        current_topic = user_context.get('current_topic', 'general knowledge')
        
        quiz_message = f"""
🧩 **Quick Quiz Time!**

Topic: {current_topic}

**Question:** What is 2 + 2?
A) 3
B) 4  
C) 5
D) 6

Reply with your answer (A, B, C, or D)!

💡 *This is a sample question. In a full implementation, questions would be generated based on your current learning topic and difficulty level.*
        """
        
        await update.message.reply_text(quiz_message, parse_mode='Markdown')

def main():
    """Main function to run the bot"""
    # Get tokens from environment variables
    TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')  # Required for Claude
    
    if not TELEGRAM_TOKEN:
        print("Please set TELEGRAM_BOT_TOKEN environment variable")
        return
    
    if not ANTHROPIC_API_KEY:
        print("Warning: ANTHROPIC_API_KEY not set. Bot will use basic responses only.")
    
    # Create bot instance
    teacher_bot = TeacherBot(TELEGRAM_TOKEN, ANTHROPIC_API_KEY)
    
    # Create application
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", teacher_bot.start_command))
    application.add_handler(CommandHandler("help", teacher_bot.help_command))
    application.add_handler(CommandHandler("goals", teacher_bot.goals_command))
    application.add_handler(CommandHandler("progress", teacher_bot.progress_command))
    application.add_handler(CommandHandler("quiz", teacher_bot.quiz_command))
    application.add_handler(CallbackQueryHandler(teacher_bot.button_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, teacher_bot.handle_message))
    
    # Start the bot
    print("🎓 Teacher Bot is starting...")
    print("Press Ctrl+C to stop the bot")
    
    try:
        application.run_polling()
    except KeyboardInterrupt:
        print("Bot stopped by user")
    finally:
        teacher_bot.conn.close()

if __name__ == '__main__':
    main()
