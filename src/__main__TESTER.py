#!/usr/bin/env python3
import asyncio
import logging.config
from pathlib import Path
import random

from symphony.bdk.core.activity.command import CommandContext
from symphony.bdk.core.activity.command import CommandActivity
from symphony.bdk.core.config.loader import BdkConfigLoader
from symphony.bdk.core.service.datafeed.real_time_event_listener import RealTimeEventListener
from symphony.bdk.core.symphony_bdk import SymphonyBdk
from symphony.bdk.gen.agent_model.v4_initiator import V4Initiator
from symphony.bdk.gen.agent_model.v4_message_sent import V4MessageSent

from .activities import EchoCommandActivity, GreetUserJoinedActivity
from .gif_activities import GifSlashCommand, GifFormReplyActivity

# Configure logging
current_dir = Path(__file__).parent.parent
logging_conf = Path.joinpath(current_dir, 'resources', 'logging.conf')
logging.config.fileConfig(logging_conf, disable_existing_loggers=False)


async def run():
    config = BdkConfigLoader.load_from_file(Path.joinpath(current_dir, 'resources', 'config.yaml'))

    async with SymphonyBdk(config) as bdk:
        datafeed_loop = bdk.datafeed()
        datafeed_loop.subscribe(MessageListener())

        activities = bdk.activities()
        activities.register(EchoCommandActivity(bdk.messages()))
        activities.register(GreetUserJoinedActivity(bdk.messages(), bdk.users()))
        activities.register(GifSlashCommand(bdk.messages()))
        activities.register(GifFormReplyActivity(bdk.messages()))

        @activities.slash("/hello")
        async def hello(context: CommandContext):
            name = context.initiator.user.display_name
            response = f"<messageML>Hello {name}, hope you are doing well!</messageML>"
            await bdk.messages().send_message(context.stream_id, response)

        @activities.slash("/number")
        async def number(context: CommandContext):
            name = context.initiator.user.display_name
            random_number = random.randint(1, 100)
            response = f"<messageML>Hello {name}! I'm thinking of the number {random_number}. Hope you are doing well!</messageML>"
            await bdk.messages().send_message(context.stream_id, response)

        @activities.slash("/userinfo")
        async def user_info(context: CommandContext):
            # Get user service
            user_service = bdk.users()
            
            # Get information about the current user
            user_info = await user_service.get_user_by_id(context.initiator['user']['user_id'])
            
            await bdk.messages().send_message(
                context.stream_id,
                f"<messageML>User info: {user_info}</messageML>"
            )

        #@activities.slash("/explore {$cashtag_argument}")
        #@activities.slash("/explore")
        #async def explore(context: CommandActivity):
        #    @activities.slash("/explore_bdk")

        @activities.slash("/explore_bdk")
        async def explore_bdk(context: CommandContext):
            print("=== BDK INSTANCE EXPLORATION ===")
            print(f"BDK Object Type: {type(bdk)}")
            print(f"BDK Object Class: {bdk.__class__}")
            print(f"BDK Object Module: {bdk.__class__.__module__}")
            
            # Get all methods and attributes on the bdk instance
            bdk_attrs = [attr for attr in dir(bdk) if not attr.startswith('_')]
            print(f"\nBDK Instance Attributes/Methods: {bdk_attrs}")
            
            # Check specifically for activities
            if hasattr(bdk, 'activities'):
                print(f"\n✓ bdk.activities exists!")
                print(f"activities() type: {type(bdk.activities)}")
                
                # If it's callable, call it and see what we get
                if callable(bdk.activities):
                    activities_obj = bdk.activities()
                    print(f"activities() returns: {type(activities_obj)}")
                    print(f"activities() methods: {[attr for attr in dir(activities_obj) if not attr.startswith('_')]}")
            
            await bdk.messages().send_message(context.stream_id, "<messageML>BDK object exploration complete!</messageML>")

        @activities.slash("/explore_commandcontext")
        async def explore(context: CommandContext):
            explore_complete(context, "context")
            
            raw_message = context.source_event['message']['message']
            print(f"Raw message: {raw_message}")

            pure_text = context.text_content
            print(f"Pure text: {pure_text}")

            output = f"<messageML>Hello {context.initiator.user.first_name}! You just wrote the following: {pure_text}. Hope you are doing well!</messageML>"

            # Output: '<div data-format="PresentationML" data-version="2.0" class="wysiwyg"><p><span class="entity" data-entity-id="0">@Dev Cert Bot 3767</span> /explore</p></div>')


            #await bdk.messages().send_message(context.stream_id, "<messageML>You wrote the following: {pure_text}</messageML>")
            await bdk.messages().send_message(context.stream_id, output)

        import pprint

        def explore_complete(obj, name="object"):
            print(f"\n{'='*60}")
            print(f"COMPLETE EXPLORATION: {name.upper()}")
            print(f"{'='*60}")
            print(f"Type: {type(obj)}")
            
            all_attrs = [attr for attr in dir(obj) if not attr.startswith('_')]
            
            data_attrs = {}
            method_attrs = []
            error_attrs = {}
            
            for attr in all_attrs:
                try:
                    value = getattr(obj, attr)
                    if callable(value):
                        method_attrs.append(attr)
                    else:
                        data_attrs[attr] = value
                except Exception as e:
                    error_attrs[attr] = str(e)
            
            if data_attrs:
                print(f"\n--- DATA ATTRIBUTES ({len(data_attrs)}) ---")
                pprint.pprint(data_attrs, width=80, indent=2)
            
            if method_attrs:
                print(f"\n--- METHODS ({len(method_attrs)}) ---")
                pprint.pprint(method_attrs, width=80, indent=2)
            
            if error_attrs:
                print(f"\n--- INACCESSIBLE ATTRIBUTES ({len(error_attrs)}) ---")
                pprint.pprint(error_attrs, width=80, indent=2)


        
        #explore_object_deeply(context.initiator, "initiator") 
        #explore_object_deeply(context.initiator.user, "user")
            
        @activities.slash("/echo")
        async def echo(context: CommandContext):
            name = context.initiator.user.first_name
            print("Available attributes in context:")
            print(dir(context))
            
            print("\nAvailable attributes in context.initiator:")
            print(dir(context.initiator))

            #print(dir (help.context.initiator))
            
            print("\nAvailable attributes in context.initiator.user:")
            print(dir(context.initiator.user))
            #cashtag = context.arguments.get_cashtag("cashtag_argument")
            #message = f"Cashtag value: {cashtag.value}"

            #message = f"<messageML>Hello! You are thinking about buying {cashtag.value.value}. Am I right?</messageML>"
            message = f"<messageML>Hello {name}! You are thinking about buying stuff. Am I right? You said {messageSent}</messageML>"

            #await bdk.messages().send_message(context.stream_id, f"<messageML>{message}</messageML>")
            #await bdk.messages().send_message(context.stream_id, f"<messageML>Hi there, you want to buy {message}?</messageML>")
            await bdk.messages().send_message(context.stream_id, message)

        @activities.slash("/echo {$cashtag_argument}")

        async def on_echo_mention(context: CommandContext):
            # can also be retrieved with context.arguments.get("ticker").value
            ticker = context.arguments.get_cashtag("ticker").value 
            quantity = context.arguments.get_string("quantity")
            message = f"Buy ticker {ticker} with quantity {quantity}"
            # send confirmation back to user
            await messages.send_message(context.stream_id, f"{message}")


        #@activities.slash("/file")
        #async def file(context: CommandContext):
        #    with open(file_path, "rb") as file1:
        #        name = context.initiator.user.display_name
        #        file_path = r"C:\Users\bencl\OneDrive - palace.cl\Documents\Palace\Sales & Marketing\Client Brochure Jul 2023.pdf"
        #        message_text = "<messageML>Hello {name}! Here is the file you requested.</messageML>"
        #        message = Message(content=message_text, attachments=[file1])
        #        await bdk.messages().send_message(context.stream_id, message)

        # THIS IS A FUNCTION USED TO EXPLORE METHODS AND ATTRIBUTES OF OBJECTS

        def explore_method(obj, method_name, test_args=None):
            """
            Comprehensive method exploration framework
            """
            print(f"\n{'='*60}")
            print(f"EXPLORING: {method_name}")
            print(f"{'='*60}")
            
            if not hasattr(obj, method_name):
                print(f"❌ Method {method_name} does not exist")
                return
            
            method = getattr(obj, method_name)
            
            # Basic info
            print(f"Type: {type(method)}")
            print(f"Callable: {callable(method)}")
            
            # Documentation
            if hasattr(method, '__doc__') and method.__doc__:
                print(f"Documentation: {method.__doc__}")
            else:
                print("Documentation: None")
            
            # Signature analysis
            if callable(method):
                import inspect
                try:
                    sig = inspect.signature(method)
                    print(f"Signature: {method_name}{sig}")
                    
                    # Parameter details
                    if sig.parameters:
                        print("Parameters:")
                        for name, param in sig.parameters.items():
                            default = "no default" if param.default == inspect.Parameter.empty else f"default={param.default}"
                            annotation = param.annotation if param.annotation != inspect.Parameter.empty else "no type hint"
                            print(f"  - {name}: {annotation} ({default})")
                    else:
                        print("Parameters: None")
                        
                except Exception as e:
                    print(f"Could not get signature: {e}")
            
            # Try calling it
            if callable(method):
                print(f"\nTesting calls:")
                
                # Test 1: No arguments
                try:
                    result = method()
                    print(f"✅ No args: Success")
                    print(f"   Result type: {type(result)}")
                    print(f"   Result preview: {str(result)[:200]}{'...' if len(str(result)) > 200 else ''}")
                    return result
                except Exception as e:
                    print(f"❌ No args: {type(e).__name__}: {e}")
                
                # Test 2: With provided test arguments
                if test_args:
                    for i, args in enumerate(test_args):
                        try:
                            if isinstance(args, dict):
                                result = method(**args)
                                print(f"✅ Test {i+1} (kwargs): Success")
                            elif isinstance(args, (list, tuple)):
                                result = method(*args)
                                print(f"✅ Test {i+1} (args): Success")
                            else:
                                result = method(args)
                                print(f"✅ Test {i+1} (single arg): Success")
                            
                            print(f"   Result: {str(result)[:100]}{'...' if len(str(result)) > 100 else ''}")
                            return result
                        except Exception as e:
                            print(f"❌ Test {i+1}: {type(e).__name__}: {e}")
            
            else:
                # Try accessing as property
                try:
                    result = method
                    print(f"✅ Property access: Success")
                    print(f"   Value: {str(result)[:200]}{'...' if len(str(result)) > 200 else ''}")
                    return result
                except Exception as e:
                    print(f"❌ Property access: {e}")
            
            return None

        # THIS IS A FUNCTION USED TO EXPLORE METHODS AND ATTRIBUTES OF ASYNC OBJECTS

        async def explore_method_async(obj, method_name, context=None):
            """
            Enhanced exploration framework that handles async methods
            """
            print(f"\n{'='*60}")
            print(f"EXPLORING: {method_name}")
            print(f"{'='*60}")
            
            if not hasattr(obj, method_name):
                print(f"❌ Method {method_name} does not exist")
                return
            
            method = getattr(obj, method_name)
            
            # Basic info
            print(f"Type: {type(method)}")
            print(f"Callable: {callable(method)}")
            
            # Documentation
            if hasattr(method, '__doc__') and method.__doc__:
                print(f"Documentation: {method.__doc__}")
            else:
                print("Documentation: None")
            
            # Check if it's async
            import inspect
            is_async = inspect.iscoroutinefunction(method)
            print(f"Async method: {is_async}")
            
            # Signature analysis
            if callable(method):
                try:
                    sig = inspect.signature(method)
                    print(f"Signature: {method_name}{sig}")
                    
                    # Parameter details
                    if sig.parameters:
                        print("Parameters:")
                        for name, param in sig.parameters.items():
                            default = "no default" if param.default == inspect.Parameter.empty else f"default={param.default}"
                            annotation = param.annotation if param.annotation != inspect.Parameter.empty else "no type hint"
                            print(f"  - {name}: {annotation} ({default})")
                    else:
                        print("Parameters: None")
                        
                except Exception as e:
                    print(f"Could not get signature: {e}")
            
            # Try calling it
            if callable(method):
                print(f"\nTesting calls:")
                
                try:
                    if is_async:
                        print("Calling async method with await...")
                        result = await method()
                        print(f"✅ Async call: Success")
                    else:
                        print("Calling sync method...")
                        result = method()
                        print(f"✅ Sync call: Success")
                    
                    print(f"   Result type: {type(result)}")
                    print(f"   Result preview: {str(result)[:200]}{'...' if len(str(result)) > 200 else ''}")
                    return result
                    
                except Exception as e:
                    print(f"❌ Call failed: {type(e).__name__}: {e}")
            
            return None

        @activities.slash("/explore_async")
        async def explore_async(context: CommandContext):
            activities_registry = bdk.activities()
            result = await explore_method_async(activities_registry, "fetch_bot_info", context)
            
            await bdk.messages().send_message(
                context.stream_id, 
                "<messageML>Async exploration complete!</messageML>"
            )

        @activities.slash("/test_activity_list")
        async def test_activity_list(context: CommandContext):
            activities_registry = bdk.activities()
            
            # Explore activity_list method
            result = explore_method(activities_registry, "activity_list")
            
            # If we got a result, explore it further
            if result is not None:
                print(f"\n--- DETAILED RESULT ANALYSIS ---")
                if hasattr(result, '__len__'):
                    print(f"Collection length: {len(result)}")
                
                if hasattr(result, '__iter__') and len(result) > 0:
                    print("All items:")
                    #for i, item in enumerate(result[:3]):  # Show first 3 items
                    for i, item in enumerate(result[:len(result)]):
                        print(f"  [{i}]: {type(item)} - {item}")
            
            await bdk.messages().send_message(
                context.stream_id, 
                "<messageML>activity_list detailed exploration complete!</messageML>"
            )
        
        @activities.slash("/test_fetch_bot_info_async")
        async def test_fetch_bot_info_async(context: CommandContext):
            activities_registry = bdk.activities()
            
            print("=== EXPLORING fetch_bot_info (ASYNC) ===")
            print(f"Method type: {type(activities_registry.fetch_bot_info)}")
            print(f"Documentation: {activities_registry.fetch_bot_info.__doc__}")
            
            # Since it's async, we need to await it
            try:
                print("Calling fetch_bot_info() with await...")
                result = await activities_registry.fetch_bot_info()
                
                print(f"✅ Async call successful!")
                print(f"Result type: {type(result)}")
                print(f"Result value: {result}")
                
                # If it returns an object, explore its attributes
                if result is not None and hasattr(result, '__dict__'):
                    print("Bot info attributes:")
                    for key, value in result.__dict__.items():
                        print(f"  {key}: {value}")
                
                # Try common bot info attributes  
                if result is not None:
                    common_attrs = ['user_id', 'display_name', 'username', 'email', 'id', 'name']
                    print("Checking common bot attributes:")
                    for attr in common_attrs:
                        try:
                            value = getattr(result, attr, None)
                            if value is not None:
                                print(f"  ✓ {attr}: {value}")
                        except:
                            pass
                
            except Exception as e:
                print(f"❌ Async call failed: {type(e).__name__}: {e}")
            
            await bdk.messages().send_message(
                context.stream_id, 
                "<messageML>fetch_bot_info async exploration complete!</messageML>"
            )

        @activities.slash("/test_is_accepting_event_proper")
        async def test_is_accepting_event_proper(context: CommandContext):
            activities_registry = bdk.activities()
            
            print("=== TESTING is_accepting_event WITH PROPER ARGUMENTS ===")
            
            # First, let's try to get bot info from the BDK
            try:
                # Try to get bot info from sessions service
                session_service = bdk.sessions()
                bot_info = await session_service.get_session()
                print(f"✅ Got bot info from sessions: {type(bot_info)}")
                print(f"Bot info: {bot_info}")
                
            except Exception as e:
                print(f"❌ Could not get bot info from sessions: {e}")
                bot_info = None
            
            # Alternative: try to get it from users service
            if bot_info is None:
                try:
                    users_service = bdk.users()
                    # We know the bot user ID from context
                    bot_user_id = context.bot_user_id
                    bot_info = await users_service.get_user_by_id(bot_user_id)
                    print(f"✅ Got bot info from users service: {type(bot_info)}")
                except Exception as e:
                    print(f"❌ Could not get bot info from users service: {e}")
                    bot_info = None
            
            # Now test is_accepting_event if we have bot_info
            if bot_info is not None:
                print(f"\n--- Testing is_accepting_event ---")
                
                # Test with the current event
                try:
                    # We need to create a proper V4Event object from source_event
                    source_event = context.source_event
                    print(f"Source event type: {type(source_event)}")
                    
                    # Test with the source event (might need conversion)
                    result = await activities_registry.is_accepting_event(source_event, bot_info)
                    print(f"✅ is_accepting_event result: {result} (type: {type(result)})")
                    
                except Exception as e:
                    print(f"❌ is_accepting_event failed: {type(e).__name__}: {e}")
                    print(f"   This might be because source_event needs to be converted to V4Event format")
            
            else:
                print("❌ Could not get bot_info, cannot test is_accepting_event properly")
            
            await bdk.messages().send_message(
                context.stream_id, 
                "<messageML>is_accepting_event proper testing complete!</messageML>"
            )

        @activities.slash("/test_on_connection_accepted")
        async def test_on_connection_accepted(context: CommandContext):
            activities_registry = bdk.activities()
            
            print("=== EXPLORING on_connection_accepted ===")
            print(f"Method type: {type(activities_registry.on_connection_accepted)}")
            print(f"Documentation: {activities_registry.on_connection_accepted.__doc__}")
            
            # Check if it's async
            import inspect
            is_async = inspect.iscoroutinefunction(activities_registry.on_connection_accepted)
            print(f"Async method: {is_async}")
            
            # Get signature
            try:
                sig = inspect.signature(activities_registry.on_connection_accepted)
                print(f"Signature: on_connection_accepted{sig}")
                
                if sig.parameters:
                    print("Parameters:")
                    for name, param in sig.parameters.items():
                        default = "no default" if param.default == inspect.Parameter.empty else f"default={param.default}"
                        annotation = param.annotation if param.annotation != inspect.Parameter.empty else "no type hint"
                        print(f"  - {name}: {annotation} ({default})")
                else:
                    print("Parameters: None")
            except Exception as e:
                print(f"Could not get signature: {e}")
            
            # Test calling it - this looks like a decorator method
            print(f"\nTesting calls:")
            
            # Test 1: Call with no arguments (might be a decorator factory)
            try:
                print("--- Test: No arguments ---")
                result = activities_registry.on_connection_accepted()
                print(f"✅ Success: {result} (type: {type(result)})")
                
                # If it returns a decorator, try to see what it expects
                if callable(result):
                    print("  Returns a callable - likely a decorator")
                    decorator_sig = inspect.signature(result)
                    print(f"  Decorator signature: {decorator_sig}")
                    
            except Exception as e:
                print(f"❌ Failed: {type(e).__name__}: {e}")
            
            # Test 2: Try passing a function (if it's a decorator)
            try:
                print("\n--- Test: With a dummy function ---")
                
                def dummy_handler():
                    pass
                    
                result = activities_registry.on_connection_accepted(dummy_handler)
                print(f"✅ Success: {result} (type: {type(result)})")
                
            except Exception as e:
                print(f"❌ Failed: {type(e).__name__}: {e}")
            
            await bdk.messages().send_message(
                context.stream_id, 
                "<messageML>on_connection_accepted exploration complete!</messageML>"
            )

        @activities.slash("/explore_connection_decorator")
        async def explore_connection_decorator(context: CommandContext):
            activities_registry = bdk.activities()
            
            print("=== LOOKING FOR CONNECTION DECORATOR ===")
            
            # Check all methods that might be connection-related decorators
            connection_methods = [attr for attr in dir(activities_registry) if 'connection' in attr.lower()]
            print(f"Connection-related methods: {connection_methods}")
            
            # Check if there are any decorator-style methods
            decorator_candidates = []
            for attr_name in dir(activities_registry):
                if not attr_name.startswith('_'):
                    attr = getattr(activities_registry, attr_name)
                    if callable(attr):
                        try:
                            # Try calling with no args to see if it returns a decorator
                            result = attr()
                            if callable(result):
                                decorator_candidates.append(attr_name)
                                print(f"Potential decorator: {attr_name}")
                        except:
                            pass
            
            print(f"Decorator candidates: {decorator_candidates}")
            
            # Let's also check the register method since that might be how we register handlers
            if hasattr(activities_registry, 'register'):
                print(f"\n=== EXPLORING register method ===")
                register_method = activities_registry.register
                import inspect
                sig = inspect.signature(register_method)
                print(f"register signature: {sig}")
            
            await bdk.messages().send_message(
                context.stream_id, 
                "<messageML>Connection decorator exploration complete!</messageML>"
            )

        @activities.slash("/explore_decorator_pattern")
        async def explore_decorator_pattern(context: CommandContext):
            activities_registry = bdk.activities()
            
            print("=== UNDERSTANDING THE DECORATOR PATTERN ===")
            
            # Let's examine the slash decorator to understand the pattern
            slash_method = activities_registry.slash
            import inspect
            
            print(f"slash method type: {type(slash_method)}")
            sig = inspect.signature(slash_method)
            print(f"slash signature: {sig}")
            
            # Try calling slash with a command to see what it returns
            try:
                decorator = activities_registry.slash("/test_decorator")
                print(f"slash('/test_decorator') returns: {type(decorator)}")
                print(f"Is callable: {callable(decorator)}")
                
                if callable(decorator):
                    decorator_sig = inspect.signature(decorator)
                    print(f"Decorator signature: {decorator_sig}")
                    
            except Exception as e:
                print(f"Error testing slash decorator: {e}")
            
            # Now let's check if there are similar patterns for connections
            print(f"\n=== CHECKING FOR CONNECTION DECORATOR PATTERNS ===")
            
            # Check the source code pattern - look at how activities are typically structured
            print("From your existing activities, the pattern seems to be:")
            print("  @activities.slash('/command') - for slash commands")
            print("  @activities.on_instant_message_created() - for message events")
            print("  @activities.on_user_joined_room() - for user join events")
            
            # Check if these methods exist and are callable
            event_methods = [
                'on_instant_message_created',
                'on_user_joined_room', 
                'on_connection_accepted',
                'on_connection_requested'
            ]
            
            for method_name in event_methods:
                if hasattr(activities_registry, method_name):
                    method = getattr(activities_registry, method_name)
                    try:
                        # Try calling with no args to see if it's a decorator factory
                        result = method()
                        print(f"✅ {method_name}() returns: {type(result)} (likely a decorator)")
                    except Exception as e:
                        print(f"❌ {method_name}() failed: {e}")
            
            await bdk.messages().send_message(
                context.stream_id, 
                "<messageML>Decorator pattern exploration complete!</messageML>"
            )

        @activities.slash("/test_decorator_pattern_deep")
        async def test_decorator_pattern_deep(context: CommandContext):
            activities_registry = bdk.activities()
            
            print("=== DEEP DIVE INTO DECORATOR PATTERNS ===")
            
            # Test the working patterns we know
            print("Testing known working patterns:")
            
            # 1. slash decorator (we know this works)
            try:
                slash_decorator = activities_registry.slash("/temp_test")
                print(f"✅ slash('/temp_test'): {type(slash_decorator)}")
            except Exception as e:
                print(f"❌ slash decorator failed: {e}")
            
            # 2. on_user_joined_room returned a coroutine - let's await it
            try:
                result = await activities_registry.on_user_joined_room()
                print(f"✅ await on_user_joined_room(): {type(result)}")
                if callable(result):
                    import inspect
                    sig = inspect.signature(result)
                    print(f"   Decorator signature: {sig}")
            except Exception as e:
                print(f"❌ await on_user_joined_room() failed: {e}")
            
            # 3. Let's check what the pattern is by looking at the method signatures more carefully
            methods_to_check = [
                'on_instant_message_created',
                'on_message_sent', 
                'on_message_suppressed',
                'on_room_created',
                'on_room_updated',
                'on_symphony_elements_action',
                'on_connection_accepted',
                'on_connection_requested'
            ]
            
            print(f"\n=== ANALYZING ALL EVENT METHODS ===")
            import inspect
            
            for method_name in methods_to_check:
                if hasattr(activities_registry, method_name):
                    method = getattr(activities_registry, method_name)
                    sig = inspect.signature(method)
                    is_async = inspect.iscoroutinefunction(method)
                    
                    print(f"\n{method_name}:")
                    print(f"  Signature: {sig}")
                    print(f"  Async: {is_async}")
                    print(f"  Params: {len(sig.parameters)}")
                    
                    # The pattern seems to be:
                    # - Methods with 0 params = decorators that return decorators
                    # - Methods with 2+ params = internal handlers
                    
                    if len(sig.parameters) == 0:
                        print("  → Likely decorator factory (call with no args)")
                    elif len(sig.parameters) >= 2:
                        print("  → Likely internal handler (needs event params)")
            
            await bdk.messages().send_message(
                context.stream_id, 
                "<messageML>Deep decorator pattern analysis complete!</messageML>"
            )

        @activities.slash("/test_on_connection_requested")
        async def test_on_connection_requested(context: CommandContext):
            activities_registry = bdk.activities()
            
            print("=== EXPLORING on_connection_requested ===")
            print(f"Method type: {type(activities_registry.on_connection_requested)}")
            print(f"Documentation: {activities_registry.on_connection_requested.__doc__}")
            
            # Check if it's async
            import inspect
            is_async = inspect.iscoroutinefunction(activities_registry.on_connection_requested)
            print(f"Async method: {is_async}")
            
            # Get signature
            try:
                sig = inspect.signature(activities_registry.on_connection_requested)
                print(f"Signature: on_connection_requested{sig}")
                
                if sig.parameters:
                    print("Parameters:")
                    for name, param in sig.parameters.items():
                        default = "no default" if param.default == inspect.Parameter.empty else f"default={param.default}"
                        annotation = param.annotation if param.annotation != inspect.Parameter.empty else "no type hint"
                        print(f"  - {name}: {annotation} ({default})")
                else:
                    print("Parameters: None")
            except Exception as e:
                print(f"Could not get signature: {e}")
            
            # Test with missing arguments (we expect this to fail like the previous one)
            print(f"\nTesting calls:")
            try:
                print("--- Test: No arguments ---")
                result = await activities_registry.on_connection_requested()
                print(f"✅ Success: {result} (type: {type(result)})")
            except Exception as e:
                print(f"❌ Failed: {type(e).__name__}: {e}")
            
            await bdk.messages().send_message(
                context.stream_id, 
                "<messageML>on_connection_requested exploration complete!</messageML>"
            )

        @activities.slash("/test_on_instant_message_created")
        async def test_on_instant_message_created(context: CommandContext):
            activities_registry = bdk.activities()
            
            print("=== EXPLORING on_instant_message_created ===")
            
            # Get signature (we know the pattern now)
            import inspect
            sig = inspect.signature(activities_registry.on_instant_message_created)
            print(f"Signature: on_instant_message_created{sig}")
            
            print("✅ Follows expected pattern: initiator + event parameters")
            print("✅ Same unclear usage as other on_* methods")
            
            # Let's move to the more interesting method: register
            print(f"\n=== EXPLORING register (the key method!) ===")
            register_method = activities_registry.register
            register_sig = inspect.signature(register_method)
            print(f"register signature: {register_sig}")
            print(f"register documentation: {register_method.__doc__}")
            
            # This is likely where the magic happens!
            if register_sig.parameters:
                print("register parameters:")
                for name, param in register_sig.parameters.items():
                    default = "no default" if param.default == inspect.Parameter.empty else f"default={param.default}"
                    annotation = param.annotation if param.annotation != inspect.Parameter.empty else "no type hint"
                    print(f"  - {name}: {annotation} ({default})")
            
            await bdk.messages().send_message(
                context.stream_id, 
                "<messageML>Pattern confirmed and register method explored!</messageML>"
            )

        @activities.slash("/explore_register_system")
        async def explore_register_system(context: CommandContext):
            activities_registry = bdk.activities()
            
            print("=== UNDERSTANDING THE REGISTER SYSTEM ===")
            
            # First, let's see what AbstractActivity looks like
            from symphony.bdk.core.activity.api import AbstractActivity
            
            print(f"AbstractActivity type: {type(AbstractActivity)}")
            print(f"AbstractActivity methods: {[method for method in dir(AbstractActivity) if not method.startswith('_')]}")
            
            # Check what methods AbstractActivity has that match our on_* methods
            abstract_methods = [method for method in dir(AbstractActivity) if method.startswith('on_')]
            print(f"AbstractActivity on_* methods: {abstract_methods}")
            
            # Let's see if we can create a simple test activity
            print(f"\n=== CREATING TEST ACTIVITY ===")
            
            class TestActivity(AbstractActivity):
                def __init__(self):
                    pass
                    
                async def on_instant_message_created(self, initiator, event):
                    print(f"TEST ACTIVITY: Message from {initiator.user.display_name}")
                    return True  # or whatever it should return
            
            try:
                test_activity = TestActivity()
                print(f"✅ Created TestActivity: {type(test_activity)}")
                
                # Try to register it
                activities_registry.register(test_activity)
                print(f"✅ Successfully registered TestActivity!")
                
                # Check if it shows up in activity_list
                current_activities = activities_registry.activity_list
                print(f"Total activities now: {len(current_activities)}")
                print(f"Last activity: {current_activities[-1]}")
                
            except Exception as e:
                print(f"❌ Failed to create/register TestActivity: {e}")
            
            await bdk.messages().send_message(
                context.stream_id, 
                "<messageML>Register system exploration complete!</messageML>"
            )

        @activities.slash("/explore_abstract_activity")
        async def explore_abstract_activity(context: CommandContext):
            activities_registry = bdk.activities()
            
            print("=== UNDERSTANDING AbstractActivity REQUIREMENTS ===")
            
            from symphony.bdk.core.activity.api import AbstractActivity
            import inspect
            
            # Get detailed info about the abstract methods
            print("AbstractActivity abstract methods:")
            for method_name in ['matches', 'on_activity', 'before_matcher']:
                if hasattr(AbstractActivity, method_name):
                    method = getattr(AbstractActivity, method_name)
                    try:
                        sig = inspect.signature(method)
                        print(f"  {method_name}{sig}")
                        if hasattr(method, '__doc__') and method.__doc__:
                            print(f"    Doc: {method.__doc__}")
                    except Exception as e:
                        print(f"  {method_name}: Could not get signature - {e}")
            
            # Let's also look at existing activities to see how they're implemented
            print(f"\n=== EXAMINING EXISTING ACTIVITIES ===")
            current_activities = activities_registry.activity_list
            
            for i, activity in enumerate(current_activities[:3]):  # Look at first 3
                print(f"\nActivity {i}: {type(activity)}")
                activity_methods = [method for method in dir(activity) if not method.startswith('_')]
                print(f"  Methods: {activity_methods[:10]}...")  # First 10 methods
                
                # Check if it has the required abstract methods
                if hasattr(activity, 'matches'):
                    try:
                        matches_sig = inspect.signature(activity.matches)
                        print(f"  matches{matches_sig}")
                    except:
                        pass
                
                if hasattr(activity, 'on_activity'):
                    try:
                        on_activity_sig = inspect.signature(activity.on_activity)
                        print(f"  on_activity{on_activity_sig}")
                    except:
                        pass
            
            # Let's also check what imports we might need
            print(f"\n=== CHECKING SYMPHONY ACTIVITY IMPORTS ===")
            try:
                from symphony.bdk.core.activity import api
                activity_classes = [attr for attr in dir(api) if not attr.startswith('_')]
                print(f"Available in symphony.bdk.core.activity.api: {activity_classes}")
            except Exception as e:
                print(f"Error importing activity api: {e}")
            
            await bdk.messages().send_message(
                context.stream_id, 
                "<messageML>AbstractActivity requirements exploration complete!</messageML>"
            )

        @activities.slash("/find_activity_types")
        async def find_activity_types(context: CommandContext):
            print("=== DISCOVERING SYMPHONY ACTIVITY TYPES ===")
            
            # Let's explore what different activity modules are available
            import symphony.bdk.core.activity
            activity_modules = [attr for attr in dir(symphony.bdk.core.activity) if not attr.startswith('_')]
            print(f"Activity modules: {activity_modules}")
            
            # Check specific modules that might have ready-made activity classes
            modules_to_check = [
                'symphony.bdk.core.activity.command',
                'symphony.bdk.core.activity.user_joined_room', 
                'symphony.bdk.core.activity.form',
                'symphony.bdk.core.activity.parsing'
            ]
            
            for module_name in modules_to_check:
                try:
                    module = __import__(module_name, fromlist=[''])
                    classes = [attr for attr in dir(module) if not attr.startswith('_') and attr[0].isupper()]
                    print(f"\n{module_name}: {classes}")
                except Exception as e:
                    print(f"\n{module_name}: Error - {e}")
            
            # Let's also look at the parent classes of existing activities
            print(f"\n=== EXAMINING ACTIVITY INHERITANCE ===")
            activities_registry = bdk.activities()
            current_activities = activities_registry.activity_list
            
            for activity in current_activities[:5]:
                print(f"\n{type(activity).__name__}:")
                print(f"  MRO: {[cls.__name__ for cls in type(activity).__mro__]}")
                
                # Look for connection-related methods
                connection_methods = [method for method in dir(activity) if 'connection' in method.lower()]
                if connection_methods:
                    print(f"  Connection methods: {connection_methods}")
                
                # Look for all on_* methods
                on_methods = [method for method in dir(activity) if method.startswith('on_')]
                if on_methods:
                    print(f"  Event methods: {on_methods}")
            
            await bdk.messages().send_message(
                context.stream_id, 
                "<messageML>Activity types discovery complete!</messageML>"
            )

        @activities.slash("/find_connection_activities")
        async def find_connection_activities(context: CommandContext):
            print("=== SEARCHING FOR CONNECTION ACTIVITY CLASSES ===")
            
            # Based on the pattern, there should be connection-related modules
            # Let's check if there are more activity modules we haven't discovered
            
            import symphony.bdk.core
            print("Checking symphony.bdk.core for more modules...")
            core_modules = [attr for attr in dir(symphony.bdk.core) if not attr.startswith('_')]
            print(f"Core modules: {core_modules}")
            
            # Let's also check the parent BDK structure
            import symphony.bdk
            bdk_modules = [attr for attr in dir(symphony.bdk) if not attr.startswith('_')]
            print(f"BDK modules: {bdk_modules}")
            
            # The key insight: activities_registry methods we explored earlier
            # Let's see what CLASS the activities_registry actually is
            activities_registry = bdk.activities()
            print(f"\nactivities_registry type: {type(activities_registry)}")
            print(f"activities_registry class: {activities_registry.__class__}")
            print(f"activities_registry module: {activities_registry.__class__.__module__}")
            
            # NOW THE BIG QUESTION: Where do the on_* methods come from?
            registry_class = type(activities_registry)
            registry_on_methods = [method for method in dir(registry_class) if method.startswith('on_')]
            print(f"ActivityRegistry on_* methods: {registry_on_methods}")
            
            # Check the MRO of ActivityRegistry to see what it inherits from
            print(f"ActivityRegistry MRO: {[cls.__name__ for cls in registry_class.__mro__]}")
            
            # AHA! The on_* methods are probably on the ActivityRegistry itself
            # Let's check if ActivityRegistry IS the event listener
            for base_class in registry_class.__mro__:
                base_on_methods = [method for method in dir(base_class) if method.startswith('on_') and not method.startswith('on_activity')]
                if base_on_methods:
                    print(f"{base_class.__name__} has on_* methods: {base_on_methods}")
            
            await bdk.messages().send_message(
                context.stream_id, 
                "<messageML>Connection activities search complete!</messageML>"
            )

        @activities.slash("/understand_event_listener_pattern")
        async def understand_event_listener_pattern(context: CommandContext):
            print("=== UNDERSTANDING THE EVENT LISTENER PATTERN ===")
            
            # The ActivityRegistry inherits from RealTimeEventListener
            # This means we can override the on_* methods!
            
            activities_registry = bdk.activities()
            
            # Let's check if we can directly assign new methods to the registry
            print("Testing if we can override on_* methods...")
            
            # Save the original method
            original_on_connection_accepted = activities_registry.on_connection_accepted
            
            # Try to override it
            async def my_connection_handler(initiator, event):
                print(f"🎉 CUSTOM HANDLER: {initiator.user.display_name} accepted connection!")
                print(f"Event type: {type(event)}")
                return original_on_connection_accepted(initiator, event)
            
            try:
                # Method 1: Direct assignment
                activities_registry.on_connection_accepted = my_connection_handler
                print("✅ Successfully assigned custom handler!")
                
                # Test if it's actually there
                print(f"New handler type: {type(activities_registry.on_connection_accepted)}")
                
            except Exception as e:
                print(f"❌ Direct assignment failed: {e}")
            
            # Method 2: Check if there's a way to add event listeners
            listener_methods = [method for method in dir(activities_registry) if 'listener' in method.lower() or 'add' in method.lower() or 'register' in method.lower()]
            print(f"\nPossible listener registration methods: {listener_methods}")
            
            # Method 3: Subclass the ActivityRegistry?
            print(f"\n=== ALTERNATIVE: SUBCLASS APPROACH ===")
            print("Maybe you're supposed to subclass ActivityRegistry...")
            
            try:
                from symphony.bdk.core.activity.registry import ActivityRegistry
                
                class MyEventListener(ActivityRegistry):
                    async def on_connection_accepted(self, initiator, event):
                        print(f"🎉 SUBCLASS HANDLER: {initiator.user.display_name} accepted!")
                        await super().on_connection_accepted(initiator, event)
                
                print("✅ Successfully created ActivityRegistry subclass!")
                
            except Exception as e:
                print(f"❌ Subclass approach failed: {e}")
            
            await bdk.messages().send_message(
                context.stream_id, 
                "<messageML>Event listener pattern exploration complete!</messageML>"
            )

        @activities.slash("/explore_slash_decorator")
        async def explore_slash_decorator(context: CommandContext):
            activities_registry = bdk.activities()
            
            print("=== EXPLORING slash DECORATOR ===")
            
            import inspect
            slash_method = activities_registry.slash
            
            print(f"Method type: {type(slash_method)}")
            print(f"Documentation: {slash_method.__doc__}")
            
            # Get signature
            sig = inspect.signature(slash_method)
            print(f"Signature: slash{sig}")
            
            if sig.parameters:
                print("Parameters:")
                for name, param in sig.parameters.items():
                    default = "no default" if param.default == inspect.Parameter.empty else f"default={param.default}"
                    annotation = param.annotation if param.annotation != inspect.Parameter.empty else "no type hint"
                    print(f"  - {name}: {annotation} ({default})")
            
            # Test what it returns when called
            print(f"\nTesting slash decorator creation:")
            
            try:
                # Test with just command
                decorator1 = activities_registry.slash("/test")
                print(f"✅ slash('/test') returns: {type(decorator1)}")
                
                # Test with all parameters
                decorator2 = activities_registry.slash("/test2", mention_bot=False, description="Test command")
                print(f"✅ slash('/test2', mention_bot=False, description='...') returns: {type(decorator2)}")
                
                # Check the decorator signature
                decorator_sig = inspect.signature(decorator1)
                print(f"Decorator expects: {decorator_sig}")
                
                # Test what happens when we apply the decorator
                def dummy_function():
                    pass
                
                decorated_result = decorator1(dummy_function)
                print(f"Applying decorator to function returns: {type(decorated_result)}")
                
                # Check if it gets added to activity_list
                initial_count = len(activities_registry.activity_list)
                
                @activities_registry.slash("/temp_test_command")
                async def temp_command(ctx):
                    pass
                
                final_count = len(activities_registry.activity_list)
                print(f"Activity count before: {initial_count}, after: {final_count}")
                
                if final_count > initial_count:
                    print("✅ Decorator automatically registers activities!")
                    new_activity = activities_registry.activity_list[-1]
                    print(f"New activity type: {type(new_activity)}")
                
            except Exception as e:
                print(f"❌ Error testing slash decorator: {e}")
            
            await bdk.messages().send_message(
                context.stream_id, 
                "<messageML>slash decorator exploration complete!</messageML>"
            )

        @activities.slash("/test_on_message_sent")
        async def test_on_message_sent(context: CommandContext):
            activities_registry = bdk.activities()
            
            print("=== EXPLORING on_message_sent ===")
            print(f"Method type: {type(activities_registry.on_message_sent)}")
            print(f"Documentation: {activities_registry.on_message_sent.__doc__}")
            
            # Check if it's async
            import inspect
            is_async = inspect.iscoroutinefunction(activities_registry.on_message_sent)
            print(f"Async method: {is_async}")
            
            # Get signature
            try:
                sig = inspect.signature(activities_registry.on_message_sent)
                print(f"Signature: on_message_sent{sig}")
                
                if sig.parameters:
                    print("Parameters:")
                    for name, param in sig.parameters.items():
                        default = "no default" if param.default == inspect.Parameter.empty else f"default={param.default}"
                        annotation = param.annotation if param.annotation != inspect.Parameter.empty else "no type hint"
                        print(f"  - {name}: {annotation} ({default})")
                else:
                    print("Parameters: None")
            except Exception as e:
                print(f"Could not get signature: {e}")
            
            # Test with missing arguments (we expect this to fail like the other on_* methods)
            print(f"\nTesting calls:")
            try:
                print("--- Test: No arguments ---")
                if is_async:
                    result = await activities_registry.on_message_sent()
                else:
                    result = activities_registry.on_message_sent()
                print(f"✅ Success: {result} (type: {type(result)})")
            except Exception as e:
                print(f"❌ Failed: {type(e).__name__}: {e}")
            
            await bdk.messages().send_message(
                context.stream_id, 
                "<messageML>on_message_sent exploration complete!</messageML>"
            )

        @activities.slash("/test_on_message_suppressed_proper")
        async def test_on_message_suppressed_proper(context: CommandContext):
            activities_registry = bdk.activities()
            
            print("=== EXPLORING on_message_suppressed WITH PROPER ARGUMENTS ===")
            
            # First get the signature info we already know
            import inspect
            sig = inspect.signature(activities_registry.on_message_suppressed)
            print(f"Signature: on_message_suppressed{sig}")
            
            # Now try to test it with proper arguments similar to what we did with is_accepting_event
            try:
                # Get bot info
                session_service = bdk.sessions()
                bot_info = await session_service.get_session()
                print(f"✅ Got bot info: {type(bot_info)}")
                
                # We can't easily create a real V4MessageSuppressed event, but let's try with current event
                source_event = context.source_event
                print(f"Source event type: {type(source_event)}")
                
                # Try calling with the context's initiator and source event (even though types won't match)
                # This should give us more info about what the method expects/does
                try:
                    result = await activities_registry.on_message_suppressed(context.initiator, source_event)
                    print(f"✅ Method call succeeded: {result} (type: {type(result)})")
                except Exception as e:
                    print(f"❌ Method call failed: {type(e).__name__}: {e}")
                    print(f"   This tells us about type expectations or internal behavior")
                
            except Exception as e:
                print(f"❌ Could not get bot info: {e}")
            
            await bdk.messages().send_message(
                context.stream_id, 
                "<messageML>Proper on_message_suppressed testing complete!</messageML>"
            )

        @activities.slash("/test_on_room_created")
        async def test_on_room_created(context: CommandContext):
            activities_registry = bdk.activities()
            
            print("=== EXPLORING on_room_created ===")
            print(f"Method type: {type(activities_registry.on_room_created)}")
            print(f"Documentation: {activities_registry.on_room_created.__doc__}")
            
            # Get signature
            import inspect
            sig = inspect.signature(activities_registry.on_room_created)
            print(f"Signature: on_room_created{sig}")
            
            if sig.parameters:
                print("Parameters:")
                for name, param in sig.parameters.items():
                    default = "no default" if param.default == inspect.Parameter.empty else f"default={param.default}"
                    annotation = param.annotation if param.annotation != inspect.Parameter.empty else "no type hint"
                    print(f"  - {name}: {annotation} ({default})")
            
            # Test with proper arguments
            print(f"\nTesting with proper arguments:")
            try:
                # Try calling with context initiator and source event (wrong types but should return None)
                result = await activities_registry.on_room_created(context.initiator, context.source_event)
                print(f"✅ Method call succeeded: {result} (type: {type(result)})")
            except Exception as e:
                print(f"❌ Method call failed: {type(e).__name__}: {e}")
            
            await bdk.messages().send_message(
                context.stream_id, 
                "<messageML>on_room_created exploration complete!</messageML>"
            )

        @activities.slash("/test_on_room_deactivated")
        async def test_on_room_deactivated(context: CommandContext):
            activities_registry = bdk.activities()
            
            print("=== EXPLORING on_room_deactivated ===")
            print(f"Method type: {type(activities_registry.on_room_deactivated)}")
            print(f"Documentation: {activities_registry.on_room_deactivated.__doc__}")
            
            # Get signature
            import inspect
            sig = inspect.signature(activities_registry.on_room_deactivated)
            print(f"Signature: on_room_deactivated{sig}")
            
            if sig.parameters:
                print("Parameters:")
                for name, param in sig.parameters.items():
                    default = "no default" if param.default == inspect.Parameter.empty else f"default={param.default}"
                    annotation = param.annotation if param.annotation != inspect.Parameter.empty else "no type hint"
                    print(f"  - {name}: {annotation} ({default})")
            
            # Test with proper arguments
            print(f"\nTesting with proper arguments:")
            try:
                result = await activities_registry.on_room_deactivated(context.initiator, context.source_event)
                print(f"✅ Method call succeeded: {result} (type: {type(result)})")
            except Exception as e:
                print(f"❌ Method call failed: {type(e).__name__}: {e}")
            
            await bdk.messages().send_message(
                context.stream_id, 
                "<messageML>on_room_deactivated exploration complete!</messageML>"
            )

        @activities.slash("/test_on_room_demoted_from_owner")
        async def test_on_room_demoted_from_owner(context: CommandContext):
            activities_registry = bdk.activities()
            
            print("=== EXPLORING on_room_demoted_from_owner ===")
            print(f"Method type: {type(activities_registry.on_room_demoted_from_owner)}")
            print(f"Documentation: {activities_registry.on_room_demoted_from_owner.__doc__}")
            
            # Get signature
            import inspect
            sig = inspect.signature(activities_registry.on_room_demoted_from_owner)
            print(f"Signature: on_room_demoted_from_owner{sig}")
            
            if sig.parameters:
                print("Parameters:")
                for name, param in sig.parameters.items():
                    default = "no default" if param.default == inspect.Parameter.empty else f"default={param.default}"
                    annotation = param.annotation if param.annotation != inspect.Parameter.empty else "no type hint"
                    print(f"  - {name}: {annotation} ({default})")
            
            # Test with proper arguments
            print(f"\nTesting with proper arguments:")
            try:
                result = await activities_registry.on_room_demoted_from_owner(context.initiator, context.source_event)
                print(f"✅ Method call succeeded: {result} (type: {type(result)})")
            except Exception as e:
                print(f"❌ Method call failed: {type(e).__name__}: {e}")
            
            await bdk.messages().send_message(
                context.stream_id, 
                "<messageML>on_room_demoted_from_owner exploration complete!</messageML>"
            )

        @activities.slash("/test_on_room_member_promoted_to_owner")
        async def test_on_room_member_promoted_to_owner(context: CommandContext):
            activities_registry = bdk.activities()
            
            print("=== EXPLORING on_room_member_promoted_to_owner ===")
            print(f"Method type: {type(activities_registry.on_room_member_promoted_to_owner)}")
            print(f"Documentation: {activities_registry.on_room_member_promoted_to_owner.__doc__}")
            
            # Get signature
            import inspect
            sig = inspect.signature(activities_registry.on_room_member_promoted_to_owner)
            print(f"Signature: on_room_member_promoted_to_owner{sig}")
            
            if sig.parameters:
                print("Parameters:")
                for name, param in sig.parameters.items():
                    default = "no default" if param.default == inspect.Parameter.empty else f"default={param.default}"
                    annotation = param.annotation if param.annotation != inspect.Parameter.empty else "no type hint"
                    print(f"  - {name}: {annotation} ({default})")
            
            # Test with proper arguments
            print(f"\nTesting with proper arguments:")
            try:
                result = await activities_registry.on_room_member_promoted_to_owner(context.initiator, context.source_event)
                print(f"✅ Method call succeeded: {result} (type: {type(result)})")
            except Exception as e:
                print(f"❌ Method call failed: {type(e).__name__}: {e}")
            
            await bdk.messages().send_message(
                context.stream_id, 
                "<messageML>on_room_member_promoted_to_owner exploration complete!</messageML>"
            )

        @activities.slash("/test_on_room_reactivated")
        async def test_on_room_reactivated(context: CommandContext):
            activities_registry = bdk.activities()
            
            print("=== EXPLORING on_room_reactivated ===")
            print(f"Method type: {type(activities_registry.on_room_reactivated)}")
            print(f"Documentation: {activities_registry.on_room_reactivated.__doc__}")
            
            # Get signature
            import inspect
            sig = inspect.signature(activities_registry.on_room_reactivated)
            print(f"Signature: on_room_reactivated{sig}")
            
            if sig.parameters:
                print("Parameters:")
                for name, param in sig.parameters.items():
                    default = "no default" if param.default == inspect.Parameter.empty else f"default={param.default}"
                    annotation = param.annotation if param.annotation != inspect.Parameter.empty else "no type hint"
                    print(f"  - {name}: {annotation} ({default})")
            
            # Test with proper arguments
            print(f"\nTesting with proper arguments:")
            try:
                result = await activities_registry.on_room_reactivated(context.initiator, context.source_event)
                print(f"✅ Method call succeeded: {result} (type: {type(result)})")
            except Exception as e:
                print(f"❌ Method call failed: {type(e).__name__}: {e}")
            
            await bdk.messages().send_message(
                context.stream_id, 
                "<messageML>on_room_reactivated exploration complete!</messageML>"
            )

        @activities.slash("/test_on_room_updated")
        async def test_on_room_updated(context: CommandContext):
            activities_registry = bdk.activities()
            
            print("=== EXPLORING on_room_updated ===")
            print(f"Method type: {type(activities_registry.on_room_updated)}")
            print(f"Documentation: {activities_registry.on_room_updated.__doc__}")
            
            # Get signature
            import inspect
            sig = inspect.signature(activities_registry.on_room_updated)
            print(f"Signature: on_room_updated{sig}")
            
            if sig.parameters:
                print("Parameters:")
                for name, param in sig.parameters.items():
                    default = "no default" if param.default == inspect.Parameter.empty else f"default={param.default}"
                    annotation = param.annotation if param.annotation != inspect.Parameter.empty else "no type hint"
                    print(f"  - {name}: {annotation} ({default})")
            
            # Test with proper arguments
            print(f"\nTesting with proper arguments:")
            try:
                result = await activities_registry.on_room_updated(context.initiator, context.source_event)
                print(f"✅ Method call succeeded: {result} (type: {type(result)})")
            except Exception as e:
                print(f"❌ Method call failed: {type(e).__name__}: {e}")
            
            await bdk.messages().send_message(
                context.stream_id, 
                "<messageML>on_room_updated exploration complete!</messageML>"
            )

        @activities.slash("/test_on_shared_post")
        async def test_on_shared_post(context: CommandContext):
            activities_registry = bdk.activities()
            
            print("=== EXPLORING on_shared_post ===")
            print(f"Method type: {type(activities_registry.on_shared_post)}")
            print(f"Documentation: {activities_registry.on_shared_post.__doc__}")
            
            # Get signature
            import inspect
            sig = inspect.signature(activities_registry.on_shared_post)
            print(f"Signature: on_shared_post{sig}")
            
            if sig.parameters:
                print("Parameters:")
                for name, param in sig.parameters.items():
                    default = "no default" if param.default == inspect.Parameter.empty else f"default={param.default}"
                    annotation = param.annotation if param.annotation != inspect.Parameter.empty else "no type hint"
                    print(f"  - {name}: {annotation} ({default})")
            
            # Test with proper arguments
            print(f"\nTesting with proper arguments:")
            try:
                result = await activities_registry.on_shared_post(context.initiator, context.source_event)
                print(f"✅ Method call succeeded: {result} (type: {type(result)})")
            except Exception as e:
                print(f"❌ Method call failed: {type(e).__name__}: {e}")
            
            await bdk.messages().send_message(
                context.stream_id, 
                "<messageML>on_shared_post exploration complete!</messageML>"
            )

        @activities.slash("/test_on_symphony_elements_action")
        async def test_on_symphony_elements_action(context: CommandContext):
            activities_registry = bdk.activities()
            
            print("=== EXPLORING on_symphony_elements_action ===")
            print(f"Method type: {type(activities_registry.on_symphony_elements_action)}")
            print(f"Documentation: {activities_registry.on_symphony_elements_action.__doc__}")
            
            # Get signature
            import inspect
            sig = inspect.signature(activities_registry.on_symphony_elements_action)
            print(f"Signature: on_symphony_elements_action{sig}")
            
            if sig.parameters:
                print("Parameters:")
                for name, param in sig.parameters.items():
                    default = "no default" if param.default == inspect.Parameter.empty else f"default={param.default}"
                    annotation = param.annotation if param.annotation != inspect.Parameter.empty else "no type hint"
                    print(f"  - {name}: {annotation} ({default})")
            
            # Test with proper arguments
            print(f"\nTesting with proper arguments:")
            try:
                result = await activities_registry.on_symphony_elements_action(context.initiator, context.source_event)
                print(f"✅ Method call succeeded: {result} (type: {type(result)})")
            except Exception as e:
                print(f"❌ Method call failed: {type(e).__name__}: {e}")
            
            await bdk.messages().send_message(
                context.stream_id, 
                "<messageML>on_symphony_elements_action exploration complete!</messageML>"
            )

        @activities.slash("/test_on_user_joined_room")
        async def test_on_user_joined_room(context: CommandContext):
            activities_registry = bdk.activities()
            
            print("=== EXPLORING on_user_joined_room ===")
            print(f"Method type: {type(activities_registry.on_user_joined_room)}")
            print(f"Documentation: {activities_registry.on_user_joined_room.__doc__}")
            
            # Get signature
            import inspect
            sig = inspect.signature(activities_registry.on_user_joined_room)
            print(f"Signature: on_user_joined_room{sig}")
            
            if sig.parameters:
                print("Parameters:")
                for name, param in sig.parameters.items():
                    default = "no default" if param.default == inspect.Parameter.empty else f"default={param.default}"
                    annotation = param.annotation if param.annotation != inspect.Parameter.empty else "no type hint"
                    print(f"  - {name}: {annotation} ({default})")
            
            # Test with proper arguments
            print(f"\nTesting with proper arguments:")
            try:
                result = await activities_registry.on_user_joined_room(context.initiator, context.source_event)
                print(f"✅ Method call succeeded: {result} (type: {type(result)})")
            except Exception as e:
                print(f"❌ Method call failed: {type(e).__name__}: {e}")
            
            await bdk.messages().send_message(
                context.stream_id, 
                "<messageML>on_user_joined_room exploration complete!</messageML>"
            )

        @activities.slash("/test_on_user_left_room")
        async def test_on_user_left_room(context: CommandContext):
            activities_registry = bdk.activities()
            
            print("=== EXPLORING on_user_left_room ===")
            print(f"Method type: {type(activities_registry.on_user_left_room)}")
            print(f"Documentation: {activities_registry.on_user_left_room.__doc__}")
            
            # Get signature
            import inspect
            sig = inspect.signature(activities_registry.on_user_left_room)
            print(f"Signature: on_user_left_room{sig}")
            
            if sig.parameters:
                print("Parameters:")
                for name, param in sig.parameters.items():
                    default = "no default" if param.default == inspect.Parameter.empty else f"default={param.default}"
                    annotation = param.annotation if param.annotation != inspect.Parameter.empty else "no type hint"
                    print(f"  - {name}: {annotation} ({default})")
            
            # Test with proper arguments
            print(f"\nTesting with proper arguments:")
            try:
                result = await activities_registry.on_user_left_room(context.initiator, context.source_event)
                print(f"✅ Method call succeeded: {result} (type: {type(result)})")
            except Exception as e:
                print(f"❌ Method call failed: {type(e).__name__}: {e}")
            
            await bdk.messages().send_message(
                context.stream_id, 
                "<messageML>on_user_left_room exploration complete!</messageML>"
            )

        @activities.slash("/test_on_user_requested_to_join_room")
        async def test_on_user_requested_to_join_room(context: CommandContext):
            activities_registry = bdk.activities()
            
            print("=== EXPLORING on_user_requested_to_join_room ===")
            print(f"Method type: {type(activities_registry.on_user_requested_to_join_room)}")
            print(f"Documentation: {activities_registry.on_user_requested_to_join_room.__doc__}")
            
            # Get signature
            import inspect
            sig = inspect.signature(activities_registry.on_user_requested_to_join_room)
            print(f"Signature: on_user_requested_to_join_room{sig}")
            
            if sig.parameters:
                print("Parameters:")
                for name, param in sig.parameters.items():
                    default = "no default" if param.default == inspect.Parameter.empty else f"default={param.default}"
                    annotation = param.annotation if param.annotation != inspect.Parameter.empty else "no type hint"
                    print(f"  - {name}: {annotation} ({default})")
            
            # Test with proper arguments
            print(f"\nTesting with proper arguments:")
            try:
                result = await activities_registry.on_user_requested_to_join_room(context.initiator, context.source_event)
                print(f"✅ Method call succeeded: {result} (type: {type(result)})")
            except Exception as e:
                print(f"❌ Method call failed: {type(e).__name__}: {e}")
            
            await bdk.messages().send_message(
                context.stream_id, 
                "<messageML>on_user_requested_to_join_room exploration complete!</messageML>"
            )

        @activities.slash("/explore_services_detailed")
        async def explore_services_detailed(context: CommandContext):
            print("=== DETAILED SERVICE EXPLORATION ===")
            
            # Let's explore the actual service instances from our BDK
            services_to_test = [
                'messages', 'users', 'streams', 'sessions', 'connections', 
                'datafeed', 'presence', 'health', 'signals'
            ]
            
            for service_name in services_to_test:
                print(f"\n--- Exploring bdk.{service_name}() ---")
                try:
                    service_method = getattr(bdk, service_name)
                    service_instance = service_method()
                    
                    print(f"Service type: {type(service_instance)}")
                    print(f"Service class: {service_instance.__class__}")
                    print(f"Service module: {service_instance.__class__.__module__}")
                    
                    # Get public methods
                    methods = [attr for attr in dir(service_instance) if not attr.startswith('_')]
                    print(f"Methods ({len(methods)}): {methods[:10]}{'...' if len(methods) > 10 else ''}")
                    
                except Exception as e:
                    print(f"Error exploring {service_name}: {e}")
            
            # Let's also try to import service classes directly
            print(f"\n=== DIRECT SERVICE CLASS IMPORTS ===")
            direct_imports = [
                ('symphony.bdk.core.service.message.message_service', 'MessageService'),
                ('symphony.bdk.core.service.user.user_service', 'UserService'),
                ('symphony.bdk.core.service.stream.stream_service', 'StreamService'),
                ('symphony.bdk.core.service.session.session_service', 'SessionService'),
            ]
            
            for module_path, class_name in direct_imports:
                try:
                    module = __import__(module_path, fromlist=[class_name])
                    service_class = getattr(module, class_name)
                    print(f"✅ {class_name}: {service_class}")
                    
                    # Get methods from the class
                    methods = [attr for attr in dir(service_class) if not attr.startswith('_') and callable(getattr(service_class, attr, None))]
                    print(f"   Methods: {methods[:8]}{'...' if len(methods) > 8 else ''}")
                    
                except Exception as e:
                    print(f"❌ {class_name}: {e}")
            
            await bdk.messages().send_message(
                context.stream_id, 
                "<messageML>Detailed service exploration complete!</messageML>"
            )

        @activities.slash("/explore_command_classes_detailed")
        async def explore_command_classes_detailed(context: CommandContext):
            print("=== DETAILED COMMAND CLASS EXPLORATION ===")
            
            import symphony.bdk.core.activity.command as cmd
            import inspect
            
            # Let's explore each important class in detail
            classes_to_detail = [
                ('CommandActivity', cmd.CommandActivity),
                ('SlashCommandActivity', cmd.SlashCommandActivity), 
                ('CommandContext', cmd.CommandContext),
                ('Arguments', cmd.Arguments)
            ]
            
            for class_name, cls in classes_to_detail:
                print(f"\n{'='*50}")
                print(f"DETAILED: {class_name}")
                print(f"{'='*50}")
                
                # Get class documentation
                if cls.__doc__:
                    print(f"Documentation: {cls.__doc__}")
                else:
                    print("Documentation: None")
                
                # For abstract classes, show abstract methods
                if hasattr(cls, '__abstractmethods__'):
                    if cls.__abstractmethods__:
                        print(f"Abstract methods: {list(cls.__abstractmethods__)}")
                    else:
                        print("Abstract methods: None")
                
                # Get method signatures
                methods = [attr for attr in dir(cls) if not attr.startswith('_') and callable(getattr(cls, attr, None))]
                print(f"Methods: {methods}")
                
                # Try to get signatures for key methods
                key_methods = ['matches', 'on_activity', 'get', 'get_string'] if hasattr(cls, 'get') else ['matches', 'on_activity']
                for method_name in key_methods:
                    if hasattr(cls, method_name):
                        try:
                            method = getattr(cls, method_name)
                            sig = inspect.signature(method)
                            print(f"  {method_name}{sig}")
                        except Exception as e:
                            print(f"  {method_name}: Could not get signature - {e}")
            
            # Let's also check the current context we're using
            print(f"\n{'='*50}")
            print(f"CURRENT CONTEXT ANALYSIS")
            print(f"{'='*50}")
            print(f"Current context type: {type(context)}")
            print(f"Context attributes: {[attr for attr in dir(context) if not attr.startswith('_')]}")
            
            # Check if current context has arguments
            if hasattr(context, 'arguments') and context.arguments:
                print(f"Arguments available: {type(context.arguments)}")
                if hasattr(context.arguments, 'get_argument_names'):
                    try:
                        arg_names = context.arguments.get_argument_names()
                        print(f"Argument names: {arg_names}")
                    except Exception as e:
                        print(f"Error getting argument names: {e}")
            else:
                print("No arguments in current context")
            
            await bdk.messages().send_message(
                context.stream_id, 
                "<messageML>Detailed command class exploration complete!</messageML>"
            )

        @activities.slash("/explore_activity_user_joined_room")
        async def explore_activity_user_joined_room(context: CommandContext):
            print("=== EXPLORING symphony.bdk.core.activity.user_joined_room ===")
            
            # Import the user_joined_room module
            import symphony.bdk.core.activity.user_joined_room as ujr_module
            
            # Get all available items
            ujr_items = [attr for attr in dir(ujr_module) if not attr.startswith('_')]
            print(f"Available in user_joined_room module: {ujr_items}")
            
            # Separate classes from other items
            classes = []
            other_items = []
            
            for item_name in ujr_items:
                item = getattr(ujr_module, item_name)
                if isinstance(item, type):  # It's a class
                    classes.append(item_name)
                else:
                    other_items.append(item_name)
            
            print(f"\nClasses: {classes}")
            print(f"Other items: {other_items}")
            
            # Explore the main classes
            classes_to_explore = ['UserJoinedRoomActivity', 'UserJoinedRoomContext']
            
            for class_name in classes_to_explore:
                if class_name in ujr_items:
                    print(f"\n--- Exploring {class_name} ---")
                    cls = getattr(ujr_module, class_name)
                    print(f"Type: {type(cls)}")
                    print(f"Module: {cls.__module__}")
                    print(f"Documentation: {cls.__doc__}")
                    
                    # Get methods/attributes
                    methods = [attr for attr in dir(cls) if not attr.startswith('_')]
                    print(f"Methods/attributes: {methods}")
                    
                    # Check inheritance
                    if hasattr(cls, '__mro__'):
                        mro_names = [base.__name__ for base in cls.__mro__]
                        print(f"Inheritance chain: {mro_names}")
                else:
                    print(f"\n--- {class_name} not found ---")
            
            await bdk.messages().send_message(
                context.stream_id, 
                "<messageML>User joined room module exploration complete!</messageML>"
            )

        @activities.slash("/explore_activity_form")
        async def explore_activity_form(context: CommandContext):
            print("=== EXPLORING symphony.bdk.core.activity.form ===")
            
            # Import the form module
            import symphony.bdk.core.activity.form as form_module
            
            # Get all available items
            form_items = [attr for attr in dir(form_module) if not attr.startswith('_')]
            print(f"Available in form module: {form_items}")
            
            # Separate classes from other items
            classes = []
            other_items = []
            
            for item_name in form_items:
                item = getattr(form_module, item_name)
                if isinstance(item, type):  # It's a class
                    classes.append(item_name)
                else:
                    other_items.append(item_name)
            
            print(f"\nClasses: {classes}")
            print(f"Other items: {other_items}")
            
            # Explore the main classes
            classes_to_explore = ['FormReplyActivity', 'FormReplyContext']
            
            for class_name in classes_to_explore:
                if class_name in form_items:
                    print(f"\n--- Exploring {class_name} ---")
                    cls = getattr(form_module, class_name)
                    print(f"Type: {type(cls)}")
                    print(f"Module: {cls.__module__}")
                    print(f"Documentation: {cls.__doc__}")
                    
                    # Get methods/attributes
                    methods = [attr for attr in dir(cls) if not attr.startswith('_')]
                    print(f"Methods/attributes: {methods}")
                    
                    # Check inheritance
                    if hasattr(cls, '__mro__'):
                        mro_names = [base.__name__ for base in cls.__mro__]
                        print(f"Inheritance chain: {mro_names}")
                else:
                    print(f"\n--- {class_name} not found ---")
            
            await bdk.messages().send_message(
                context.stream_id, 
                "<messageML>Form module exploration complete!</messageML>"
            )

        @activities.slash("/explore_activity_api")
        async def explore_activity_api(context: CommandContext):
            print("=== EXPLORING symphony.bdk.core.activity.api ===")
            
            # Import the api module
            import symphony.bdk.core.activity.api as api_module
            
            # Get all available items
            api_items = [attr for attr in dir(api_module) if not attr.startswith('_')]
            print(f"Available in api module: {api_items}")
            
            # Separate classes from other items
            classes = []
            other_items = []
            
            for item_name in api_items:
                item = getattr(api_module, item_name)
                if isinstance(item, type):  # It's a class
                    classes.append(item_name)
                else:
                    other_items.append(item_name)
            
            print(f"\nClasses: {classes}")
            print(f"Other items: {other_items}")
            
            # Explore the main classes
            classes_to_explore = ['AbstractActivity', 'ActivityContext']
            
            for class_name in classes_to_explore:
                if class_name in api_items:
                    print(f"\n--- Exploring {class_name} ---")
                    cls = getattr(api_module, class_name)
                    print(f"Type: {type(cls)}")
                    print(f"Module: {cls.__module__}")
                    print(f"Documentation: {cls.__doc__}")
                    
                    # Get methods/attributes
                    methods = [attr for attr in dir(cls) if not attr.startswith('_')]
                    print(f"Methods/attributes: {methods}")
                    
                    # Check inheritance
                    if hasattr(cls, '__mro__'):
                        mro_names = [base.__name__ for base in cls.__mro__]
                        print(f"Inheritance chain: {mro_names}")
                        
                    # For abstract classes, check abstract methods
                    if hasattr(cls, '__abstractmethods__'):
                        if cls.__abstractmethods__:
                            print(f"Abstract methods: {list(cls.__abstractmethods__)}")
                        else:
                            print("Abstract methods: None")
                else:
                    print(f"\n--- {class_name} not found ---")
            
            await bdk.messages().send_message(
                context.stream_id, 
                "<messageML>API module exploration complete!</messageML>"
            )

        @activities.slash("/explore_activity_parsing")
        async def explore_activity_parsing(context: CommandContext):
            print("=== EXPLORING symphony.bdk.core.activity.parsing ===")
            
            # Import the parsing module
            import symphony.bdk.core.activity.parsing as parsing_module
            
            # Get all available items
            parsing_items = [attr for attr in dir(parsing_module) if not attr.startswith('_')]
            print(f"Available in parsing module: {parsing_items}")
            
            # Separate classes from other items
            classes = []
            functions = []
            other_items = []
            
            for item_name in parsing_items:
                item = getattr(parsing_module, item_name)
                if isinstance(item, type):  # It's a class
                    classes.append(item_name)
                elif callable(item):  # It's a function
                    functions.append(item_name)
                else:
                    other_items.append(item_name)
            
            print(f"\nClasses: {classes}")
            print(f"Functions: {functions}")
            print(f"Other items: {other_items}")
            
            # Explore classes
            for class_name in classes:
                print(f"\n--- Exploring {class_name} ---")
                cls = getattr(parsing_module, class_name)
                print(f"Type: {type(cls)}")
                print(f"Module: {cls.__module__}")
                print(f"Documentation: {cls.__doc__}")
                
                # Get methods/attributes
                methods = [attr for attr in dir(cls) if not attr.startswith('_')]
                print(f"Methods/attributes: {methods}")
                
                # Check inheritance
                if hasattr(cls, '__mro__'):
                    mro_names = [base.__name__ for base in cls.__mro__]
                    print(f"Inheritance chain: {mro_names}")
            
            # Explore functions
            import inspect
            for func_name in functions:
                print(f"\n--- Exploring function {func_name} ---")
                func = getattr(parsing_module, func_name)
                print(f"Documentation: {func.__doc__}")
                
                try:
                    sig = inspect.signature(func)
                    print(f"Signature: {func_name}{sig}")
                except Exception as e:
                    print(f"Could not get signature: {e}")
            
            await bdk.messages().send_message(
                context.stream_id, 
                "<messageML>Parsing module exploration complete!</messageML>"
            )

        @activities.slash("/explore_parsing_submodules")
        async def explore_parsing_submodules(context: CommandContext):
            print("=== EXPLORING PARSING SUBMODULES ===")
            
            # List of parsing submodules to explore
            submodules = [
                'symphony.bdk.core.activity.parsing.arguments',
                'symphony.bdk.core.activity.parsing.command_token', 
                'symphony.bdk.core.activity.parsing.input_tokenizer',
                'symphony.bdk.core.activity.parsing.match_result',
                'symphony.bdk.core.activity.parsing.message_entities',
                'symphony.bdk.core.activity.parsing.slash_command_pattern'
            ]
            
            for module_path in submodules:
                try:
                    print(f"\n{'='*60}")
                    print(f"EXPLORING: {module_path}")
                    print(f"{'='*60}")
                    
                    # Import the submodule
                    module = __import__(module_path, fromlist=[''])
                    
                    # Get all items in the submodule
                    items = [attr for attr in dir(module) if not attr.startswith('_')]
                    print(f"Available items: {items}")
                    
                    # Categorize items
                    classes = []
                    functions = []
                    other_items = []
                    
                    for item_name in items:
                        item = getattr(module, item_name)
                        if isinstance(item, type):
                            classes.append(item_name)
                        elif callable(item):
                            functions.append(item_name)
                        else:
                            other_items.append(item_name)
                    
                    print(f"Classes: {classes}")
                    print(f"Functions: {functions}")
                    print(f"Other items: {other_items}")
                    
                    # Explore main classes
                    for class_name in classes[:3]:  # First 3 to avoid too much output
                        cls = getattr(module, class_name)
                        print(f"\n  {class_name}:")
                        print(f"    Type: {type(cls)}")
                        print(f"    Doc: {cls.__doc__}")
                        methods = [attr for attr in dir(cls) if not attr.startswith('_')]
                        print(f"    Methods: {methods[:8]}{'...' if len(methods) > 8 else ''}")
                        
                except Exception as e:
                    print(f"❌ Error exploring {module_path}: {e}")
            
            await bdk.messages().send_message(
                context.stream_id, 
                "<messageML>Parsing submodules exploration complete!</messageML>"
            )

        @activities.slash("/explore_activity_exception")
        async def explore_activity_exception(context: CommandContext):
            print("=== EXPLORING symphony.bdk.core.activity.exception ===")
            
            # Import the exception module
            import symphony.bdk.core.activity.exception as exception_module
            
            # Get all available items
            exception_items = [attr for attr in dir(exception_module) if not attr.startswith('_')]
            print(f"Available in exception module: {exception_items}")
            
            # Separate classes from other items
            exception_classes = []
            other_items = []
            
            for item_name in exception_items:
                item = getattr(exception_module, item_name)
                if isinstance(item, type):  # It's a class
                    exception_classes.append(item_name)
                else:
                    other_items.append(item_name)
            
            print(f"\nException classes: {exception_classes}")
            print(f"Other items: {other_items}")
            
            # Explore each exception class
            for exception_name in exception_classes:
                print(f"\n--- Exploring {exception_name} ---")
                exc_class = getattr(exception_module, exception_name)
                print(f"Type: {type(exc_class)}")
                print(f"Module: {exc_class.__module__}")
                print(f"Documentation: {exc_class.__doc__}")
                
                # Get methods/attributes
                methods = [attr for attr in dir(exc_class) if not attr.startswith('_')]
                print(f"Methods/attributes: {methods}")
                
                # Check inheritance (what base exception it extends)
                if hasattr(exc_class, '__mro__'):
                    mro_names = [base.__name__ for base in exc_class.__mro__]
                    print(f"Inheritance chain: {mro_names}")
                    
                # Check if it's actually an exception
                if issubclass(exc_class, Exception):
                    print(f"✅ Is a proper Exception subclass")
                else:
                    print(f"❌ Not an Exception subclass")
            
            await bdk.messages().send_message(
                context.stream_id, 
                "<messageML>Exception module exploration complete!</messageML>"
            )

        @activities.slash("/explore_attachments")
        async def explore_attachments(context: CommandContext):
            print("=== EXPLORING ATTACHMENT CAPABILITIES ===")
            
            # Let's check what attachment methods are available on the message service
            message_service = bdk.messages()
            attachment_methods = [method for method in dir(message_service) if 'attachment' in method.lower()]
            print(f"Message service attachment methods: {attachment_methods}")
            
            # Let's also check what's in the context when we receive messages
            print(f"\nContext attributes: {[attr for attr in dir(context) if not attr.startswith('_')]}")
            
            # Check the source event for attachment info
            source_event = context.source_event
            print(f"Source event type: {type(source_event)}")
            print(f"Source event attributes: {[attr for attr in dir(source_event) if not attr.startswith('_')]}")
            
            # Check if the message has attachments
            if hasattr(source_event, 'message'):
                message = source_event.message
                print(f"Message attributes: {[attr for attr in dir(message) if not attr.startswith('_')]}")
                
                # Look for attachment-related fields
                if hasattr(message, 'attachments'):
                    print(f"Message has attachments field: {message.attachments}")
                if hasattr(message, 'data'):
                    print(f"Message data: {message.data}")
            
            await bdk.messages().send_message(
                context.stream_id,
                "<messageML>Attachment exploration complete! Check console for details.</messageML>"
            )

        @activities.slash("/explore_message_service_complete")
        async def explore_message_service_complete(context: CommandContext):
            print("=== COMPLETE MESSAGE SERVICE EXPLORATION ===")
            
            # Import the message service module
            import symphony.bdk.core.service.message as message_module
            
            # Get all items in the message module
            message_items = [attr for attr in dir(message_module) if not attr.startswith('_')]
            print(f"Available in message module: {message_items}")
            
            # Separate classes from other items
            classes = []
            other_items = []
            
            for item_name in message_items:
                item = getattr(message_module, item_name)
                if isinstance(item, type):  # It's a class
                    classes.append(item_name)
                else:
                    other_items.append(item_name)
            
            print(f"\nClasses: {classes}")
            print(f"Other items: {other_items}")
            
            # Explore the MessageService class in detail
            if 'MessageService' in classes:
                print(f"\n{'='*60}")
                print(f"DETAILED MessageService CLASS EXPLORATION")
                print(f"{'='*60}")
                
                message_service_class = getattr(message_module, 'MessageService')
                print(f"Type: {type(message_service_class)}")
                print(f"Module: {message_service_class.__module__}")
                print(f"Documentation: {message_service_class.__doc__}")
                
                # Get all methods (public only)
                methods = [attr for attr in dir(message_service_class) if not attr.startswith('_') and callable(getattr(message_service_class, attr, None))]
                print(f"Total methods: {len(methods)}")
                print(f"All methods: {methods}")
                
                # Get method signatures
                import inspect
                print(f"\nMethod signatures:")
                for method_name in methods:
                    try:
                        method = getattr(message_service_class, method_name)
                        sig = inspect.signature(method)
                        print(f"  {method_name}{sig}")
                    except Exception as e:
                        print(f"  {method_name}: Could not get signature - {e}")
            
            # Also explore the actual instance we're using
            print(f"\n{'='*60}")
            print(f"CURRENT MESSAGE SERVICE INSTANCE")
            print(f"{'='*60}")
            
            message_service = bdk.messages()
            print(f"Instance type: {type(message_service)}")
            instance_methods = [attr for attr in dir(message_service) if not attr.startswith('_') and callable(getattr(message_service, attr, None))]
            print(f"Instance methods: {instance_methods}")
            
            await bdk.messages().send_message(
                context.stream_id,
                "<messageML>Complete message service exploration done! Check console.</messageML>"
            )

        @activities.slash("/explore_message_submodules")
        async def explore_message_submodules(context: CommandContext):
            print("=== EXPLORING MESSAGE SUBMODULES ===")
            
            # Explore each submodule
            submodules = [
                ('symphony.bdk.core.service.message.message_service', 'MessageService'),
                ('symphony.bdk.core.service.message.message_parser', 'MessageParser'),
                ('symphony.bdk.core.service.message.model', 'Model'),
                ('symphony.bdk.core.service.message.multi_attachments_messages_api', 'MultiAttachmentsAPI')
            ]
            
            for module_path, description in submodules:
                try:
                    print(f"\n{'='*60}")
                    print(f"EXPLORING: {module_path}")
                    print(f"{'='*60}")
                    
                    # Import the submodule
                    module = __import__(module_path, fromlist=[''])
                    
                    # Get all items in the submodule
                    items = [attr for attr in dir(module) if not attr.startswith('_')]
                    print(f"Available items: {items}")
                    
                    # Categorize items
                    classes = []
                    functions = []
                    other_items = []
                    
                    for item_name in items:
                        item = getattr(module, item_name)
                        if isinstance(item, type):
                            classes.append(item_name)
                        elif callable(item):
                            functions.append(item_name)
                        else:
                            other_items.append(item_name)
                    
                    print(f"Classes: {classes}")
                    print(f"Functions: {functions}")
                    print(f"Other items: {other_items}")
                    
                    # Explore main classes
                    for class_name in classes[:3]:  # First 3 to avoid too much output
                        cls = getattr(module, class_name)
                        print(f"\n  {class_name}:")
                        print(f"    Type: {type(cls)}")
                        print(f"    Doc: {cls.__doc__}")
                        methods = [attr for attr in dir(cls) if not attr.startswith('_') and callable(getattr(cls, attr, None))]
                        print(f"    Methods: {methods[:10]}{'...' if len(methods) > 10 else ''}")
                        
                except Exception as e:
                    print(f"❌ Error exploring {module_path}: {e}")
            
            await bdk.messages().send_message(
                context.stream_id,
                "<messageML>Message submodules exploration complete!</messageML>"
            )

        @activities.slash("/explore_message_service_methods")
        async def explore_message_service_methods(context: CommandContext):
            print("=== DETAILED MESSAGE SERVICE METHODS ===")
            
            message_service = bdk.messages()
            import inspect
            
            # All methods we found
            methods = ['blast_message', 'get_attachment', 'get_attachment_types', 'get_message', 
                    'get_message_relationships', 'get_message_status', 'import_messages', 
                    'list_attachments', 'list_message_receipts', 'list_messages', 
                    'search_all_messages', 'search_messages', 'send_message', 
                    'suppress_message', 'update_message']
            
            for method_name in methods:
                print(f"\n{'='*50}")
                print(f"METHOD: {method_name}")
                print(f"{'='*50}")
                
                method = getattr(message_service, method_name)
                
                # Documentation
                if method.__doc__:
                    print(f"Documentation: {method.__doc__}")
                else:
                    print("Documentation: None")
                
                # Signature
                try:
                    sig = inspect.signature(method)
                    print(f"Signature: {method_name}{sig}")
                    
                    # Parameter details
                    if sig.parameters:
                        print("Parameters:")
                        for name, param in sig.parameters.items():
                            default = "no default" if param.default == inspect.Parameter.empty else f"default={param.default}"
                            annotation = param.annotation if param.annotation != inspect.Parameter.empty else "no type hint"
                            print(f"  - {name}: {annotation} ({default})")
                    else:
                        print("Parameters: None")
                except Exception as e:
                    print(f"Could not get signature: {e}")
            
            await bdk.messages().send_message(
                context.stream_id,
                "<messageML>Detailed method exploration complete!</messageML>"
            )


        # DO NOT DELETE THE FOLLOWING LINE
        # Start the datafeed read loop
        await datafeed_loop.start()


class MessageListener(RealTimeEventListener):
    async def on_message_sent(self, initiator: V4Initiator, event: V4MessageSent):
        logging.debug("Message received from %s: %s",
            initiator.user.display_name, event.message.message)


# Start the main asyncio run
try:
    logging.info("Running bot application...")
    asyncio.run(run())
except KeyboardInterrupt:
    logging.info("Ending bot application")
