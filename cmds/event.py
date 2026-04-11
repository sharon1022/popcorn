import discord
from discord.ext import commands
import os
import asyncio
import requests
from datetime import datetime, timezone, timedelta
from dateutil import parser

BOT_DIR = os.getcwd()

REGION = "tw"

class PJSKEvent(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def rank(self, ctx, rank_num):
        rank_num_str = rank_num
        try:
            url = "https://api.hisekai.org/tw/event/live/top100"
            resp = requests.get(url)
            data = resp.json()

            async with ctx.typing():
                event_id = data["id"]
            
            players = data["top_100_player_rankings"]

            # 支持範圍查詢 (例如 5-10)
            if "-" in rank_num_str:
                start, end = map(int, rank_num_str.split("-"))
                target_ranks = list(range(start, end + 1))
            else:
                target_ranks = [int(rank_num_str)]

            # 尋找指定的所有 rank
            results = []
            for target_rank in target_ranks:
                for p in players:
                    if p["rank"] == target_rank:
                        results.append(p)
                        break
            
            if not results:
                await ctx.send("找不到此名次範圍資料")
                return

            # 建立單一 Embed，包含所有名次
            embed = discord.Embed(
                color=discord.Color.from_rgb(int(0.945 * 255), int(0.906 * 255), int(0.486 * 255)),
            )

            # 逐個名次添加欄位
            for p in results:
                # 找下一名玩家資料
                p_2 = next((x for x in players if x["rank"] == p["rank"] + 1), None)

                name = p["name"]
                score = p['score']
                last_score = p["last_score"]
                time = parser.isoparse(p["last_played_at"]).astimezone(timezone(timedelta(hours=8)))

                one_hour = p["last_1h_stats"]
                count = one_hour["count"]
                speed = one_hour['speed']
                average = one_hour["average"]

                # 組合欄位內容
                field_value = f"名次：{p['rank']}\n"
                field_value += f"分數：{score:,}\n"
                if p_2:
                    score_diff = score - p_2['score']
                    field_value += f"與下一名分差：{score_diff:,}\n"
                field_value += (
                    f"最近一場pt：{last_score}\n"
                    f"1小時周回：{count}\n"
                    f"1小時分數：{speed:,}\n"
                    f"1小時場均：{average}\n"
                    f"最後更新時間：{time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                    f"-----------------------------\n"
                )

                embed.add_field(name=name, value=field_value, inline=False)

            embed.add_field(name="資料來源", value="[Hi Sekai](https://docs.hisekai.org/zh/docs)", inline=False)
            embed.set_footer(text=f"活動期數：{event_id}")
            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.reply(f'查詢範圍太廣，請重新輸入查詢範圍')


async def setup(bot):
    await bot.add_cog(PJSKEvent(bot))