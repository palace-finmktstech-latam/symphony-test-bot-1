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
        print("Cannot connect to trades API - is it running on port 8001?")
        return None
    except asyncio.TimeoutError:
        print("Trades API request timed out")
        return None
    except Exception as e:
        print(f"Error calling trades API: {e}")
        return None

async def get_client_status(client_id):
    """Fetch client status from the status API."""
    try:
        async with aiohttp.ClientSession() as session:
            url = f"{TRADES_API_BASE_URL}/status/{client_id}"
            print(f"Calling status API: {url}")
            
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    status = await response.json()
                    print(f"Retrieved status for client {client_id}: {status.get('status_line', 'Unknown')}")
                    return status
                elif response.status == 404:
                    print(f"No status found for client {client_id}")
                    return None
                else:
                    print(f"Status API returned status {response.status}")
                    return None
                    
    except aiohttp.ClientConnectorError:
        print("Cannot connect to status API - is it running on port 8001?")
        return None
    except asyncio.TimeoutError:
        print("Status API request timed out")
        return None
    except Exception as e:
        print(f"Error calling status API: {e}")
        return None

async def get_client_credit_lines(client_id):
    """Fetch client credit lines from the credit API."""
    try:
        async with aiohttp.ClientSession() as session:
            url = f"{TRADES_API_BASE_URL}/credit/{client_id}"
            print(f"Calling credit API: {url}")
            
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    credit = await response.json()
                    print(f"Retrieved credit lines for client {client_id}: {credit.get('credit_line', 'Unknown')}")
                    return credit
                elif response.status == 404:
                    print(f"No credit lines found for client {client_id}")
                    return None
                else:
                    print(f"Credit API returned status {response.status}")
                    return None
                    
    except aiohttp.ClientConnectorError:
        print("Cannot connect to credit API - is it running on port 8001?")
        return None
    except asyncio.TimeoutError:
        print("Credit API request timed out")
        return None
    except Exception as e:
        print(f"Error calling credit API: {e}")
        return None

def create_trades_table(trades, client_name):
    """Create compact trades table with link-style clickable trade numbers for document download."""
    if not trades:
        return f"""<div style="font-size: 10px; padding: 4px; border-radius: 2px; margin-top: 4px;">
            <b>📊 No trades found for {client_name}</b>
        </div>"""
    
    # Generate unique form ID
    import time
    form_id = f"trades_table_{int(time.time())}"
    
    # Create compact table with minimal download buttons
    table_html = f"""<div style="font-size: 9px; padding: 4px; border-radius: 2px; margin-top: 4px;">
        <b style="font-size: 10px;">📊 Last {len(trades)} trade(s) for {client_name}:</b><br/>
        <form id="{form_id}">
        <table style="width: 100%; font-size: 8px; border-collapse: collapse; margin-top: 2px;">
            <tr>
                <th style="padding: 1px 3px; border: 1px solid #dee2e6; font-size: 7px;">Trade#</th>
                <th style="padding: 1px 3px; border: 1px solid #dee2e6; font-size: 7px;">Date</th>
                <th style="padding: 1px 3px; border: 1px solid #dee2e6; font-size: 7px;">Product</th>
                <th style="padding: 1px 3px; border: 1px solid #dee2e6; font-size: 7px;">Dir</th>
                <th style="padding: 1px 3px; border: 1px solid #dee2e6; font-size: 7px;">Currency Pair</th>
                <th style="padding: 1px 3px; border: 1px solid #dee2e6; font-size: 7px;">Amount</th>
                <th style="padding: 1px 3px; border: 1px solid #dee2e6; font-size: 7px;">Price</th>
                <th style="padding: 1px 3px; border: 1px solid #dee2e6; font-size: 7px;">Spread</th>
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
        
        # Create minimal download button with just down arrow
        trade_number = trade.get('trade_number', 'N/A')
        download_button = f'<button name="trade_doc_{trade_number}" type="action">{trade_number}</button>'
        
        table_html += f"""
            <tr>
                <td style="padding: 1px 3px; border: 1px solid #dee2e6; font-size: 7px;">{download_button}</td>
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
        </form>
    </div>"""
    
    return table_html

class TradeDocumentActivity(FormReplyActivity):
    """Handles trade document download requests."""
    
    def __init__(self, messages):
        self._messages = messages
        super().__init__()
    
    def matches(self, context: FormReplyContext) -> bool:
        # Match forms with trade document requests
        return context.form_id.startswith("trades_table_")
    
    async def on_activity(self, context: FormReplyContext):
        print(f"TradeDocumentActivity triggered by {context.initiator.user.display_name}")
        print(f"Form ID: {context.form_id}")
        print(f"Form values: {context.form_values}")
        
        # Extract trade number from form values
        trade_number = None
        
        for key, value in context.form_values.items():
            print(f"Checking form field: {key} = {value}")
            
            if key == "action" and value and value.startswith("trade_doc_"):
                trade_number = value[10:]  # Remove "trade_doc_" prefix
                break
            elif key.startswith("trade_doc_"):
                trade_number = key[10:]  # Remove "trade_doc_" prefix
                break
        
        print(f"Extracted trade number: {trade_number}")
        
        # Get the correct stream ID
        stream_id = context.source_event.stream.stream_id
        
        # Get user's first name
        user_display_name = context.initiator.user.display_name
        user_first_name = user_display_name.split()[0] if user_display_name else "there"
        
        if trade_number:
            # Send acknowledgment message with personalized greeting
            ack_message = f"""<messageML>
                <div style="font-size: 10px; padding: 4px; border-radius: 2px; border-left: 3px solid #007bff;">
                    <b>📄 Fetching contract for trade {trade_number}, {user_first_name}...</b>
                </div>
            </messageML>"""
            await self._messages.send_message(stream_id, ack_message)
            
            # Download the trade document
            success = await self._download_and_send_trade_document(stream_id, trade_number, user_first_name)
            
            if not success:
                error_message = f"""<messageML>
                    <div style="font-size: 10px; padding: 4px; border-radius: 2px; border-left: 3px solid #dc3545;">
                        <b>❌ Sorry {user_first_name}, contract not found for trade {trade_number}</b><br/>
                        <i>The trade contract may not be available in our system</i>
                    </div>
                </messageML>"""
                await self._messages.send_message(stream_id, error_message)
        else:
            error_message = f"""<messageML>
                <div style="font-size: 10px; padding: 4px; border-radius: 2px;">
                    <b>❌ No trade number detected, {user_first_name}</b>
                </div>
            </messageML>"""
            await self._messages.send_message(stream_id, error_message)
    
    async def _download_and_send_trade_document(self, stream_id, trade_number, user_first_name):
        """Download trade document from API and send as attachment with personalized message."""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{TRADES_API_BASE_URL}/document/{trade_number}"
                print(f"Calling trade document API: {url}")
                
                async with session.get(url, timeout=30) as response:
                    if response.status == 200:
                        # Get the file content and filename from response
                        file_content = await response.read()
                        
                        # Try to get filename from Content-Disposition header
                        content_disposition = response.headers.get('content-disposition', '')
                        if 'filename=' in content_disposition:
                            filename = content_disposition.split('filename=')[1].strip('"')
                        else:
                            # Fallback to trade number with extension
                            filename = f"{trade_number}.pdf"
                        
                        print(f"Downloaded {len(file_content)} bytes for {filename}")
                        
                        # Create a temporary file-like object for the attachment
                        import io
                        file_obj = io.BytesIO(file_content)
                        file_obj.name = filename  # Set the filename attribute
                        
                        # Send personalized message with attachment
                        message_with_doc = f"""<messageML>
                            <div style="font-size: 10px; padding: 4px; border-radius: 2px; border-left: 3px solid #28a745;">
                                <b>Here you go {user_first_name}, here is the contract for trade number: {trade_number}</b><br/>
                                <i>File: {filename} ({len(file_content):,} bytes)</i>
                            </div>
                        </messageML>"""
                        
                        await self._messages.send_message(
                            stream_id, 
                            message_with_doc,
                            attachment=[file_obj]
                        )
                        
                        print(f"✅ Successfully sent contract {filename} for trade {trade_number} to {user_first_name}")
                        return True
                        
                    elif response.status == 404:
                        print(f"❌ Contract not found for trade {trade_number}")
                        return False
                    else:
                        print(f"❌ Document API returned status {response.status}")
                        return False
                        
        except aiohttp.ClientConnectorError:
            print("❌ Cannot connect to document API")
            return False
        except asyncio.TimeoutError:
            print("❌ Document API request timed out")
            return False
        except Exception as e:
            print(f"❌ Error downloading trade contract: {e}")
            return False

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
                
                # Fetch client status
                print(f"Fetching status for client {selected_client_id}")
                status = await get_client_status(selected_client_id)
                
                if status:
                    # Display status as traffic lights
                    status_message = f"""<messageML>
                        <div style="font-size: 10px; padding: 4px; border-radius: 2px; margin-top: 4px;">
                            <b>🚦 Client Status:</b><br/>
                            {status['status_line']}
                        </div>
                    </messageML>"""
                    await self._messages.send_message(stream_id, status_message)
                
                # Fetch client credit lines
                print(f"Fetching credit lines for client {selected_client_id}")
                credit = await get_client_credit_lines(selected_client_id)
                
                if credit:
                    # Display credit lines as traffic lights
                    credit_message = f"""<messageML>
                        <div style="font-size: 10px; padding: 4px; border-radius: 2px; margin-top: 4px;">
                            <b>💳 Credit Lines:</b><br/>
                            {credit['credit_line']}
                        </div>
                    </messageML>"""
                    await self._messages.send_message(stream_id, credit_message)
                
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
    print("Starting Enhanced Client Lookup Bot for Traders...")
    
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

        print("Registering TradeDocumentActivity...")
        activities.register(TradeDocumentActivity(bdk.messages()))

        # Add helpful slash commands
        @activities.slash("/help", description="Show help for client lookup")
        async def help_command(context: CommandContext):
            help_text = f"""<messageML>
                <h2>📞 Enhanced Client Lookup Bot - Help</h2>
                
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
                    <li>🚦 Client status with traffic lights</li>
                    <li>💳 Credit line utilization monitoring</li>
                    <li>📊 Last 5 trades history</li>
                    <li>📋 Use /favourites to refresh the pinned favourites</li>
                </ul>
                
                <p><b>Loaded:</b> {len(CLIENTS)} clients, {len(FAVOURITES)} favourites</p>
                <p><b>API Status:</b> Connected to {TRADES_API_BASE_URL}</p>
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

        @activities.slash("/api", description="Check API connectivity and status")
        async def api_command(context: CommandContext):
            """Check API connectivity and show status."""
            print(f"API check command triggered by {context.initiator.user.display_name}")
            
            try:
                async with aiohttp.ClientSession() as session:
                    url = f"{TRADES_API_BASE_URL}/health"
                    async with session.get(url, timeout=5) as response:
                        if response.status == 200:
                            health_data = await response.json()
                            api_message = f"""<messageML>
                                <div style="font-size: 10px; padding: 6px; border-radius: 2px;">
                                    <b>✅ API Status: Healthy</b><br/>
                                    📊 Trades: {health_data.get('total_trades', 'Unknown')}<br/>
                                    🚦 Statuses: {health_data.get('total_client_statuses', 'Unknown')}<br/>
                                    💳 Credit Lines: {health_data.get('total_credit_lines', 'Unknown')}<br/>
                                    🔗 URL: {TRADES_API_BASE_URL}
                                </div>
                            </messageML>"""
                        else:
                            api_message = f"""<messageML>
                                <div style="font-size: 10px; padding: 6px; border-radius: 2px;">
                                    <b>⚠️ API Status: Error {response.status}</b><br/>
                                    🔗 URL: {TRADES_API_BASE_URL}
                                </div>
                            </messageML>"""
            except Exception as e:
                api_message = f"""<messageML>
                    <div style="font-size: 10px; padding: 6px; border-radius: 2px;">
                        <b>❌ API Status: Unavailable</b><br/>
                        Error: {str(e)}<br/>
                        🔗 URL: {TRADES_API_BASE_URL}
                    </div>
                </messageML>"""
            
            await bdk.messages().send_message(context.stream_id, api_message)

        # Start the datafeed loop
        datafeed_loop = bdk.datafeed()
        print("Starting datafeed...")
        print(f"Bot ready! Loaded {len(CLIENTS)} clients with {len(FAVOURITES)} favourites.")
        print("Usage: Type 'find client name' or 'find 12345' to search")
        print(f"API: {TRADES_API_BASE_URL}")
        await datafeed_loop.start()


if __name__ == "__main__":
    asyncio.run(run())