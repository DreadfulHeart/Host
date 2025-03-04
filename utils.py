import logging
import asyncio
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
            delay = self.bot.config['DEFAULT_DELAY']
            
        try:
            # Log command execution
            self.logger.info(f"Executing command: /{command}")
            
            # Create the slash command
            cmd = f"/{command}"
            if options:
                cmd += " " + " ".join([f"{k}:{v}" for k, v in options.items()])
            
            # Send the command
            await channel.send(cmd)
            
            # Wait for the specified delay
            await asyncio.sleep(delay)
            
            # Log successful execution
            self.logger.info(f"Command /{command} executed successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to execute command /{command}: {str(e)}")
            raise
            
    async def wait_for_response(self, channel, timeout=None):
        """Wait for a response from the target bot"""
        if timeout is None:
            timeout = self.bot.config['COMMAND_TIMEOUT']
            
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
