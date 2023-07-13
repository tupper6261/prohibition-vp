import discord
from discord.ext import commands
from discord.ui import Button, View, Select
import os
from dotenv import load_dotenv
import asyncio

load_dotenv()

DATABASE_TOKEN = os.getenv('DATABASE_TOKEN')
BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')

guild_id = 1101580614945222708
channel_id = 1129038551066103959
roles = {
    "Artist": 1107785958746771538,
    "Coder": 1107786089932013709,
    "Collector": 1107786213575893012
}

# Set up the bot with the proper intents to read message content and reactions
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    guild = discord.utils.get(bot.guilds, id=guild_id)
    channel = discord.utils.get(guild.channels, id=channel_id)
    await channel.send(
        "Choose your role:",
        components=[
            [
                Button(style=discord.ButtonStyle.green, label=name)
                for name in roles.keys()
            ]
        ]
    )

@bot.event
async def on_button_click(res):
    guild = discord.utils.get(bot.guilds, id=guild_id)
    role_id = roles[res.component.label]
    role = discord.utils.get(guild.roles, id=role_id)
    member = res.guild.get_member(res.user.id)

    if role in member.roles:
        await member.remove_roles(role)
        await res.respond(
            type=InteractionType.ChannelMessageWithSource,
            content=f"Removed role {res.component.label}",
            ephemeral=True
        )
    else:
        await member.add_roles(role)
        await res.respond(
            type=InteractionType.ChannelMessageWithSource,
            content=f"Added role {res.component.label}",
            ephemeral=True
        )

bot.run(BOT_TOKEN)