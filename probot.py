import discord
from discord.ext import commands
from discord.ui import Button, View, Select
import os
from dotenv import load_dotenv
import asyncio
from datetime import datetime

load_dotenv()

DATABASE_TOKEN = os.getenv('DATABASE_TOKEN')
BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')

# Set up the bot with the proper intents to read message content and reactions
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

class MyView(discord.ui.View):  # Create a class called MyView that subclasses discord.ui.View
    def __init__(self):
        super().__init__(timeout=None)  # timeout of the view must be set to None

    @discord.ui.button(label="Artist", style=discord.ButtonStyle.primary)  # Create a button with the label "Artist" with color Blurple
    async def artist_button_callback(self, button, interaction):
        role = discord.utils.get(interaction.guild.roles, id=1107785958746771538)
        await self.toggle_role(interaction, role)

    @discord.ui.button(label="Coder", style=discord.ButtonStyle.primary)  # Create a button with the label "Coder" with color Blurple
    async def coder_button_callback(self, button, interaction):
        role = discord.utils.get(interaction.guild.roles, id=1107786089932013709)
        await self.toggle_role(interaction, role)

    @discord.ui.button(label="Collector", style=discord.ButtonStyle.primary)  # Create a button with the label "Collector" with color Blurple
    async def collector_button_callback(self, button, interaction):
        role = discord.utils.get(interaction.guild.roles, id=1107786213575893012)
        await self.toggle_role(interaction, role)

    @staticmethod
    async def toggle_role(interaction, role):
        if role in interaction.user.roles:
            await interaction.user.remove_roles(role)
            await interaction.response.send_message(f"I have successfully removed your {role.name} role.", ephemeral=True)
        else:
            await interaction.user.add_roles(role)
            await interaction.response.send_message(f"I have successfully given you the {role.name} role.", ephemeral=True)

@bot.event
async def on_ready():
    guild = discord.utils.get(bot.guilds, id=1101580614945222708)
    channel = discord.utils.get(guild.channels, id=1129038551066103959)
    message_id = 1129129885928005874
    message = await channel.fetch_message(message_id)
    await message.edit(content="Tap the below buttons to add/remove the corresponding role:", view=MyView())

    # Get the role to assign
    role = discord.utils.get(guild.roles, id=1129131947625562183)

    # Define the cutoff date
    cutoff = datetime(2023, 7, 11)  # Replace with the correct year

    # Iterate over the members of the guild
    for member in guild.members:
        # If the member joined before the cutoff date, add the role
        if member.joined_at < cutoff:
            await member.add_roles(role)

    print("Role assignment complete")

bot.run(BOT_TOKEN)