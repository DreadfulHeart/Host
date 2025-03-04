import discord
import asyncio
import logging
from discord.ext import commands
from config import load_config
from utils import setup_logging, CommandExecutor

# Setup logging
logger = setup_logging()

class AutomationBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)
        self.config = load_config()
        self.command_executor = CommandExecutor(self)
        
    async def setup_hook(self):
        logger.info("Bot is setting up...")
        
    async def on_ready(self):
        logger.info(f"Logged in as {self.user}")
        
    async def execute_command_sequence(self, channel_id, commands):
        """Execute a sequence of slash commands"""
        channel = self.get_channel(channel_id)
        if not channel:
            logger.error(f"Channel {channel_id} not found")
            return False
            
        try:
            for cmd in commands:
                await self.command_executor.execute_slash_command(
                    channel,
                    cmd['command'],
                    cmd.get('options', {}),
                    cmd.get('delay', 2)
                )
        except Exception as e:
            logger.error(f"Error executing command sequence: {str(e)}")
            return False
        return True

async def main():
    bot = AutomationBot()
    
    @bot.command(name="run_sequence")
    async def run_sequence(ctx, channel_id: str = None):
        """Run a predefined sequence of commands in the specified channel"""
        try:
            # Use current channel if no channel_id provided
            target_channel_id = int(channel_id) if channel_id else ctx.channel.id
            channel = bot.get_channel(target_channel_id)

            if not channel:
                await ctx.send(f"❌ Could not find channel with ID: {target_channel_id}")
                return

            await ctx.send(f"Starting command sequence in channel: {channel.name}...")

            # Example command sequence
            commands = [
                {"command": "ping", "delay": 2},
                {"command": "help", "delay": 3},
            ]

            success = await bot.execute_command_sequence(target_channel_id, commands)
            if success:
                await ctx.send("✅ Command sequence completed successfully!")
            else:
                await ctx.send("❌ Error occurred during command execution.")

        except ValueError:
            await ctx.send("❌ Invalid channel ID provided. Please provide a valid channel ID.")
        except Exception as e:
            logger.error(f"Error in run_sequence: {str(e)}")
            await ctx.send("❌ An unexpected error occurred.")

    try:
        async with bot:
            await bot.start(bot.config['TOKEN'])
    except Exception as e:
        logger.error(f"Failed to start bot: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())