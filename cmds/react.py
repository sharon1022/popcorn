import discord
from typing import List, Union
from discord.ext import commands
import json

# 1. 定義選單 View (放在 Cog 外面或裡面皆可，這裡放外面方便維護)
class HelpMenuView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None) 

    # 1. 改良後的共用邏輯：支援傳入多個欄位
    # fields 格式為：[("標題1", "內容1"), ("標題2", "內容2")]
    async def _update_embed(self, interaction: discord.Interaction, fields: list):
        embed = discord.Embed(title="爆米花使用指南", color=discord.Color.from_str("#ff9911"))
        
        for name, value in fields:
            embed.add_field(name=name, value=value, inline=False)
            
        await interaction.response.edit_message(embed=embed, view=self)

    # 2. 按鈕部分
    @discord.ui.button(label="一般指令", style=discord.ButtonStyle.primary, row=0)
    async def normal_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        # 把要顯示的所有內容包在一個清單裡
        my_fields = [
            ("遊戲相關", ">>> **&sk [隊長] [成員] [成員] [成員] [成員]\n&倍率 [隊長] [成員] [成員] [成員] [成員]**\n。幫你算倍率"),
            ("查榜相關", ">>> **&rank [名次]-[名次]**\n。查詢排名資訊(可輸入單一名次)"),
            ("語音房相關", ">>> **&join**\n。讓爆米花加入語音房\n*註：請先加入語音頻道後再使用此指令\n**&leave**\n。讓爆米花退出語音房\n**\\*[內文]**\n。讓爆米花說你想說的話\n**&stop**\n。讓爆米花停止說話")
        ]
        
        # 只呼叫一次 _update_embed，但帶入多個內容
        await self._update_embed(interaction, my_fields)

    # 3. 其他按鈕（例如只有一個欄位的）也可以用同樣的邏輯
    @discord.ui.button(label="私車專用指令", style=discord.ButtonStyle.primary, row=0)
    async def voice_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        my_fields = [
            ("登記相關", ">>> **&reg [名稱] [倍率]**\n。登記原推倍率\n**&regs6 [倍率] [綜合]**\n。登記S6倍率&綜合"),
            ("報班相關", ">>> **[日期] [時間]-[時間]**\n。報班\n**-[日期] [時間]-[時間]**\n。砍班\n&vac [日期]\n。查缺額\n&sub [日期]\n。查候補"),
            ("伺服器相關", ">>> **[房號]**\n。輸入房號改名，輸入0改回\n&che\n。提醒車上成員")
        ]
        await self._update_embed(interaction, my_fields)


# 2. 將指令與監聽器封裝在 Cog 中
class React(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def h(self, ctx):
        """幫助指令"""
        embed = discord.Embed(
            title='爆米花使用指南',
            color=discord.Color.from_str("#ff9911")
        )
        embed.add_field(name="遊戲相關", value=">>> **&sk [隊長] [成員] [成員] [成員] [成員]\n&倍率 [隊長] [成員] [成員] [成員] [成員]**\n。幫你算倍率", inline=False)
        embed.add_field(name="查榜相關", value=">>> **&rank [名次]-[名次]**\n。查詢排名資訊(可輸入單一名次)", inline=False)
        embed.add_field(name="語音房相關", value=">>> **&join**\n。讓爆米花加入語音房\n*註：請先加入語音頻道後再使用此指令\n**&leave**\n。讓爆米花退出語音房\n**\\*[內文]**\n。讓爆米花說你想說的話\n**&stop**\n。讓爆米花停止說話", inline=False)
        # 初始化 View 並發送
        await ctx.send(embed=embed, view=HelpMenuView())

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, data):
        if data.message_id == 1440326957618299031:  # 金魚私車
            if str(data.emoji) == '<a:emoji_40:1305829128955760680>':
                guild = self.bot.get_guild(1164979913548382210)
                user = guild.get_member(data.user_id)
                role = guild.get_role(1439770810926497893)
                await user.add_roles(role)
        elif data.message_id == 1349386596922687518:  # 阿堇私車
            if str(data.emoji) == '<:L1_thx:1202707292840001626>':
                guild = self.bot.get_guild(1201110858957332480)
                user = guild.get_member(data.user_id)
                role = guild.get_role(1349247663148765184)
                if guild and user and role:
                    await user.add_roles(role)
            elif str(data.emoji) == '<:chihuahua_sleep:1202723352003743857>':
                guild = self.bot.get_guild(1201110858957332480)
                user = guild.get_member(data.user_id)
                role1 = guild.get_role(1349247908511219742)
                await user.add_roles(role1)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, data):
        if data.message_id == 1440326957618299031:  # 金魚私車
            if str(data.emoji) == '<a:emoji_40:1305829128955760680>':
                guild = self.bot.get_guild(1164979913548382210)
                user = guild.get_member(data.user_id)
                role = guild.get_role(1439770810926497893)
                await user.remove_roles(role)
        elif data.message_id == 1349386596922687518:  # 阿堇私車
            if str(data.emoji) == '<:L1_thx:1202707292840001626>':
                guild = self.bot.get_guild(1201110858957332480)
                user = guild.get_member(data.user_id)
                role = guild.get_role(1349247663148765184)
                await user.remove_roles(role)
            elif str(data.emoji) == '<:chihuahua_sleep:1202723352003743857>':
                guild = self.bot.get_guild(1201110858957332480)
                user = guild.get_member(data.user_id)
                role1 = guild.get_role(1349247908511219742)
                await user.remove_roles(role1)

    @commands.Cog.listener()
    async def on_message(self, message): #更改房號
        try:
            channel = self.bot.get_channel(1424899372210065428) #綾車頻
            if message.author == self.bot.user:
                return
            if message.channel.id in [1424899372210065428,1424899372210065428]:
                if message.content.isdigit():
                    if len(message.content) == 5:
                        await channel.edit(name=f"{message.content}")
                        await channel.send(f'已將頻道名改為[{message.content}]\n(十分鐘內機器人只可改2次名)')
                    elif message.content == '0':
                        await channel.edit(name='房號')
                        await channel.send('已將頻道名改回')
        except Exception as e:
            print(e)

async def setup(bot: commands.Bot):
    await bot.add_cog(React(bot))