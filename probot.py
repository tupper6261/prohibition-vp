import discord
from discord.ext import commands
from discord.ui import Button, View, Select
import os
from dotenv import load_dotenv
import asyncio

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
            await interaction.response.send_message(f"Removed role {role.name}", ephemeral=True)
        else:
            await interaction.user.add_roles(role)
            await interaction.response.send_message(f"Added role {role.name}", ephemeral=True)

@bot.event
async def on_ready():
    print(f"We have logged in as {bot.user}")
    guild = discord.utils.get(bot.guilds, id=1101580614945222708)
    channel = discord.utils.get(guild.channels, id=1129038551066103959)
    await channel.send("Choose your role:", view=MyView())

bot.run(BOT_TOKEN)