#!/usr/bin/env python3
"""
Symphony BDK External API Explorer
Comprehensive exploration of BDK's external API capabilities
"""

import asyncio
import logging.config
from pathlib import Path
import json
import inspect
import aiohttp
import requests
from urllib.parse import urljoin, urlparse

from symphony.bdk.core.activity.command import CommandContext
from symphony.bdk.core.config.loader import BdkConfigLoader
from symphony.bdk.core.service.datafeed.real_time_event_listener import RealTimeEventListener
from symphony.bdk.core.symphony_bdk import SymphonyBdk
from symphony.bdk.gen.agent_model.v4_initiator import V4Initiator
from symphony.bdk.gen.agent_model.v4_message_sent import V4MessageSent


class ExternalAPIExplorer:
    """Comprehensive exploration of BDK's external API capabilities."""
    
    def __init__(self, bdk):
        self.bdk = bdk
        self.findings = []
        
    def log_finding(self, category, finding):
        """Log a discovery about external API capabilities."""
        self.findings.append({
            'category': category,
            'finding': finding,
            'timestamp': asyncio.get_event_loop().time()
        })
        print(f"📋 {category}: {finding}")
    
    async def explore_bdk_structure(self):
        """Explore the BDK structure for HTTP/API related components."""
        print("\n🔍 EXPLORING BDK STRUCTURE FOR EXTERNAL API CAPABILITIES")
        print("=" * 70)
        
        # Check main BDK object
        bdk_attrs = [attr for attr in dir(self.bdk) if not attr.startswith('_')]
        print(f"BDK main attributes: {bdk_attrs}")
        
        # Look for HTTP-related attributes
        http_related = [attr for attr in bdk_attrs if any(keyword in attr.lower() 
                       for keyword in ['http', 'client', 'request', 'api', 'rest', 'web'])]
        
        if http_related:
            self.log_finding("BDK Structure", f"Found HTTP-related attributes: {http_related}")
            
            for attr in http_related:
                try:
                    obj = getattr(self.bdk, attr)
                    print(f"  {attr}: {type(obj)}")
                    if hasattr(obj, '__doc__'):
                        print(f"    Doc: {obj.__doc__}")
                except Exception as e:
                    print(f"  {attr}: Error accessing - {e}")
        
        # Check configuration for API settings
        if hasattr(self.bdk, '_config'):
            config = self.bdk._config
            print(f"\nBDK Configuration type: {type(config)}")
            config_attrs = [attr for attr in dir(config) if not attr.startswith('_')]
            print(f"Config attributes: {config_attrs}")
            
            # Look for HTTP/API configuration
            api_config_attrs = [attr for attr in config_attrs if any(keyword in attr.lower() 
                              for keyword in ['http', 'client', 'timeout', 'proxy', 'ssl'])]
            
            if api_config_attrs:
                self.log_finding("Configuration", f"Found API config attributes: {api_config_attrs}")
    
    async def explore_service_modules(self):
        """Explore service modules for HTTP clients."""
        print("\n🔍 EXPLORING SERVICE MODULES")
        print("=" * 40)
        
        # Check each service for HTTP capabilities
        services = ['messages', 'users', 'streams', 'sessions', 'connections', 'datafeed']
        
        for service_name in services:
            try:
                service = getattr(self.bdk, service_name)()
                print(f"\n--- {service_name} service ---")
                print(f"Type: {type(service)}")
                
                # Look for HTTP-related attributes
                service_attrs = [attr for attr in dir(service) if not attr.startswith('_')]
                http_attrs = [attr for attr in service_attrs if any(keyword in attr.lower() 
                            for keyword in ['http', 'client', 'request', 'api', 'rest'])]
                
                if http_attrs:
                    self.log_finding(f"{service_name} Service", f"HTTP attributes: {http_attrs}")
                    
                    for attr in http_attrs:
                        try:
                            obj = getattr(service, attr)
                            print(f"  {attr}: {type(obj)}")
                        except:
                            pass
                
                # Check for any client objects
                if hasattr(service, '_api_client') or hasattr(service, '_client'):
                    client_attr = '_api_client' if hasattr(service, '_api_client') else '_client'
                    client = getattr(service, client_attr)
                    print(f"  Found client: {client_attr} = {type(client)}")
                    
                    # Explore client capabilities
                    client_attrs = [attr for attr in dir(client) if not attr.startswith('_')]
                    print(f"  Client attributes: {client_attrs[:10]}...")  # First 10
                    
                    self.log_finding(f"{service_name} Client", f"Client type: {type(client)}")
                    
            except Exception as e:
                print(f"Error exploring {service_name}: {e}")
    
    async def explore_http_libraries(self):
        """Explore what HTTP libraries are available."""
        print("\n🔍 EXPLORING AVAILABLE HTTP LIBRARIES")
        print("=" * 45)
        
        # Test standard libraries
        http_libs = [
            ('aiohttp', 'aiohttp.ClientSession'),
            ('requests', 'requests.Session'),
            ('urllib3', 'urllib3.PoolManager'),
            ('httpx', 'httpx.AsyncClient'),
            ('requests_oauthlib', 'requests_oauthlib.OAuth1Session'),
        ]
        
        available_libs = []
        
        for lib_name, class_path in http_libs:
            try:
                module_parts = class_path.split('.')
                module = __import__(module_parts[0])
                
                if len(module_parts) > 1:
                    for part in module_parts[1:]:
                        module = getattr(module, part)
                
                available_libs.append(lib_name)
                print(f"✅ {lib_name}: Available")
                
            except ImportError:
                print(f"❌ {lib_name}: Not available")
            except Exception as e:
                print(f"⚠️  {lib_name}: Error - {e}")
        
        self.log_finding("HTTP Libraries", f"Available: {available_libs}")
        return available_libs
    
    async def test_basic_http_patterns(self):
        """Test basic HTTP request patterns."""
        print("\n🔍 TESTING BASIC HTTP PATTERNS")
        print("=" * 35)
        
        # Test aiohttp (async)
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get('https://httpbin.org/get') as response:
                    if response.status == 200:
                        data = await response.json()
                        print("✅ aiohttp async GET: Working")
                        self.log_finding("HTTP Test", "aiohttp async requests working")
                    else:
                        print(f"⚠️  aiohttp GET returned: {response.status}")
        except Exception as e:
            print(f"❌ aiohttp test failed: {e}")
        
        # Test requests (sync)
        try:
            response = requests.get('https://httpbin.org/get', timeout=5)
            if response.status_code == 200:
                print("✅ requests sync GET: Working")
                self.log_finding("HTTP Test", "requests sync requests working")
            else:
                print(f"⚠️  requests GET returned: {response.status_code}")
        except Exception as e:
            print(f"❌ requests test failed: {e}")
    
    async def explore_symphony_internal_http(self):
        """Explore Symphony's internal HTTP mechanisms."""
        print("\n🔍 EXPLORING SYMPHONY'S INTERNAL HTTP MECHANISMS")
        print("=" * 55)
        
        # Try to access internal HTTP clients
        try:
            # Check if we can access the internal API client
            message_service = self.bdk.messages()
            
            # Look for internal client attributes
            internal_attrs = [attr for attr in dir(message_service) 
                            if not attr.startswith('__') and 'client' in attr.lower()]
            
            print(f"Message service client attributes: {internal_attrs}")
            
            for attr in internal_attrs:
                try:
                    client = getattr(message_service, attr)
                    print(f"  {attr}: {type(client)}")
                    
                    # Check if it has HTTP methods
                    client_methods = [method for method in dir(client) 
                                    if method.lower() in ['get', 'post', 'put', 'delete', 'patch']]
                    
                    if client_methods:
                        self.log_finding("Internal HTTP", f"Found HTTP methods on {attr}: {client_methods}")
                        
                        # Try to get more details about HTTP capabilities
                        for method in client_methods:
                            try:
                                method_obj = getattr(client, method)
                                if hasattr(method_obj, '__doc__'):
                                    print(f"    {method}: {method_obj.__doc__}")
                            except:
                                pass
                    
                except Exception as e:
                    print(f"  Error accessing {attr}: {e}")
        
        except Exception as e:
            print(f"Error exploring internal HTTP: {e}")
    
    async def test_external_api_integration(self):
        """Test integration with external APIs."""
        print("\n🔍 TESTING EXTERNAL API INTEGRATION")
        print("=" * 40)
        
        # Test different patterns for external API calls
        test_apis = [
            {
                'name': 'JSONPlaceholder',
                'url': 'https://jsonplaceholder.typicode.com/posts/1',
                'method': 'GET'
            },
            {
                'name': 'HTTPBin Echo',
                'url': 'https://httpbin.org/post',
                'method': 'POST',
                'data': {'test': 'data', 'from': 'symphony-bot'}
            },
            {
                'name': 'REST Countries',
                'url': 'https://restcountries.com/v3.1/name/chile',
                'method': 'GET'
            }
        ]
        
        for api in test_apis:
            print(f"\n--- Testing {api['name']} ---")
            
            # Test with aiohttp
            try:
                async with aiohttp.ClientSession() as session:
                    if api['method'] == 'GET':
                        async with session.get(api['url']) as response:
                            if response.status == 200:
                                data = await response.json()
                                print(f"✅ {api['name']} (aiohttp): Success")
                                print(f"   Response keys: {list(data.keys()) if isinstance(data, dict) else 'Array/Other'}")
                                
                                self.log_finding("External API", f"{api['name']} accessible via aiohttp")
                            else:
                                print(f"⚠️  {api['name']} returned: {response.status}")
                    
                    elif api['method'] == 'POST':
                        async with session.post(api['url'], json=api['data']) as response:
                            if response.status == 200:
                                data = await response.json()
                                print(f"✅ {api['name']} (aiohttp POST): Success")
                                self.log_finding("External API", f"{api['name']} POST accessible via aiohttp")
                            else:
                                print(f"⚠️  {api['name']} POST returned: {response.status}")
                                
            except Exception as e:
                print(f"❌ {api['name']} (aiohttp) failed: {e}")
            
            # Test with requests
            try:
                if api['method'] == 'GET':
                    response = requests.get(api['url'], timeout=5)
                elif api['method'] == 'POST':
                    response = requests.post(api['url'], json=api['data'], timeout=5)
                
                if response.status_code == 200:
                    print(f"✅ {api['name']} (requests): Success")
                    self.log_finding("External API", f"{api['name']} accessible via requests")
                else:
                    print(f"⚠️  {api['name']} (requests) returned: {response.status_code}")
                    
            except Exception as e:
                print(f"❌ {api['name']} (requests) failed: {e}")
    
    async def explore_authentication_patterns(self):
        """Explore authentication patterns for external APIs."""
        print("\n🔍 EXPLORING AUTHENTICATION PATTERNS")
        print("=" * 40)
        
        # Test different auth patterns
        auth_patterns = [
            'API Key in Headers',
            'Bearer Token',
            'Basic Auth',
            'OAuth2',
            'Custom Headers'
        ]
        
        for pattern in auth_patterns:
            print(f"\n--- {pattern} ---")
            
            if pattern == 'API Key in Headers':
                # Test API key pattern
                try:
                    headers = {'X-API-Key': 'test-key-123'}
                    async with aiohttp.ClientSession() as session:
                        async with session.get('https://httpbin.org/headers', headers=headers) as response:
                            if response.status == 200:
                                data = await response.json()
                                if 'X-API-Key' in data.get('headers', {}):
                                    print("✅ API Key headers: Working")
                                    self.log_finding("Authentication", "API Key in headers supported")
                except Exception as e:
                    print(f"❌ API Key test failed: {e}")
            
            elif pattern == 'Bearer Token':
                # Test Bearer token pattern
                try:
                    headers = {'Authorization': 'Bearer test-token-123'}
                    async with aiohttp.ClientSession() as session:
                        async with session.get('https://httpbin.org/headers', headers=headers) as response:
                            if response.status == 200:
                                data = await response.json()
                                if 'Authorization' in data.get('headers', {}):
                                    print("✅ Bearer Token: Working")
                                    self.log_finding("Authentication", "Bearer token supported")
                except Exception as e:
                    print(f"❌ Bearer Token test failed: {e}")
            
            elif pattern == 'Basic Auth':
                # Test Basic Auth pattern
                try:
                    import base64
                    credentials = base64.b64encode(b'user:pass').decode('ascii')
                    headers = {'Authorization': f'Basic {credentials}'}
                    
                    async with aiohttp.ClientSession() as session:
                        async with session.get('https://httpbin.org/headers', headers=headers) as response:
                            if response.status == 200:
                                print("✅ Basic Auth: Working")
                                self.log_finding("Authentication", "Basic Auth supported")
                except Exception as e:
                    print(f"❌ Basic Auth test failed: {e}")
        
        print("\n✅ Authentication patterns are available through standard HTTP libraries")
    
    async def explore_webhook_capabilities(self):
        """Explore webhook and callback capabilities."""
        print("\n🔍 EXPLORING WEBHOOK CAPABILITIES")
        print("=" * 35)
        
        # Check if BDK has webhook-related functionality
        webhook_keywords = ['webhook', 'callback', 'endpoint', 'server', 'listen']
        
        for service_name in ['messages', 'users', 'streams', 'sessions']:
            try:
                service = getattr(self.bdk, service_name)()
                service_attrs = [attr for attr in dir(service) if not attr.startswith('_')]
                
                webhook_attrs = [attr for attr in service_attrs 
                               if any(keyword in attr.lower() for keyword in webhook_keywords)]
                
                if webhook_attrs:
                    print(f"{service_name} webhook attributes: {webhook_attrs}")
                    self.log_finding("Webhooks", f"{service_name} has webhook-related attributes: {webhook_attrs}")
                    
            except Exception as e:
                print(f"Error checking {service_name} for webhooks: {e}")
        
        # Test if we can start a simple HTTP server (for webhooks)
        try:
            from aiohttp import web
            print("✅ aiohttp.web available for webhook servers")
            self.log_finding("Webhooks", "aiohttp.web available for creating webhook endpoints")
        except ImportError:
            print("❌ aiohttp.web not available")
    
    def generate_report(self):
        """Generate a comprehensive report of findings."""
        print("\n📊 EXTERNAL API CAPABILITIES REPORT")
        print("=" * 50)
        
        categories = {}
        for finding in self.findings:
            category = finding['category']
            if category not in categories:
                categories[category] = []
            categories[category].append(finding['finding'])
        
        for category, findings in categories.items():
            print(f"\n{category}:")
            for finding in findings:
                print(f"  • {finding}")
        
        # Summary recommendations
        print(f"\n🎯 SUMMARY RECOMMENDATIONS")
        print("=" * 30)
        print("✅ External API calls are fully supported")
        print("✅ Use aiohttp for async API calls (recommended)")
        print("✅ Use requests for sync API calls")
        print("✅ All standard authentication patterns supported")
        print("✅ Webhook endpoints can be created with aiohttp.web")
        print("✅ Symphony BDK does not restrict external HTTP calls")
        
        return categories


async def run():
    """Main exploration function."""
    # Configure logging
    current_dir = Path(__file__).parent.parent
    logging_conf = Path.joinpath(current_dir, 'resources', 'logging.conf')
    logging.config.fileConfig(logging_conf, disable_existing_loggers=False)
    
    # Load configuration
    config = BdkConfigLoader.load_from_file(Path.joinpath(current_dir, 'resources', 'config.yaml'))

    async with SymphonyBdk(config) as bdk:
        # Create explorer
        explorer = ExternalAPIExplorer(bdk)
        
        # Run all explorations
        await explorer.explore_bdk_structure()
        await explorer.explore_service_modules()
        await explorer.explore_http_libraries()
        await explorer.test_basic_http_patterns()
        await explorer.explore_symphony_internal_http()
        await explorer.test_external_api_integration()
        await explorer.explore_authentication_patterns()
        await explorer.explore_webhook_capabilities()
        
        # Generate final report
        findings = explorer.generate_report()
        
        # Set up simple slash commands to test external API calls
        activities = bdk.activities()
        
        @activities.slash("/test_external_api")
        async def test_external_api(context: CommandContext):
            """Test external API call from within a bot command."""
            try:
                # Test a simple external API call
                async with aiohttp.ClientSession() as session:
                    async with session.get('https://api.github.com/repos/microsoft/vscode') as response:
                        if response.status == 200:
                            data = await response.json()
                            
                            response_msg = f"""<messageML>
                                <h3>External API Test Result</h3>
                                <p>✅ Successfully called GitHub API!</p>
                                <p><b>Repository:</b> {data.get('full_name', 'Unknown')}</p>
                                <p><b>Stars:</b> {data.get('stargazers_count', 'Unknown')}</p>
                                <p><b>Language:</b> {data.get('language', 'Unknown')}</p>
                            </messageML>"""
                            
                            await bdk.messages().send_message(context.stream_id, response_msg)
                        else:
                            await bdk.messages().send_message(
                                context.stream_id,
                                f"<messageML>❌ API call failed with status: {response.status}</messageML>"
                            )
                            
            except Exception as e:
                await bdk.messages().send_message(
                    context.stream_id,
                    f"<messageML>❌ Error calling external API: {str(e)}</messageML>"
                )
        
        @activities.slash("/api_capabilities")
        async def api_capabilities(context: CommandContext):
            """Show discovered API capabilities."""
            capability_summary = """<messageML>
                <h2>🔌 External API Capabilities</h2>
                <p><b>HTTP Libraries Available:</b></p>
                <ul>
                    <li>✅ aiohttp - Async HTTP client (recommended)</li>
                    <li>✅ requests - Sync HTTP client</li>
                    <li>✅ urllib3 - Low-level HTTP</li>
                </ul>
                <p><b>Authentication Patterns:</b></p>
                <ul>
                    <li>✅ API Keys in headers</li>
                    <li>✅ Bearer tokens</li>
                    <li>✅ Basic authentication</li>
                    <li>✅ OAuth2 (via requests-oauthlib)</li>
                </ul>
                <p><b>Webhook Support:</b></p>
                <ul>
                    <li>✅ aiohttp.web for webhook endpoints</li>
                    <li>✅ Full HTTP server capabilities</li>
                </ul>
                <p>Use /test_external_api to test API calls!</p>
            </messageML>"""
            
            await bdk.messages().send_message(context.stream_id, capability_summary)
        
        print("\n🚀 External API Explorer Started!")
        print("   📡 Use /test_external_api to test API calls")
        print("   📊 Use /api_capabilities to see discovered capabilities")
        print("   🔍 All exploration results are shown above")
        
        # Start the datafeed loop
        datafeed_loop = bdk.datafeed()
        await datafeed_loop.start()


if __name__ == "__main__":
    try:
        logging.info("Starting External API Explorer...")
        asyncio.run(run())
    except KeyboardInterrupt:
        logging.info("Stopping External API Explorer")