import logging
import asyncio
import random
from datetime import datetime
import discord
from discord import app_commands

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
        """Execute a command by sending it as a message to the channel"""
        if delay is None:
            delay = float(self.bot.config['DEFAULT_DELAY'])

        try:
            self.logger.info(f"Starting command execution in channel: {channel.name} ({channel.id})")

            if command == "remove-money":
                try:
                    # Ensure target is properly formatted as a mention
                    target = options['target']
                    if isinstance(target, discord.Member):
                        target = target.mention
                        self.logger.info(f"Formatted mention for target: {target}")

                    # Format command as a regular message, exactly like a user would type
                    cmd = f"!remove-money {target} {options['amount']}"

                    # Detailed logging
                    self.logger.info(f"Preparing to send command: {cmd}")
                    self.logger.info(f"Channel permissions: {channel.permissions_for(channel.guild.me)}")

                    # Wait for the specified delay
                    await asyncio.sleep(delay)

                    # Send as a regular message
                    try:
                        message = await channel.send(content=cmd)
                        self.logger.info(f"Successfully sent message with ID: {message.id}")
                        self.logger.info(f"Message content sent: {message.content}")
                        return True
                    except discord.Forbidden as e:
                        self.logger.error(f"Permission error sending message: {str(e)}")
                        return False
                    except discord.HTTPException as e:
                        self.logger.error(f"HTTP error sending message: {str(e)}")
                        return False

                except KeyError as e:
                    self.logger.error(f"Missing required option: {str(e)}")
                    return False
                except Exception as e:
                    self.logger.error(f"Unexpected error in remove-money command: {str(e)}")
                    return False
            else:
                self.logger.error(f"Unknown command: {command}")
                return False

        except Exception as e:
            self.logger.error(f"Failed to execute command {command}: {str(e)}")
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