#!/usr/bin/env python3

import asyncio
import logging.config
from pathlib import Path
import aiohttp

from symphony.bdk.core.config.loader import BdkConfigLoader
from symphony.bdk.core.symphony_bdk import SymphonyBdk
from symphony.bdk.core.activity.command import CommandActivity, CommandContext

# Configure logging (same as expenses bot)
logging_conf = Path(__file__).parent.parent / "resources" / "logging.conf"
logging.config.fileConfig(logging_conf, disable_existing_loggers=False)

# Custom Weather Command Activity (like the expenses bot pattern)
class WeatherCommandActivity(CommandActivity):
    """Handles weather requests like @Bot /weather London"""
    
    def __init__(self, messages):
        self._messages = messages
        super().__init__()
    
    def matches(self, context: CommandContext) -> bool:
        text = context.text_content.lower()
        bot_name = context.bot_display_name.lower()
        # Match "@Bot /weather" pattern (case insensitive)
        return f"@{bot_name} /weather" in text
    
    async def on_activity(self, context: CommandContext):
        print(f"WeatherCommandActivity triggered by {context.initiator.user.display_name}")
        print(f"Full text: '{context.text_content}'")
        
        text = context.text_content
        
        # Extract city from the message
        if "/weather" in text:
            parts = text.split("/weather", 1)
            if len(parts) > 1:
                city = parts[1].strip()
                if city:
                    print(f"City extracted: '{city}'")
                    
                    # Make weather API call
                    try:
                        headers = {'User-Agent': 'Symphony-Weather-Bot/1.0'}
                        
                        async with aiohttp.ClientSession() as session:
                            url = f"https://wttr.in/{city}?format=j1"
                            print(f"Calling URL: {url}")
                            
                            async with session.get(url, timeout=10, headers=headers) as response:
                                if response.status == 200:
                                    data = await response.json()
                                    current = data['current_condition'][0]
                                    
                                    weather_info = f"""<messageML>
                                        <h3>🌤️ Weather for {data['nearest_area'][0]['areaName'][0]['value']}</h3>
                                        <p><b>Condition:</b> {current['weatherDesc'][0]['value']}</p>
                                        <p><b>Temperature:</b> {current['temp_C']}°C (Feels like: {current['FeelsLikeC']}°C)</p>
                                        <p><b>Humidity:</b> {current['humidity']}%</p>
                                        <p><b>Wind:</b> {current['windspeedKmph']} km/h from {current['winddir16Point']}</p>
                                        <p><b>Visibility:</b> {current['visibility']} km</p>
                                    </messageML>"""
                                    
                                    await self._messages.send_message(context.stream_id, weather_info)
                                else:
                                    await self._messages.send_message(
                                        context.stream_id,
                                        f"<messageML>Sorry, I couldn't find weather for '<b>{city}</b>'. Please check the name and try again.</messageML>"
                                    )
                                    
                    except Exception as e:
                        print(f"Weather API error: {e}")
                        await self._messages.send_message(
                            context.stream_id,
                            f"<messageML>❌ Error getting weather for {city}: {str(e)}</messageML>"
                        )
                    return
        
        # No city provided
        await self._messages.send_message(
            context.stream_id,
            f"<messageML>Please provide a city name. Usage: <b>@{context.bot_display_name} /weather London</b></messageML>"
        )

# Custom Claude API Command Activity
class ClaudeAPIActivity(CommandActivity):
    """Handles Claude API requests like @Bot /ask What is the capital of France?"""
    
    def __init__(self, messages):
        self._messages = messages
        super().__init__()
    
    def matches(self, context: CommandContext) -> bool:
        text = context.text_content.lower()
        bot_name = context.bot_display_name.lower()
        # Match "@Bot /ask" pattern (case insensitive)
        return f"@{bot_name} /ask" in text
    
    async def on_activity(self, context: CommandContext):
        print(f"ClaudeAPIActivity triggered by {context.initiator.user.display_name}")
        print(f"Full text: '{context.text_content}'")
        
        text = context.text_content
        
        # Extract question from the message
        if "/ask" in text:
            parts = text.split("/ask", 1)
            if len(parts) > 1:
                question = parts[1].strip()
                if question:
                    print(f"Question extracted: '{question}'")
                    
                    # Call your local Claude API
                    try:
                        headers = {
                            'Content-Type': 'application/json',
                            'User-Agent': 'Symphony-Bot/1.0'
                        }
                        
                        payload = {
                            "question": question
                        }
                        
                        async with aiohttp.ClientSession() as session:
                            url = "http://127.0.0.1:8000/ask"
                            print(f"Calling local Claude API: {url}")
                            print(f"Payload: {payload}")
                            
                            async with session.post(url, json=payload, headers=headers, timeout=30) as response:
                                if response.status == 200:
                                    data = await response.json()
                                    print(f"Claude API response: {data}")
                                    
                                    # Extract the answer from the response
                                    # Adjust this based on your API's response format
                                    answer = data.get('answer', data.get('response', str(data)))
                                    
                                    claude_response = f"""<messageML>
                                        <h3>🤖 Claude's Response</h3>
                                        <p><b>Question:</b> {question}</p>
                                        <p><b>Answer:</b></p>
                                        <p>{answer}</p>
                                    </messageML>"""
                                    
                                    await self._messages.send_message(context.stream_id, claude_response)
                                else:
                                    print(f"Claude API returned status: {response.status}")
                                    error_text = await response.text()
                                    print(f"Error response: {error_text}")
                                    await self._messages.send_message(
                                        context.stream_id,
                                        f"<messageML>❌ Claude API error: Status {response.status}</messageML>"
                                    )
                                    
                    except aiohttp.ClientConnectorError:
                        print("Connection error - is your local API running on port 8000?")
                        await self._messages.send_message(
                            context.stream_id,
                            "<messageML>❌ Cannot connect to local Claude API. Is it running on http://127.0.0.1:8000?</messageML>"
                        )
                    except Exception as e:
                        print(f"Claude API error: {e}")
                        await self._messages.send_message(
                            context.stream_id,
                            f"<messageML>❌ Error calling Claude API: {str(e)}</messageML>"
                        )
                    return
        
        # No question provided
        await self._messages.send_message(
            context.stream_id,
            f"<messageML>Please provide a question. Usage: <b>@{context.bot_display_name} /ask What is the capital of France?</b></messageML>"
        )

async def run():
    """Main function to configure and run the Symphony Bot."""
    print("Starting Weather Bot...")

    # Load configuration using the working pattern from expenses bot
    config = BdkConfigLoader.load_from_file(Path(__file__).parent.parent / "resources" / "config.yaml")

    async with SymphonyBdk(config) as bdk:
        activities = bdk.activities()
        
        # Register custom activities
        print("Registering WeatherCommandActivity...")
        activities.register(WeatherCommandActivity(bdk.messages()))
        
        print("Registering ClaudeAPIActivity...")
        activities.register(ClaudeAPIActivity(bdk.messages()))

        # Keep simple slash commands that work (without arguments)
        @activities.slash("/hello", description="Say hello to the bot")
        async def hello(context: CommandContext):
            print(f"Hello command received from {context.initiator.user.display_name}")
            user_name = context.initiator.user.display_name
            response = f"""<messageML>Hello, <b>{user_name}</b>! I'm the Weather Bot with Claude integration. 
            
Try these commands:
• <b>@{context.bot_display_name} /weather London</b> - Get weather
• <b>@{context.bot_display_name} /ask What is the capital of France?</b> - Ask Claude anything
👋</messageML>"""
            await bdk.messages().send_message(context.stream_id, response)

        @activities.slash("/test", description="Simple test command")
        async def test_cmd(context: CommandContext):
            print(f"Test command received from {context.initiator.user.display_name}")
            await bdk.messages().send_message(
                context.stream_id,
                "<messageML>✅ Test command works!</messageML>"
            )

        # Start the datafeed loop
        datafeed_loop = bdk.datafeed()
        print("Starting datafeed...")
        await datafeed_loop.start()


if __name__ == "__main__":
    asyncio.run(run())