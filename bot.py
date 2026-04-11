import discord
from discord.ext import commands,tasks
import json
import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.voice_states = True
intents.message_content = True

intents = discord.Intents.all()
bot = commands.Bot(command_prefix = "&", intents = intents)


@bot.event
async def on_ready():
    activity = discord.Activity(type=discord.ActivityType.watching, name="&h 指令表(最近更新時間:2026/4/4)")
    await bot.change_presence(status=discord.Status.online, activity=activity)
    print(f"目前登入身份 --> {bot.user}")

@bot.event
async def on_member_join(member: discord.Member):
    channel1 = bot.get_channel(1080147523315957894)
    channel2 = bot.get_channel(1199999825102512181)
    channel3 = bot.get_channel(1305874647958687815)
    print(f"「{member.display_name}」加入「{member.guild.name}」伺服器")

@bot.event
async def on_member_remove(member: discord.Member):
    channel1 = bot.get_channel(1080147523315957894)
    channel2 = bot.get_channel(1199999825102512181)
    print(f"「{member.display_name}」離開「{member.guild.name}」伺服器")

@bot.command()
async def load(ctx, extension):
    try:
        await bot.load_extension(f"cmds.{extension}")
        await ctx.send(f"Loaded {extension} done.")
    except Exception as e:
            await ctx.send(e) 

@bot.command()
async def unload(ctx, extension):
    await bot.unload_extension(f"cmds.{extension}")
    await ctx.send(f"UnLoaded {extension} done.")

@bot.command()
async def reload(ctx, extension):
    try:
        await bot.reload_extension(f"cmds.{extension}")
        await ctx.send(f"ReLoaded {extension} done.")
    except Exception as e:
            await ctx.send(e) 
async def main():
    for filename in os.listdir("./cmds"):
        if filename.endswith("py"):
            await bot.load_extension(f"cmds.{filename[:-3]}")
    await bot.start(os.getenv("DISCORD_TOKEN"))

if __name__ == "__main__":
    asyncio.run(main())