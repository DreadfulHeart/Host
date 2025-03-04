import discord
from discord import app_commands
import asyncio
import logging
import random
from discord.ext import commands
from config import load_config
from utils import setup_logging
from api_client import UnbelievaBoatAPI

# Setup logging
logger = setup_logging()

class AutomationBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.guilds = True
        super().__init__(command_prefix="!", intents=intents)
        self.config = load_config()
        self.unbelievaboat = UnbelievaBoatAPI()

    async def setup_hook(self):
        logger.info("Bot is setting up...")
        await self.tree.sync()

    async def on_ready(self):
        logger.info(f"Logged in as {self.user}")

async def main():
    bot = AutomationBot()

    @bot.tree.command(name="gunpoint", description="Rob someone at gunpoint (requires Shotgun role)")
    @app_commands.describe(target="The user to rob (optional, random if not specified)")
    async def gunpoint(interaction: discord.Interaction, target: discord.Member = None):
        try:
            # Check if user has the Shotgun role
            shotgun_role = discord.utils.get(interaction.guild.roles, name="Shotgun")
            if not shotgun_role or shotgun_role not in interaction.user.roles:
                await interaction.response.send_message("❌ You need the Shotgun role to use this command!", ephemeral=True)
                return

            # If no target specified, randomly select one
            if not target:
                members = interaction.guild.members
                valid_targets = [member for member in members if not member.bot and member != interaction.user]

                if not valid_targets:
                    await interaction.response.send_message("❌ No valid targets found!", ephemeral=True)
                    return

                target = random.choice(valid_targets)
            elif target == interaction.user:
                await interaction.response.send_message("❌ You can't rob yourself!", ephemeral=True)
                return
            elif target.bot:
                await interaction.response.send_message("❌ You can't rob a bot!", ephemeral=True)
                return

            # Send initial response
            await interaction.response.send_message(f"🔫 You're robbing {target.mention}!")

            # Use UnbelievaBoat API to remove money
            guild_id = str(interaction.guild_id)
            user_id = str(target.id)
            amount = 50000

            logger.info(f"Attempting to remove {amount} from user {user_id} in guild {guild_id}")

            result = await bot.unbelievaboat.remove_money(guild_id, user_id, amount)

            if result:
                new_balance = result.get('cash', 'unknown')
                await interaction.followup.send(
                    f"💰 Successfully robbed {amount:,} from {target.mention}!\n"
                    f"Their new balance is ${new_balance:,}"
                )
            else:
                await interaction.followup.send(
                    "❌ Failed to rob the target. They might be broke or protected!\n"
                    "Make sure you have permissions to use economy commands."
                )

        except Exception as e:
            logger.error(f"Error in gunpoint command: {str(e)}")
            await interaction.followup.send("❌ An unexpected error occurred while trying to rob the target.")

    try:
        async with bot:
            await bot.start(bot.config['TOKEN'])
    except Exception as e:
        logger.error(f"Failed to start bot: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())