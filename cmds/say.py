import discord
from discord.ext import commands
import asyncio
from gtts import gTTS
import os

intents = discord.Intents.default()
intents.voice_states = True
intents.message_content = True

class Say(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True)
    async def join(self,ctx):
        if not ctx.author.voice:
            await ctx.send("你沒有加入任何語音頻道！")
            return

        channel = ctx.author.voice.channel

        if ctx.voice_client:
            await ctx.voice_client.disconnect()
       
        await channel.connect(timeout=20.0, reconnect=True)
        await ctx.send(f"機器人加入了 {channel.name} 語音頻道！")
            
    @commands.command()
    async def leave(self,ctx):
        if (ctx.voice_client):
            await ctx.guild.voice_client.disconnect()
            await ctx.send("機器人已離開語音頻道！")
        else:
            await ctx.send("機器人不在任何語音頻道中！")
    
    @commands.Cog.listener()
    async def on_message(self,message):
        if message.author == self.bot.user:
            return
        voice_client = message.guild.voice_client
        if message.content.startswith('*'):
            text = message.content[1:]
            if not text.strip():
                await message.channel.send("請輸入要讓機器人說話的內容")
                return
            if not voice_client:
                await message.channel.send("機器人不在語音頻道中，請先使用 &join 命令讓機器人加入語音頻道。")
                return

        tts = gTTS(text, lang='zh')
        filename = 'tts.mp3'
        tts.save(filename)
        if not voice_client.is_playing():
                voice_client.play(discord.FFmpegPCMAudio(source=filename))
                while voice_client.is_playing():
                    await asyncio.sleep(1)
                os.remove(filename)
        else:
                await message.channel.send("機器人目前正在播放其他音訊，請稍後再試。")
    
    @commands.command()
    async def stop(self,ctx):
        voice_client = ctx.voice_client
        if voice_client and voice_client.is_playing():
            voice_client.stop()
            await ctx.send("已停止播放語音。")
        else:
            await ctx.send("目前沒有正在播放的語音。")

async def setup(bot: commands.Bot):
    await bot.add_cog(Say(bot))