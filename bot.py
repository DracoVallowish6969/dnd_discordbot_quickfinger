"""
Main entry point. Run with: python bot.py
"""
import os
import asyncio
import discord
from discord.ext import commands
from dotenv import load_dotenv

import database

load_dotenv()

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (id: {bot.user.id})")
    try:
        # Global sync (can take up to an hour to propagate everywhere across Discord)
        synced = await bot.tree.sync()
        print(f"Globally synced {len(synced)} slash command(s).")

        # Guild sync (instant update in every server the bot is currently in)
        for guild in bot.guilds:
            guild_synced = await bot.tree.sync(guild=guild)
            print(f"⚡ Instantly synced {len(guild_synced)} command(s) to server '{guild.name}'.")
    except Exception as e:
        print(f"❌ Failed to sync commands: {e}")


@bot.tree.command(name="ping", description="Check if the bot is alive")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("🏓 Pong! I'm alive and ready to roll some dice.")


async def main():
    await database.init_db()
    await bot.load_extension("cogs.character")
    await bot.load_extension("cogs.dice")
    await bot.load_extension("cogs.spells")

    token = os.environ.get("DISCORD_BOT_TOKEN")
    if not token:
        raise RuntimeError("No DISCORD_BOT_TOKEN found. Set it as an environment variable.")
    await bot.start(token)


if __name__ == "__main__":
    asyncio.run(main())