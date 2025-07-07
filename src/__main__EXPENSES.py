import asyncio
import logging.config
from pathlib import Path

from symphony.bdk.core.config.loader import BdkConfigLoader
from symphony.bdk.core.symphony_bdk import SymphonyBdk
from symphony.bdk.core.activity.command import CommandActivity, CommandContext
from symphony.bdk.core.activity.user_joined_room import UserJoinedRoomActivity, UserJoinedRoomContext
from symphony.bdk.core.service.message.message_service import MessageService
from symphony.bdk.core.service.user.user_service import UserService
import re
from datetime import datetime

# Global storage for demo
EXPENSES = []

# Configure logging
logging_conf = Path(__file__).parent.parent / "resources" / "logging.conf"
logging.config.fileConfig(logging_conf, disable_existing_loggers=False)

# Existing activities
class EchoCommandActivity(CommandActivity):
    """Example of a complex command that just echoes what is after @bot-name /echo"""
    command_name = "/echo "

    def __init__(self, messages: MessageService):
        self._messages = messages
        super().__init__()

    def matches(self, context: CommandContext) -> bool:
        return context.text_content.startswith("@" + context.bot_display_name + " " + self.command_name)

    async def on_activity(self, context: CommandContext):
        text_to_echo = context.text_content[context.text_content.index(self.command_name) + len(self.command_name):]
        await self._messages.send_message(context.stream_id, f"<messageML>{text_to_echo}</messageML>")

class GreetUserJoinedActivity(UserJoinedRoomActivity):
    """Greets a user when joining a room"""

    def __init__(self, messages: MessageService, users: UserService):
        super().__init__()
        self._messages = messages
        self._users = users

    def matches(self, context: UserJoinedRoomContext) -> bool:
        return True

    async def on_activity(self, context: UserJoinedRoomContext):
        user_details = await self._users.get_user_detail(context.affected_user_id)
        await self._messages.send_message(context.stream_id,
                                          f"<messageML>Hello {user_details.user_attributes.display_name}!</messageML>")

# Simple expense tracking without forms
class ExpenseTrackerActivity(CommandActivity):
    """Tracks expenses through natural language"""
    
    def __init__(self, messages):
        self._messages = messages
        super().__init__()
    
    def matches(self, context: CommandContext) -> bool:
        text = context.text_content.lower()
        expense_keywords = ['spent', 'paid', 'bought', 'expense', 'cost']
        return any(keyword in text for keyword in expense_keywords)
    
    async def on_activity(self, context: CommandContext):
        text = context.text_content
        user_name = context.initiator.user.display_name
        
        expense_data = self._parse_expense(text)
        
        if expense_data:
            # Save the expense automatically with default category
            expense = {
                'user': user_name,
                'amount': float(expense_data['amount']),
                'description': expense_data['description'],
                'category': 'other',
                'date': datetime.now().strftime('%Y-%m-%d'),
                'timestamp': datetime.now()
            }
            EXPENSES.append(expense)
            
            confirmation = f"""<messageML>
<h2>✅ Expense Tracked!</h2>
<p><b>{user_name}</b> spent <b>${expense_data['amount']}</b> on <b>{expense_data['description']}</b></p>
<p>📦 Category: Other</p>
<p>📅 Date: {expense['date']}</p>
<p>Total expenses tracked: <b>{len(EXPENSES)}</b></p>
<p><i>Use @{context.bot_display_name} /expenses to see your summary</i></p>
</messageML>"""
            
            await self._messages.send_message(context.stream_id, confirmation)
        else:
            # Couldn't parse the expense
            await self._messages.send_message(context.stream_id, f"""<messageML>
<h2>💡 Expense Tip</h2>
<p>Hi {user_name}! I can track expenses when you mention amounts and what you bought.</p>
<p><b>Try saying:</b></p>
<ul>
<li>"I spent $25 on lunch"</li>
<li>"Paid $150 for software"</li>
<li>"Bought coffee for $4.50"</li>
</ul>
<p>Use @{context.bot_display_name} /expenses to see your total!</p>
</messageML>""")
    
    def _parse_expense(self, text):
        # Look for money amounts ($25, $25.50, 25.50, etc.)
        money_pattern = r'\$?(\d+(?:\.\d{2})?)'
        money_match = re.search(money_pattern, text)
        
        if money_match:
            amount = money_match.group(1)
            
            # Try to extract description (everything after common expense verbs)
            expense_verbs = ['spent', 'paid', 'bought', 'cost']
            description = text
            
            for verb in expense_verbs:
                if verb in text.lower():
                    parts = text.lower().split(verb, 1)
                    if len(parts) > 1:
                        # Clean up the description
                        desc = parts[1].strip()
                        desc = re.sub(r'\$?\d+(?:\.\d{2})?', '', desc).strip()
                        desc = desc.replace('on ', '').replace('for ', '').strip()
                        if desc:
                            description = desc
                            break
            
            # Clean up description
            if description == text:
                description = "misc expense"
            
            return {
                'amount': amount,
                'description': description
            }
        
        return None

async def run():
    config = BdkConfigLoader.load_from_file(Path(__file__).parent.parent / "resources" / "config.yaml")

    async with SymphonyBdk(config) as bdk:
        activities = bdk.activities()
        
        # Register existing activities
        activities.register(EchoCommandActivity(bdk.messages()))
        activities.register(GreetUserJoinedActivity(bdk.messages(), bdk.users()))
        
        # Register new expense activities
        activities.register(ExpenseTrackerActivity(bdk.messages()))
        
        # Add expense summary slash command
        @activities.slash("/expenses")
        async def show_expenses(context: CommandContext):
            if not EXPENSES:
                await bdk.messages().send_message(
                    context.stream_id,
                    "<messageML>📊 No expenses tracked yet! Try saying 'I spent $20 on lunch' to get started.</messageML>"
                )
                return
            
            total = sum(exp['amount'] for exp in EXPENSES)
            user_expenses = [exp for exp in EXPENSES if exp['user'] == context.initiator.user.display_name]
            user_total = sum(exp['amount'] for exp in user_expenses)
            
            summary = f"""<messageML>
<h2>📊 Expense Summary</h2>
<p><b>Your Total: ${user_total:.2f}</b></p>
<p>Your Entries: {len(user_expenses)}</p>
<p><i>Everyone's Total: ${total:.2f} ({len(EXPENSES)} entries)</i></p>

<h3>Your Recent Expenses:</h3>"""
            
            for exp in user_expenses[-5:]:  # Last 5 user expenses
                summary += f"<p>• ${exp['amount']:.2f} - {exp['description']} ({exp['date']})</p>"
            
            summary += """
<h3>💡 Tips:</h3>
<ul>
<li>Say "I spent $25 on lunch" to track expenses</li>
<li>Say "Paid $150 for software license"</li>
<li>Say "Bought coffee for $4.50"</li>
</ul>
</messageML>"""
            
            await bdk.messages().send_message(context.stream_id, summary)

        # Add a clear expenses command for testing
        @activities.slash("/clear")
        async def clear_expenses(context: CommandContext):
            global EXPENSES
            old_count = len(EXPENSES)
            EXPENSES = []
            await bdk.messages().send_message(
                context.stream_id,
                f"<messageML>🗑️ Cleared {old_count} expenses. Ready for fresh tracking!</messageML>"
            )

        datafeed_loop = bdk.datafeed()
        print("Starting datafeed...")
        await datafeed_loop.start()

if __name__ == "__main__":
    asyncio.run(run())