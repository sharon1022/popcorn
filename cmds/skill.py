import discord
from typing import List, Union
from discord.ext import commands
import json

class Skill(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def sk(self,ctx,str1:int,str2:int,str3:int,str4:int,str5:int):
        skill = (str1+str2/5+str3/5+str4/5+str5/5)/100+1
        round_sk = round(skill,2)
        await ctx.send(f"這隊倍率為{round_sk}")

    @commands.command()
    async def 倍率(self,ctx,str1:int,str2:int,str3:int,str4:int,str5:int):
        skill = (str1+str2/5+str3/5+str4/5+str5/5)/100+1
        round_sk = round(skill,2)
        await ctx.send(f"這隊倍率為{round_sk}")

async def setup(bot:commands.bot):
    await bot.add_cog(Skill(bot))