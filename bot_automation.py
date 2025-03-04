import discord
from discord import app_commands
import asyncio
import logging
import random
from discord.ext import commands
from config import load_config
from utils import setup_logging, CommandExecutor

# Setup logging
logger = setup_logging()

class AutomationBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True  # Enable member intents for member listing
        super().__init__(command_prefix="!", intents=intents)
        self.config = load_config()
        self.command_executor = CommandExecutor(self)

    async def setup_hook(self):
        logger.info("Bot is setting up...")
        await self.tree.sync()  # Sync slash commands

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

    @bot.tree.command(name="gunpoint", description="Rob someone at gunpoint (requires Shotgun role)")
    async def gunpoint(interaction: discord.Interaction):
        try:
            # Check if user has the Shotgun role
            shotgun_role = discord.utils.get(interaction.guild.roles, name="Shotgun")
            if not shotgun_role or shotgun_role not in interaction.user.roles:
                await interaction.response.send_message("❌ You need the Shotgun role to use this command!", ephemeral=True)
                return

            # Get all members from the server
            members = interaction.guild.members
            # Filter out bots and the command user
            valid_targets = [member for member in members if not member.bot and member != interaction.user]

            if not valid_targets:
                await interaction.response.send_message("❌ No valid targets found!", ephemeral=True)
                return

            # Randomly select a target
            target = random.choice(valid_targets)

            # Send initial response
            await interaction.response.send_message(f"🔫 You're robbing {target.mention}!")

            # Execute the remove-money command
            channel = interaction.channel
            command = {
                "command": "remove-money",
                "options": {
                    "target": target.mention,
                    "amount": "50000"
                },
                "delay": 2
            }

            success = await bot.command_executor.execute_slash_command(
                channel,
                command["command"],
                command["options"],
                command["delay"]
            )

            if success:
                await interaction.followup.send(f"💰 Successfully robbed {target.mention} of 50,000!")
            else:
                await interaction.followup.send("❌ Failed to execute the robbery!")

        except Exception as e:
            logger.error(f"Error in gunpoint command: {str(e)}")
            await interaction.followup.send("❌ An unexpected error occurred.")

    try:
        async with bot:
            await bot.start(bot.config['TOKEN'])
    except Exception as e:
        logger.error(f"Failed to start bot: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())