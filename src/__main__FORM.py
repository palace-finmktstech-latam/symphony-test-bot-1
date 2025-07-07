import asyncio
import logging.config
from pathlib import Path

from symphony.bdk.core.config.loader import BdkConfigLoader
from symphony.bdk.core.symphony_bdk import SymphonyBdk
from symphony.bdk.core.activity.command import CommandActivity, CommandContext
from symphony.bdk.core.activity.form import FormReplyActivity, FormReplyContext
from symphony.bdk.core.activity.user_joined_room import UserJoinedRoomActivity, UserJoinedRoomContext
from symphony.bdk.core.service.message.message_service import MessageService
from symphony.bdk.core.service.user.user_service import UserService
import re
from datetime import datetime

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


# Trading form handler
class TradingFormHandler(FormReplyActivity):
    def __init__(self, messages):
        self._messages = messages
        super().__init__()
    
    def matches(self, context: FormReplyContext) -> bool:
        return context.form_id == "trading_form"
    
    async def on_activity(self, context: FormReplyContext):
        # Extract form data
        currency_pair = context.get_form_value("currency_pair")
        amount = context.get_form_value("amount")
        price = context.get_form_value("price")
        action = context.get_form_value("action")
        user_name = context.initiator.user.display_name
        
        # Print to console (screen)
        print("="*50)
        print("TRADING FORM SUBMITTED")
        print("="*50)
        print(f"User: {user_name}")
        print(f"Currency Pair: {currency_pair}")
        print(f"Amount: {amount}")
        print(f"Price: {price}")
        print(f"Action: {action}")
        print("="*50)
        
        # Send confirmation back to user
        confirmation = f"""<messageML>
            <h2>✅ Trade Order Received!</h2>
            <p><b>Trader:</b> {user_name}</p>
            <p><b>Action:</b> {action}</p>
            <p><b>Currency Pair:</b> {currency_pair}</p>
            <p><b>Amount:</b> {amount}</p>
            <p><b>Price:</b> {price}</p>
            <p><i>Order details printed to console ✓</i></p>
            </messageML>"""
        
        await self._messages.send_message(
            context.source_event.stream.stream_id,
            confirmation
        )


async def run():
    config = BdkConfigLoader.load_from_file(Path(__file__).parent.parent / "resources" / "config.yaml")

    async with SymphonyBdk(config) as bdk:
        activities = bdk.activities()
        
        # Register existing activities
        activities.register(EchoCommandActivity(bdk.messages()))
        activities.register(GreetUserJoinedActivity(bdk.messages(), bdk.users()))

         # Register trading form handler
        activities.register(TradingFormHandler(bdk.messages()))
        
        # Command to show the trading form
        @activities.slash("/trade")
        async def show_trading_form(context):
            trading_form = """<messageML>
                <h2>💰 Currency Trading Form</h2>

                <form id="trading_form">
                    <h3>Currency Pair:</h3>
                    <select name="currency_pair" required="true">
                        <option value="EUR/USD">EUR/USD</option>
                        <option value="GBP/USD">GBP/USD</option>
                        <option value="USD/JPY">USD/JPY</option>
                        <option value="AUD/USD">AUD/USD</option>
                        <option value="USD/CAD">USD/CAD</option>
                    </select>
                    
                    <h3>Amount:</h3>
                    <text-field name="amount" placeholder="Enter amount (e.g. 100000)" required="true"></text-field>
                    
                    <h3>Price:</h3>
                    <text-field name="price" placeholder="Enter price (e.g. 1.2345)" required="true"></text-field>
                    
                    <h3>Action:</h3>
                    <button name="buy">🟢 BUY</button>
                    <button name="sell">🔴 SELL</button>
                </form>
                </messageML>"""
            
            await bdk.messages().send_message(context.stream_id, trading_form)


        datafeed_loop = bdk.datafeed()
        print("Starting datafeed...")
        await datafeed_loop.start()

if __name__ == "__main__":
    asyncio.run(run())