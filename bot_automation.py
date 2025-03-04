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

    @bot.tree.command(name="gunpoint", description="Rob someone at gunpoint (requires Woozie role)")
    @app_commands.describe(target="The user to rob (optional, random if not specified)")
    async def gunpoint(interaction: discord.Interaction, target: discord.Member = None):
        try:
            # Check if user has the Woozie role
            woozie_role = discord.utils.get(interaction.guild.roles, name="Woozie")
            if not woozie_role or woozie_role not in interaction.user.roles:
                await interaction.response.send_message("❌ You need the Woozie role to use this command!", ephemeral=True)
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

            # Check if target has the shotgun role (case insensitive check)
            shotgun_role = discord.utils.find(
                lambda r: r.name.lower() == "shotgun",
                interaction.guild.roles
            )
            
            # Debug log to help troubleshoot
            logger.info(f"Checking if {target.display_name} has shotgun role")
            if shotgun_role:
                logger.info(f"Found shotgun role: {shotgun_role.name}")
                logger.info(f"Target roles: {[role.name for role in target.roles]}")
            else:
                logger.info(f"No shotgun role found in the server")
            
            if shotgun_role and shotgun_role in target.roles:
                # Target has shotgun role, they defend themselves
                logger.info(f"{target.display_name} has shotgun role, preventing robbery")
                await interaction.response.send_message(
                    f"🔫 You try to rob {target.mention}, but they have a shotgun!\n"
                    f"💥 {target.display_name} protected themselves! You were blown away with the shotgun!"
                )
                return

            # Send initial response for normal robbery
            await interaction.response.send_message(f"🔫 You're robbing {target.mention}!")

            # Use UnbelievaBoat API to remove money with random amount between 25k-50k
            guild_id = str(interaction.guild_id)
            target_user_id = str(target.id)
            robber_user_id = str(interaction.user.id)
            amount = random.randint(25000, 50000)

            logger.info(f"Attempting to remove {amount} from user {target_user_id} in guild {guild_id}")

            # Remove money from target
            result = await bot.unbelievaboat.remove_money(guild_id, target_user_id, amount)

            if result:
                target_new_balance = result.get('cash', 'unknown')
                
                # Add the stolen money to the robber
                logger.info(f"Attempting to add {amount} to user {robber_user_id} in guild {guild_id}")
                add_result = await bot.unbelievaboat.add_money(guild_id, robber_user_id, amount)
                
                if add_result:
                    robber_new_balance = add_result.get('cash', 'unknown')
                    await interaction.followup.send(
                        f"💰 Successfully robbed ${amount:,} from {target.mention}!\n"
                        f"Their new balance is ${target_new_balance:,}\n"
                        f"Your new balance is ${robber_new_balance:,}"
                    )
                else:
                    await interaction.followup.send(
                        f"💰 Successfully robbed ${amount:,} from {target.mention}, but failed to add it to your account.\n"
                        f"Their new balance is ${target_new_balance:,}"
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