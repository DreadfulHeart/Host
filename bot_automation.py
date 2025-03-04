import discord
from discord import app_commands
import asyncio
import logging
import random
import os
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

            # Check for roles
            shotgun_role = discord.utils.find(
                lambda r: r.name.lower() == "shotgun",
                interaction.guild.roles
            )
            
            # Debug log to help troubleshoot
            logger.info(f"Checking if {target.display_name} has shotgun/woozie roles")
            if shotgun_role:
                logger.info(f"Found shotgun role: {shotgun_role.name}")
                logger.info(f"Target roles: {[role.name for role in target.roles]}")
            else:
                logger.info(f"No shotgun role found in the server")
            
            # Priority check: if target has Woozie role, always trigger the gunfight scenario
            # regardless of whether they have a shotgun role
            if woozie_role in target.roles:
                # Both have Woozie role, gunfight happens
                logger.info(f"Gunfight scenario: both {interaction.user.display_name} and {target.display_name} have Woozie role")
                
                penalty1 = random.randint(5000, 15000)
                penalty2 = random.randint(5000, 15000)
                
                # Initial response
                await interaction.response.send_message(
                    f"🔫 You try to rob {target.mention}, but they pull out their piece too!"
                )
                
                # Dramatic gunfight sequence
                gunfight_messages = [
                    f"💥 **BANG!** {interaction.user.display_name} fires first but misses!",
                    f"💨 {target.display_name} ducks behind cover and returns fire!",
                    f"🔫 **BANG! BANG!** Bullets fly everywhere!",
                    f"💢 {interaction.user.display_name} gets grazed by a bullet! (-${penalty1:,})",
                    f"💥 Your shot hits {target.display_name}'s arm! (-${penalty2:,})",
                    f"🚓 The sound of police sirens in the distance forces you both to flee!"
                ]
                
                # Send each message with a delay for dramatic effect
                for i, message in enumerate(gunfight_messages):
                    if i == 0:  # First message is already sent
                        await asyncio.sleep(1.5)
                    else:
                        await asyncio.sleep(1.5)
                        await interaction.followup.send(message)
                
                # Remove money from both participants
                guild_id = str(interaction.guild_id)
                robber_user_id = str(interaction.user.id)
                target_user_id = str(target.id)
                
                # Remove from robber
                result1 = await bot.unbelievaboat.remove_money(guild_id, robber_user_id, penalty1)
                # Remove from target
                result2 = await bot.unbelievaboat.remove_money(guild_id, target_user_id, penalty2)
                
                if result1 and result2:
                    robber_new_balance = result1.get('cash', 'unknown')
                    target_new_balance = result2.get('cash', 'unknown')
                    await interaction.followup.send(
                        f"💸 **Gunfight Aftermath:**\n"
                        f"{interaction.user.mention}: ${robber_new_balance:,} (-${penalty1:,})\n"
                        f"{target.mention}: ${target_new_balance:,} (-${penalty2:,})"
                    )
                
                return
            
            # If target only has shotgun role (no Woozie role), trigger the shotgun defense scenario
            elif shotgun_role and shotgun_role in target.roles:
                # Target has shotgun role, they defend themselves - attacker loses money
                penalty = random.randint(10000, 15000)
                logger.info(f"{target.display_name} has shotgun role, preventing robbery and penalizing robber {penalty}")
                
                # Initial response
                await interaction.response.send_message(
                    f"🔫 You try to rob {target.mention}, but wait... what's that they're reaching for?"
                )
                
                # Dramatic shotgun defense sequence
                shotgun_messages = [
                    f"💥 **BOOM!** {target.display_name} pulls out a shotgun!",
                    f"😱 You try to run but it's too late!",
                    f"💢 **BOOM!** The shotgun blast catches you! (-${penalty:,})",
                    f"🩸 You manage to escape, but not without serious injuries!"
                ]
                
                # Send each message with a delay for dramatic effect
                for message in shotgun_messages:
                    await asyncio.sleep(1.5)
                    await interaction.followup.send(message)
                
                # Remove penalty money from robber
                guild_id = str(interaction.guild_id)
                robber_user_id = str(interaction.user.id)
                
                result = await bot.unbelievaboat.remove_money(guild_id, robber_user_id, penalty)
                if result:
                    robber_new_balance = result.get('cash', 'unknown')
                    await interaction.followup.send(
                        f"💸 **Medical Bill:** ${penalty:,}\n"
                        f"Your new balance: ${robber_new_balance:,}"
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

    @bot.tree.command(name="geturl", description="Get the bot's Replit URL for uptime monitoring (Admin only)")
    @app_commands.check(lambda interaction: interaction.user.guild_permissions.administrator)
    async def geturl(interaction: discord.Interaction):
        try:
            # Check if user is an administrator
            if not interaction.user.guild_permissions.administrator:
                await interaction.response.send_message("❌ You need administrator permissions to use this command!", ephemeral=True)
                return
                
            repl_slug = os.getenv('REPL_SLUG', 'unknown')
            repl_owner = os.getenv('REPL_OWNER', 'unknown')
            
            if repl_slug != 'unknown' and repl_owner != 'unknown':
                replit_url = f"https://{repl_slug}.{repl_owner}.repl.co"
                await interaction.response.send_message(
                    f"🔗 **Bot URL for UptimeRobot:**\n{replit_url}\n\n"
                    f"Copy this URL to set up monitoring on UptimeRobot to keep the bot online 24/7.",
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    "❌ Could not determine the Replit URL. Make sure this is running on Replit.",
                    ephemeral=True
                )
                
        except Exception as e:
            logger.error(f"Error in geturl command: {str(e)}")
            await interaction.response.send_message(
                "❌ An error occurred while getting the URL.",
                ephemeral=True
            )

    try:
        async with bot:
            await bot.start(bot.config['TOKEN'])
    except Exception as e:
        logger.error(f"Failed to start bot: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())