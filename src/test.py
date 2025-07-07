from symphony.bdk.core.activity.command import CommandContext

async def echo(context: CommandContext):
            name = context.initiator.user.first_name
            print("Available attributes in context:")
            print(dir(context))
            
            print("\nAvailable attributes in context.initiator:")
            print(dir(context.initiator))
            
            print("\nAvailable attributes in context.initiator.user:")
            print(dir(context.initiator.user))
        