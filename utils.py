import logging
import asyncio
import random
from datetime import datetime

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(f'bot_automation_{datetime.now().strftime("%Y%m%d")}.log')
        ]
    )
    return logging.getLogger('BotAutomation')

class CommandExecutor:
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger('BotAutomation.CommandExecutor')

    async def execute_slash_command(self, channel, command, options=None, delay=None):
        """Execute a slash command and wait for response"""
        if delay is None:
            delay = float(self.bot.config['DEFAULT_DELAY'])

        try:
            # Log command execution
            self.logger.info(f"Executing command: /{command} with options: {options}")

            # Format the command exactly as needed for the target bot
            if command == "remove-money":
                # Special formatting for remove-money command
                cmd = f"/remove-money {options['target']} {options['amount']}"
            else:
                # Standard slash command formatting
                cmd = f"/{command}"
                if options:
                    option_parts = []
                    for k, v in options.items():
                        option_parts.append(f"{k}:{v}")
                    cmd += " " + " ".join(option_parts)

            # Send the command
            await channel.send(cmd)

            # Wait for the specified delay
            await asyncio.sleep(delay)

            # Log successful execution
            self.logger.info(f"Command /{command} executed successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to execute command /{command}: {str(e)}")
            return False

    async def wait_for_response(self, channel, timeout=None):
        """Wait for a response from the target bot"""
        if timeout is None:
            timeout = int(self.bot.config['COMMAND_TIMEOUT'])

        try:
            def check(message):
                return (
                    message.channel.id == channel.id and
                    message.author.id == int(self.bot.config['TARGET_BOT_ID'])
                )

            response = await self.bot.wait_for(
                'message',
                check=check,
                timeout=timeout
            )
            return response

        except asyncio.TimeoutError:
            self.logger.warning(f"Timeout waiting for response in channel {channel.id}")
            return None