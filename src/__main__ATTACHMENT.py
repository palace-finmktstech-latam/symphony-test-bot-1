#!/usr/bin/env python3
"""
Working Attachment Downloader Bot with PDF Content Preview
Based on our exploration findings - uses direct event listener pattern
"""

import asyncio
import logging.config
from pathlib import Path
import os
import base64
import tempfile

from symphony.bdk.core.activity.command import CommandContext
from symphony.bdk.core.config.loader import BdkConfigLoader
from symphony.bdk.core.service.datafeed.real_time_event_listener import RealTimeEventListener
from symphony.bdk.core.symphony_bdk import SymphonyBdk
from symphony.bdk.gen.agent_model.v4_initiator import V4Initiator
from symphony.bdk.gen.agent_model.v4_message_sent import V4MessageSent

# PDF processing (you may need to install: pip install PyPDF2)
try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    print("⚠️  PyPDF2 not available. Install with: pip install PyPDF2")

# Text file processing
import io


class AttachmentDownloadListener(RealTimeEventListener):
    """Direct event listener that processes attachment messages."""
    
    def __init__(self, bdk):
        self.bdk = bdk
        self.download_path = r"C:\Users\bencl\OneDrive - palace.cl\Desktop"
        self.processed_messages = set()  # Avoid duplicate processing
        
    async def on_message_sent(self, initiator: V4Initiator, event: V4MessageSent):
        """Process every message and download attachments if found."""
        try:
            message = event.message
            
            # Skip if no attachments
            if not (hasattr(message, 'attachments') and message.attachments):
                return
            
            # Skip if already processed (avoid duplicates)
            message_id = message.message_id
            if message_id in self.processed_messages:
                return
            
            self.processed_messages.add(message_id)
            
            # Get basic info
            user_name = initiator.user.display_name
            stream_id = message.stream.stream_id
            
            print(f"\n📎 PROCESSING ATTACHMENT MESSAGE")
            print(f"   From: {user_name}")
            print(f"   Message ID: {message_id}")
            print(f"   Stream ID: {stream_id}")
            print(f"   Attachments: {len(message.attachments)}")
            
            # Process each attachment
            attachment_results = []
            for i, attachment in enumerate(message.attachments):
                print(f"\n   Processing attachment {i}...")
                
                # Access attachment properties correctly
                attachment_id = attachment.id
                file_name = attachment.name
                file_size = attachment.size
                
                print(f"      ID: {attachment_id}")
                print(f"      Name: {file_name}")
                print(f"      Size: {file_size} bytes")
                
                # Download the attachment
                download_result = await self._download_attachment(
                    stream_id, message_id, attachment_id, file_name
                )
                
                # Try to read file content for preview
                content_preview = await self._get_file_preview(file_name, attachment_id, stream_id, message_id)
                
                if content_preview:
                    attachment_results.append(f"📎 {file_name} ({file_size:,} bytes) - {download_result}<br/><b>Preview:</b><br/>{content_preview}")
                else:
                    attachment_results.append(f"📎 {file_name} ({file_size:,} bytes) - {download_result}")
                
            # Send response message
            if attachment_results:
                results_text = "<br/>".join(attachment_results)
                response = f"""<messageML>
                    <p>Hi {user_name}! I processed your attachments:</p>
                    <p>{results_text}</p>
                </messageML>"""
                
                await self.bdk.messages().send_message(stream_id, response)
            
        except Exception as e:
            print(f"❌ Error processing attachment message: {e}")
            import traceback
            traceback.print_exc()
            
            # Try to send error message
            try:
                await self.bdk.messages().send_message(
                    stream_id,
                    f"<messageML>Sorry, I encountered an error processing your attachment: {str(e)}</messageML>"
                )
            except:
                pass
    
    async def _download_attachment(self, stream_id, message_id, attachment_id, file_name):
        """Download an attachment and save it to the specified path."""
        try:
            print(f"      Downloading: {file_name}")
            print(f"      Stream ID: {stream_id}")
            print(f"      Message ID: {message_id}")
            print(f"      Attachment ID: {attachment_id}")
            
            # Get the attachment content using MessageService
            attachment_content = await self.bdk.messages().get_attachment(stream_id, message_id, attachment_id)
            
            print(f"      Retrieved content length: {len(attachment_content)}")
            
            # The content is returned as base64 encoded string, so we need to decode it
            file_data = base64.b64decode(attachment_content)
            
            print(f"      Decoded file size: {len(file_data)} bytes")
            
            # Create the full file path
            file_path = os.path.join(self.download_path, file_name)
            
            # Handle file name conflicts by adding a number suffix
            counter = 1
            original_file_path = file_path
            while os.path.exists(file_path):
                name, ext = os.path.splitext(original_file_path)
                file_path = f"{name}_{counter}{ext}"
                counter += 1
            
            # Write the file
            with open(file_path, 'wb') as f:
                f.write(file_data)
            
            print(f"      ✅ Saved to: {file_path}")
            return f"✅ Downloaded: {os.path.basename(file_path)}"
            
        except Exception as e:
            print(f"      ❌ Download failed: {e}")
            import traceback
            traceback.print_exc()
            return f"❌ Failed to download: {file_name} - {str(e)}"
    
    async def _get_file_preview(self, file_name, attachment_id, stream_id, message_id):
        """Get first 5 lines of file content for preview."""
        try:
            file_ext = os.path.splitext(file_name)[1].lower()
            
            if file_ext == '.pdf':
                return await self._get_pdf_preview(attachment_id, stream_id, message_id)
            elif file_ext in ['.txt', '.md', '.csv', '.log', '.json', '.xml', '.html', '.py', '.js', '.css']:
                return await self._get_text_preview(attachment_id, stream_id, message_id)
            else:
                return f"<i>Preview not available for {file_ext} files</i>"
                
        except Exception as e:
            print(f"      ⚠️  Preview failed: {e}")
            return f"<i>Preview error: {str(e)}</i>"
    
    async def _get_pdf_preview(self, attachment_id, stream_id, message_id):
        """Extract first 5 lines from PDF."""
        if not PDF_AVAILABLE:
            return "<i>PDF preview requires PyPDF2 (pip install PyPDF2)</i>"
        
        try:
            # Get the attachment content
            attachment_content = await self.bdk.messages().get_attachment(stream_id, message_id, attachment_id)
            file_data = base64.b64decode(attachment_content)
            
            # Create a temporary file to work with PyPDF2
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                temp_file.write(file_data)
                temp_file_path = temp_file.name
            
            try:
                # Read PDF content
                with open(temp_file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    
                    if len(pdf_reader.pages) == 0:
                        return "<i>PDF has no readable pages</i>"
                    
                    # Extract text from first page
                    first_page = pdf_reader.pages[0]
                    text = first_page.extract_text()
                    
                    if not text or text.strip() == "":
                        return "<i>PDF contains no extractable text</i>"
                    
                    # Get first 5 lines
                    lines = text.split('\n')
                    first_5_lines = []
                    line_count = 0
                    
                    for line in lines:
                        line = line.strip()
                        if line:  # Skip empty lines
                            first_5_lines.append(line)
                            line_count += 1
                            if line_count >= 5:
                                break
                    
                    if first_5_lines:
                        preview_text = "<br/>".join(first_5_lines)
                        return f"<code>{preview_text}</code>"
                    else:
                        return "<i>PDF contains no readable text lines</i>"
                        
            finally:
                # Clean up temp file
                try:
                    os.unlink(temp_file_path)
                except:
                    pass
                    
        except Exception as e:
            print(f"      ❌ PDF preview error: {e}")
            return f"<i>PDF preview error: {str(e)}</i>"
    
    async def _get_text_preview(self, attachment_id, stream_id, message_id):
        """Extract first 5 lines from text file."""
        try:
            # Get the attachment content
            attachment_content = await self.bdk.messages().get_attachment(stream_id, message_id, attachment_id)
            file_data = base64.b64decode(attachment_content)
            
            # Try to decode as text (try multiple encodings)
            text_content = None
            for encoding in ['utf-8', 'latin-1', 'cp1252', 'ascii']:
                try:
                    text_content = file_data.decode(encoding)
                    break
                except UnicodeDecodeError:
                    continue
            
            if text_content is None:
                return "<i>Could not decode text file</i>"
            
            # Get first 5 lines
            lines = text_content.split('\n')
            first_5_lines = []
            line_count = 0
            
            for line in lines:
                line = line.strip()
                if line:  # Skip empty lines
                    # Limit line length to avoid huge lines
                    if len(line) > 100:
                        line = line[:100] + "..."
                    first_5_lines.append(line)
                    line_count += 1
                    if line_count >= 5:
                        break
            
            if first_5_lines:
                preview_text = "<br/>".join(first_5_lines)
                return f"<code>{preview_text}</code>"
            else:
                return "<i>File contains no readable text lines</i>"
                
        except Exception as e:
            print(f"      ❌ Text preview error: {e}")
            return f"<i>Text preview error: {str(e)}</i>"


async def run():
    """Main bot function."""
    # Configure logging
    current_dir = Path(__file__).parent.parent
    logging_conf = Path.joinpath(current_dir, 'resources', 'logging.conf')
    logging.config.fileConfig(logging_conf, disable_existing_loggers=False)
    
    # Load configuration
    config = BdkConfigLoader.load_from_file(Path.joinpath(current_dir, 'resources', 'config.yaml'))

    async with SymphonyBdk(config) as bdk:
        # Set up datafeed with our attachment listener
        datafeed_loop = bdk.datafeed()
        attachment_listener = AttachmentDownloadListener(bdk)
        datafeed_loop.subscribe(attachment_listener)

        # Add some helper slash commands
        activities = bdk.activities()
        
        @activities.slash("/help")
        async def help_command(context: CommandContext):
            response = """<messageML>
                <h2>Attachment Download Bot with Preview</h2>
                <p>I automatically download file attachments and show content previews!</p>
                <ul>
                    <li><b>Send me a file attachment</b> - I'll download it and show the first 5 lines</li>
                    <li><b>Supported previews:</b> PDF, TXT, MD, CSV, LOG, JSON, XML, HTML, PY, JS, CSS</li>
                    <li><b>/help</b> - Show this message</li>
                    <li><b>/test</b> - Test if the bot is working</li>
                    <li><b>/download_path</b> - Show current download path</li>
                    <li><b>/stats</b> - Show download statistics</li>
                </ul>
                <p>Downloads are saved to: <code>C:\\Users\\bencl\\OneDrive - palace.cl\\Desktop</code></p>
                <p><i>Note: PDF preview requires PyPDF2 (pip install PyPDF2)</i></p>
            </messageML>"""
            await bdk.messages().send_message(context.stream_id, response)

        @activities.slash("/test")
        async def test_command(context: CommandContext):
            """Test command to verify bot is working."""
            user_name = context.initiator.user.display_name
            pdf_status = "✅ Available" if PDF_AVAILABLE else "❌ Not installed (pip install PyPDF2)"
            
            response = f"""<messageML>
                <p>Hello {user_name}! Bot is working.</p>
                <p><b>Features:</b></p>
                <ul>
                    <li>File download: ✅ Ready</li>
                    <li>PDF preview: {pdf_status}</li>
                    <li>Text preview: ✅ Ready</li>
                </ul>
                <p>Send me a file attachment to test downloads and previews!</p>
            </messageML>"""
            await bdk.messages().send_message(context.stream_id, response)

        @activities.slash("/download_path")
        async def download_path_command(context: CommandContext):
            """Show current download path."""
            download_path = attachment_listener.download_path
            
            # Check if the path exists
            path_exists = os.path.exists(download_path)
            path_status = "✅ Path exists" if path_exists else "❌ Path does not exist"
            
            response = f"""<messageML>
                <p><b>Current download path:</b></p>
                <p><code>{download_path}</code></p>
                <p>{path_status}</p>
            </messageML>"""
            
            await bdk.messages().send_message(context.stream_id, response)

        @activities.slash("/stats")
        async def stats_command(context: CommandContext):
            """Show download statistics."""
            processed_count = len(attachment_listener.processed_messages)
            
            response = f"""<messageML>
                <p><b>Download Statistics:</b></p>
                <p>Messages processed: {processed_count}</p>
                <p>Download path: <code>{attachment_listener.download_path}</code></p>
            </messageML>"""
            
            await bdk.messages().send_message(context.stream_id, response)

        print("🚀 Attachment Download Bot Started!")
        print(f"📁 Download path: {attachment_listener.download_path}")
        print("📎 Send file attachments to test automatic download")
        
        # Start the datafeed loop
        await datafeed_loop.start()


if __name__ == "__main__":
    try:
        logging.info("Starting Attachment Download Bot...")
        asyncio.run(run())
    except KeyboardInterrupt:
        logging.info("Stopping Attachment Download Bot")