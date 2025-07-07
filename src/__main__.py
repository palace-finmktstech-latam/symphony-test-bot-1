#!/usr/bin/env python3

import asyncio
import logging.config
from pathlib import Path
import csv
import json
import aiohttp

from symphony.bdk.core.config.loader import BdkConfigLoader
from symphony.bdk.core.symphony_bdk import SymphonyBdk
from symphony.bdk.core.activity.command import CommandActivity, CommandContext
from symphony.bdk.core.activity.form import FormReplyActivity, FormReplyContext

# Configure logging
logging_conf = Path(__file__).parent.parent / "resources" / "logging.conf"
logging.config.fileConfig(logging_conf, disable_existing_loggers=False)

# Global client data storage
CLIENTS = []
FAVOURITES = []

# Trades API configuration
TRADES_API_BASE_URL = "http://127.0.0.1:8001"

def load_clients_from_csv(csv_path="clients.csv"):
    """Load clients from CSV file."""
    global CLIENTS, FAVOURITES
    
    try:
        csv_file_path = Path(__file__).parent.parent / csv_path
        
        with open(csv_file_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            CLIENTS = []
            FAVOURITES = []
            
            for row in reader:
                client = {
                    'client_id': row['client_id'].strip(),
                    'client_name': row['client_name'].strip(),
                    'is_favourite': row['is_favourite'].strip().lower() == 'true'
                }
                CLIENTS.append(client)
                
                if client['is_favourite']:
                    FAVOURITES.append(client)
            
            # Sort favourites by name and limit to 10
            FAVOURITES.sort(key=lambda x: x['client_name'])
            FAVOURITES = FAVOURITES[:10]
            
            print(f"Loaded {len(CLIENTS)} clients, {len(FAVOURITES)} favourites")
            return True
            
    except FileNotFoundError:
        print(f"CSV file not found: {csv_path}")
        # Create sample data for testing
        CLIENTS = [
            {'client_id': '12345', 'client_name': 'Juan Pérez', 'is_favourite': True},
            {'client_id': '67890', 'client_name': 'María García', 'is_favourite': False},
            {'client_id': '11111', 'client_name': 'Carlos Rodriguez', 'is_favourite': True},
            {'client_id': '22222', 'client_name': 'Ana Martínez', 'is_favourite': True},
            {'client_id': '33333', 'client_name': 'José López', 'is_favourite': False},
            {'client_id': '44444', 'client_name': 'Carmen Sánchez', 'is_favourite': True},
            {'client_id': '55555', 'client_name': 'Luis Fernández', 'is_favourite': False},
            {'client_id': '66666', 'client_name': 'Isabel Ruiz', 'is_favourite': True}
        ]
        
        FAVOURITES = [client for client in CLIENTS if client['is_favourite']]
        print("Using sample client data")
        return False
        
    except Exception as e:
        print(f"Error loading CSV: {e}")
        return False

async def get_client_trades(client_id):
    """Fetch last 5 trades for a client from the trades API."""
    try:
        async with aiohttp.ClientSession() as session:
            url = f"{TRADES_API_BASE_URL}/trades/{client_id}"
            print(f"Calling trades API: {url}")
            
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    trades = await response.json()
                    print(f"Retrieved {len(trades)} trades for client {client_id}")
                    return trades
                elif response.status == 404:
                    print(f"No trades found for client {client_id}")
                    return []
                else:
                    print(f"Trades API returned status {response.status}")
                    return None
                    
    except aiohttp.ClientConnectorError:
        print("Cannot connect to trades API - is it running on port 8000?")
        return None
    except asyncio.TimeoutError:
        print("Trades API request timed out")
        return None
    except Exception as e:
        print(f"Error calling trades API: {e}")
        return None

def create_trades_table(trades, client_name):
    """Create compact trades table for display."""
    if not trades:
        return f"""<div style="font-size: 10px; padding: 4px; border-radius: 2px; margin-top: 4px;">
            <b>📊 No trades found for {client_name}</b>
        </div>"""
    
    # Create compact table
    table_html = f"""<div style="font-size: 9px; padding: 4px; border-radius: 2px; margin-top: 4px;">
        <b style="font-size: 10px;">📊 Last {len(trades)} trade(s) for {client_name}:</b><br/>
        <table style="width: 100%; font-size: 8px; border-collapse: collapse; margin-top: 2px;">
            <tr>
                <th style="padding: 1px 3px; border: 1px solid #dee2e6;">Trade#</th>
                <th style="padding: 1px 3px; border: 1px solid #dee2e6;">Date</th>
                <th style="padding: 1px 3px; border: 1px solid #dee2e6;">Product</th>
                <th style="padding: 1px 3px; border: 1px solid #dee2e6;">Dir</th>
                <th style="padding: 1px 3px; border: 1px solid #dee2e6;">Currency Pair</th>
                <th style="padding: 1px 3px; border: 1px solid #dee2e6;">Amount</th>
                <th style="padding: 1px 3px; border: 1px solid #dee2e6;">Price</th>
                <th style="padding: 1px 3px; border: 1px solid #dee2e6;">Spread</th>
            </tr>
    """
    
    for trade in trades:
        # Format direction as Buy/Sell with color
        direction = trade.get('direction', 'N/A')
        dir_color = '#28a745' if direction == 'Buy' else '#dc3545' if direction == 'Sell' else '#6c757d'
        
        # Format amount with thousands separator
        try:
            amount = f"{float(trade.get('notional_amount', 0)):,.0f}"
        except:
            amount = trade.get('notional_amount', 'N/A')
        
        table_html += f"""
            <tr>
                <td style="padding: 1px 3px; border: 1px solid #dee2e6;">{trade.get('trade_number', 'N/A')}</td>
                <td style="padding: 1px 3px; border: 1px solid #dee2e6;">{trade.get('trade_date', 'N/A')}</td>
                <td style="padding: 1px 3px; border: 1px solid #dee2e6;">{trade.get('product', 'N/A')}</td>
                <td style="padding: 1px 3px; border: 1px solid #dee2e6; color: {dir_color}; font-weight: bold;">{direction}</td>
                <td style="padding: 1px 3px; border: 1px solid #dee2e6;">{trade.get('currency_pair', 'N/A')}</td>
                <td style="padding: 1px 3px; border: 1px solid #dee2e6;">{amount}</td>
                <td style="padding: 1px 3px; border: 1px solid #dee2e6;">{trade.get('price', 'N/A')}</td>
                <td style="padding: 1px 3px; border: 1px solid #dee2e6;">{trade.get('spread', 'N/A')}</td>
            </tr>
        """
    
    table_html += """
        </table>
    </div>"""
    
    return table_html
    """Search clients by name and ID."""
    if not query:
        return []
    
    query = query.lower().strip()
    matches = []
    
    for client in CLIENTS:
        client_name_lower = client['client_name'].lower()
        client_id_lower = client['client_id'].lower()
        
        # Split query into terms
        query_terms = query.split()
        
        # Check if all query terms match either name or ID
        match = True
        for term in query_terms:
            if term not in client_name_lower and term not in client_id_lower:
                match = False
                break
        
        if match:
            matches.append(client)
    
    # Sort matches: favourites first, then by name
    matches.sort(key=lambda x: (not x['is_favourite'], x['client_name']))
    
    return matches

def search_clients(query):
    """Search clients by name and ID."""
    if not query:
        return []
    
    query = query.lower().strip()
    matches = []
    
    for client in CLIENTS:
        client_name_lower = client['client_name'].lower()
        client_id_lower = client['client_id'].lower()
        
        # Split query into terms
        query_terms = query.split()
        
        # Check if all query terms match either name or ID
        match = True
        for term in query_terms:
            if term not in client_name_lower and term not in client_id_lower:
                match = False
                break
        
        if match:
            matches.append(client)
    
    # Sort matches: favourites first, then by name
    matches.sort(key=lambda x: (not x['is_favourite'], x['client_name']))
    
    return matches

def create_client_selection_form(matches, request_id):
    """Create Symphony Elements form for client selection."""
    if not matches:
        return "<messageML>No clients found matching your search.</messageML>"
    
    form_html = f"""<messageML>
        <h3>📋 Client Search Results</h3>
        <form id="client_selection_{request_id}">
            <h4>Select Client:</h4>
    """
    
    # Add client selection buttons - use name attribute with client_id as value
    for i, client in enumerate(matches):
        favourite_star = "⭐ " if client['is_favourite'] else ""
        button_name = f"client_{client['client_id']}"
        form_html += f"""
            <button name="{button_name}" type="action">
                {favourite_star}{client['client_name']} - ID: {client['client_id']}
            </button><br/>
        """
    
    form_html += """
        </form>
    </messageML>"""
    
    return form_html

def create_favourites_bar():
    """Create favourites bar with top 10 favourite clients."""
    if not FAVOURITES:
        return ""
    
    favourites_html = """
        <h4>⭐ Favourite Clients:</h4>
        <form id="favourites_bar">
    """
    
    for client in FAVOURITES:
        button_name = f"fav_{client['client_id']}"
        favourites_html += f"""
            <button name="{button_name}" type="action">
                {client['client_name']} ({client['client_id']})
            </button>
        """
    
    favourites_html += "</form>"
    return favourites_html

class ClientSearchActivity(CommandActivity):
    """Handles client searches - responds to 'find' keyword or any message in client-lookup room."""
    
    def __init__(self, messages):
        self._messages = messages
        super().__init__()
    
    def matches(self, context: CommandContext) -> bool:
        text = context.text_content.lower().strip()
        
        # Don't match slash commands (let the slash command decorators handle those)
        if text.startswith('/'):
            return False
        
        # Method 1: Messages starting with "find" in any room
        if text.startswith("find "):
            return True
        
        # Method 2: Simple "fav" command to show favourites
        if text == "fav":
            return True
        
        # Method 3: Any message in #client-lookup room (we'll need to check room name)
        # For now, let's use a simple approach - check if message looks like a search
        # (short message, no common conversational words)
        words = text.split()
        if len(words) <= 4 and not any(word in text for word in ['hello', 'hola', 'thanks', 'gracias', 'how', 'como', 'please', 'por', 'favor', 'fav']):
            # Looks like a search query, but make sure it's not a slash command
            if not text.startswith('@') and len(text) > 1:
                return True
        
        return False
    
    async def on_activity(self, context: CommandContext):
        print(f"ClientSearchActivity triggered by {context.initiator.user.display_name}")
        print(f"Search text: '{context.text_content}'")
        
        text = context.text_content.strip()
        
        # Check if this is the "fav" command
        if text.lower() == "fav":
            print("Showing favourites")
            favourites_message = create_favourites_bar()
            await self._messages.send_message(context.stream_id, favourites_message)
            return
        
        # Extract search query
        if text.lower().startswith("find "):
            query = text[5:]  # Remove "find " prefix
        else:
            query = text  # Assume entire message is the search query
        
        print(f"Search query: '{query}'")
        
        # Perform search
        matches = search_clients(query)
        print(f"Found {len(matches)} matches")
        
        # Generate unique request ID
        import time
        request_id = str(int(time.time()))
        
        # Create response with search results (no favourites embedded)
        if matches:
            response = create_client_selection_form(matches, request_id)
        else:
            # No matches found
            response = f"""<messageML>
                <div style="font-size: 10px; padding: 4px; border-radius: 2px;">
                    No matches for "{query}"
                </div>
            </messageML>"""
        
        await self._messages.send_message(context.stream_id, response)

class ClientSelectionFormActivity(FormReplyActivity):
    """Handles client selection from the form."""
    
    def __init__(self, messages):
        self._messages = messages
        super().__init__()
    
    def matches(self, context: FormReplyContext) -> bool:
        # Match forms for client selection or favourites
        return (context.form_id.startswith("client_selection_") or 
                context.form_id == "favourites_bar")
    
    async def on_activity(self, context: FormReplyContext):
        print(f"ClientSelectionFormActivity triggered by {context.initiator.user.display_name}")
        print(f"Form ID: {context.form_id}")
        print(f"Form values: {context.form_values}")
        
        # Extract client ID from form values
        selected_client_id = None
        
        # Check all form values for client selection
        for key, value in context.form_values.items():
            print(f"Checking form field: {key} = {value}")
            
            if key == "action" and value:
                # Symphony sends button name as the value of "action" field
                button_name = value
                if button_name.startswith("client_"):
                    selected_client_id = button_name[7:]  # Remove "client_" prefix
                elif button_name.startswith("fav_"):
                    selected_client_id = button_name[4:]  # Remove "fav_" prefix
                break
            elif key.startswith("client_") or key.startswith("fav_"):
                # Alternative: if button name is the key itself
                if key.startswith("client_"):
                    selected_client_id = key[7:]  # Remove "client_" prefix
                elif key.startswith("fav_"):
                    selected_client_id = key[4:]  # Remove "fav_" prefix
                break
        
        print(f"Extracted client ID: {selected_client_id}")
        
        # Get the correct stream ID for FormReplyContext
        stream_id = context.source_event.stream.stream_id
        
        if selected_client_id:
            # Find the selected client
            selected_client = None
            for client in CLIENTS:
                if client['client_id'] == selected_client_id:
                    selected_client = client
                    break
            
            if selected_client:
                favourite_star = "⭐ " if selected_client['is_favourite'] else ""
                
                # Send confirmation message first
                response = f"""<messageML>
                    <div style="font-size: 10px; padding: 6px; border-radius: 2px; border-left: 3px solid #28a745;">
                        <b style="font-size: 11px;">✅ {favourite_star}{selected_client['client_name']} - {selected_client['client_id']}</b><br/>
                    </div>
                </messageML>"""
                
                await self._messages.send_message(stream_id, response)
                
                # Fetch and display trades
                print(f"Fetching trades for client {selected_client_id}")
                trades = await get_client_trades(selected_client_id)
                
                if trades is not None:  # API call succeeded
                    trades_table = create_trades_table(trades, selected_client['client_name'])
                    trades_message = f"<messageML>{trades_table}</messageML>"
                    await self._messages.send_message(stream_id, trades_message)
                else:  # API call failed
                    error_message = f"""<messageML>
                        <div style="font-size: 10px; padding: 4px; border-radius: 2px; margin-top: 4px;">
                            <b>⚠️ Could not fetch trades for {selected_client['client_name']}</b><br/>
                            <i>Trades API may be unavailable</i>
                        </div>
                    </messageML>"""
                    await self._messages.send_message(stream_id, error_message)
                
                # Log the selection for trading workflow
                print(f"TRADE LOG: User {context.initiator.user.display_name} selected client {selected_client['client_name']} (ID: {selected_client_id})")
            else:
                await self._messages.send_message(
                    stream_id,
                    """<messageML>
                        <div style="font-size: 12px; padding: 8px; border-radius: 4px;">
                            <b>❌ Client not found</b><br/>
                            <i>Please try again</i>
                        </div>
                    </messageML>"""
                )
        else:
            await self._messages.send_message(
                stream_id,
                """<messageML>
                    <div style="font-size: 12px; padding: 8px; border-radius: 4px;">
                        <b>❌ No selection detected</b><br/>
                        <i>Please click a client button</i>
                    </div>
                </messageML>"""
            )

async def run():
    """Main function to configure and run the Client Lookup Bot."""
    print("Starting Client Lookup Bot for Traders...")
    
    # Load client data
    load_clients_from_csv("clients.csv")

    # Load configuration
    config = BdkConfigLoader.load_from_file(Path(__file__).parent.parent / "resources" / "config.yaml")

    async with SymphonyBdk(config) as bdk:
        activities = bdk.activities()
        
        # Register activities
        print("Registering ClientSearchActivity...")
        activities.register(ClientSearchActivity(bdk.messages()))
        
        print("Registering ClientSelectionFormActivity...")
        activities.register(ClientSelectionFormActivity(bdk.messages()))

        # Add helpful slash commands
        @activities.slash("/help", description="Show help for client lookup")
        async def help_command(context: CommandContext):
            help_text = f"""<messageML>
                <h2>📞 Client Lookup Bot - Help</h2>
                
                <h3>Quick Commands:</h3>
                <ul>
                    <li><b>find juan 123</b> - Search for clients matching "juan" and "123"</li>
                    <li><b>find maria</b> - Search for clients named Maria</li>
                    <li><b>find 456</b> - Search for clients with ID containing 456</li>
                    <li><b>fav</b> - Show favourite clients instantly</li>
                </ul>
                
                <h3>Features:</h3>
                <ul>
                    <li>⭐ Favourite clients pinned at top of chat</li>
                    <li>🔍 Searches both name and ID</li>
                    <li>⚡ Ultra-fast selection with buttons</li>
                    <li>📋 Use /favourites to refresh the pinned favourites</li>
                </ul>
                
                <p><b>Loaded:</b> {len(CLIENTS)} clients, {len(FAVOURITES)} favourites</p>
            </messageML>"""
            
            await bdk.messages().send_message(context.stream_id, help_text)

        @activities.slash("/favourites", description="Show/refresh favourite clients")
        async def favourites_command(context: CommandContext):
            """Send/refresh the favourites bar."""
            favourites_message = create_favourites_bar()
            await bdk.messages().send_message(context.stream_id, favourites_message)

        @activities.slash("/reload", description="Reload client data from CSV and refresh favourites")
        async def reload_command(context: CommandContext):
            """Reload CSV data and automatically show updated favourites."""
            print(f"Reload command triggered by {context.initiator.user.display_name}")
            
            success = load_clients_from_csv("clients.csv")
            
            if success:
                message = f"""<messageML>
                    <div style="font-size: 10px; padding: 6px; border-radius: 2px;">
                        <b>✅ Reloaded {len(CLIENTS)} clients, {len(FAVOURITES)} favourites from CSV</b>
                    </div>
                </messageML>"""
            else:
                message = f"""<messageML>
                    <div style="font-size: 10px; padding: 6px; border-radius: 2px;">
                        <b>⚠️ Using sample data: {len(CLIENTS)} clients, {len(FAVOURITES)} favourites</b>
                    </div>
                </messageML>"""
            
            await bdk.messages().send_message(context.stream_id, message)
            
            # Auto-refresh favourites after reload with small delay
            await asyncio.sleep(0.5)
            favourites_message = create_favourites_bar()
            await bdk.messages().send_message(context.stream_id, favourites_message)

        # Auto-send favourites on startup for any room the bot is active in
        print("Sending initial favourites message...")
        
        # Note: In a real implementation, you'd want to send this to specific rooms
        # For now, we'll let users trigger it with /favourites command

        # Start the datafeed loop
        datafeed_loop = bdk.datafeed()
        print("Starting datafeed...")
        print(f"Bot ready! Loaded {len(CLIENTS)} clients with {len(FAVOURITES)} favourites.")
        print("Usage: Type 'find client name' or 'find 12345' to search")
        await datafeed_loop.start()


if __name__ == "__main__":
    asyncio.run(run())