import discord
from discord.ext import commands, tasks
import os
import asyncio
import aiohttp  # 引入非同步網路庫
import json
from datetime import datetime, timezone, timedelta
from dateutil import parser
from collections import deque

BOT_DIR = os.getcwd()
REGION = "tw"

class PJSKEvent(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.rank_history = {}
        # 建立一個持久的 aiohttp Session，避免重複建立連線，也能大幅提升效能
        self.session = aiohttp.ClientSession()
        # 追蹤目前活動的結束時間與名稱（timezone-aware datetime）
        self.current_event_close_time = None
        self.current_event_name = None
        
        # 嘗試載入先前儲存的歷史（如有）
        history_path = os.path.join(BOT_DIR, "event_rank_history.json")
        if os.path.exists(history_path):
            try:
                with open(history_path, "r", encoding="utf-8") as hf:
                    j = json.load(hf)
                    for k, v in j.get("history", {}).items():
                        try:
                            # 固定保留最近 11 次取樣，對應 10 個時間差
                            self.rank_history[int(k)] = deque(v, maxlen=11)
                        except Exception:
                            continue
            except Exception:
                pass

        self.update_rank_data.start()

    def cog_unload(self):
        # 當 Cog 被卸載時，確保關閉網路 Session 與 Task
        self.bot.loop.create_task(self.session.close())
        self.update_rank_data.cancel()

    def _append_jsonl(self, file_path, record):
        try:
            with open(file_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
            return True
        except Exception:
            return False

    def _write_if_changed(self, file_path, content):
        try:
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    if f.read() == content:
                        return False

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            return True
        except Exception:
            return False
        
    def _load_saved_close_time(self):
        """從本地 event_rank_history.json 嘗試載入已知的活動結束時間（假設為 UTC+8）。"""
        path = os.path.join(BOT_DIR, "event_rank_history.json")
        if not os.path.exists(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                j = json.load(f)
            close_time_str = j.get("close_time")
            if not close_time_str:
                return None
            dt = parser.parse(close_time_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone(timedelta(hours=8)))
            self.current_event_close_time = dt
            return dt
        except Exception:
            return None
        
    def _is_event_active(self):
        """回傳活動是否仍在進行中（以 UTC 時間比對）。"""
        if not self.current_event_close_time:
            return False
        try:
            now_utc = datetime.now(timezone.utc)
            event_close_utc = self.current_event_close_time.astimezone(timezone.utc)
            return now_utc < event_close_utc
        except Exception:
            return False

    # 每 1 分鐘嚴格執行一次
    @tasks.loop(minutes=1)
    async def update_rank_data(self):
        try:
            # 嘗試先從快取載入活動結束時間，若已結束就不向 API 請求
            if not self.current_event_close_time:
                self._load_saved_close_time()
            if not self._is_event_active():
                return
            url = "https://api.hisekai.org/tw/event/live/top100"
            
            # 改用 aiohttp 非同步獲取資料，絕不卡死 Bot 計時器
            async with self.session.get(url) as resp:
                if resp.status != 200:
                    print(f"API 請求失敗，狀態碼: {resp.status}")
                    return
                data = await resp.json()

            event_id = data["id"]
            close_time = data["aggregate_at"]
            close_time_utc8 = parser.isoparse(close_time).astimezone(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S')
            event_name = data["name"]
            # 更新目前活動資訊（保留 timezone-aware 的 datetime 方便比對）
            try:
                self.current_event_close_time = parser.isoparse(close_time)
            except Exception:
                self.current_event_close_time = None
            self.current_event_name = event_name

            history_snapshot = {}
            players = data.get("player_top_100_rankings", [])

            for p in players:
                try:
                    rank = int(p.get("rank"))
                    score = p.get("score")
                except Exception:
                    continue

                last_played_at = p.get("last_played_at")
                if last_played_at:
                    try:
                        ts = parser.isoparse(last_played_at).astimezone(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S')
                    except Exception:
                        ts = datetime.now(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S')
                else:
                    ts = datetime.now(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S')

                if rank not in self.rank_history:
                    self.rank_history[rank] = deque(maxlen=11)

                # 每分鐘固定記錄一次，但若分數未變化則不重複記錄
                if not self.rank_history[rank] or self.rank_history[rank][-1]["score"] != score:
                    self.rank_history[rank].append({"score": score, "time": ts})
                    history_snapshot[str(rank)] = list(self.rank_history[rank])

            # 將基本活動資料寫入文字檔
            event_data_content = (
                f"活動期數：{event_id}\n"
                f"活動名稱：{event_name}\n"
                f"結束時間：{close_time_utc8} (UTC+8)\n"
            )
            self._write_if_changed(os.path.join(BOT_DIR, "event_data.txt"), event_data_content)

            # 將 rank history 寫入 JSON 檔
            try:
                out = {
                    "event_id": event_id,
                    "name": event_name,
                    "close_time": close_time_utc8,
                    "updated_at": ts,
                    "history": history_snapshot,
                }
                json_content = json.dumps(out, ensure_ascii=False, indent=2)
                self._write_if_changed(os.path.join(BOT_DIR, "event_rank_history.json"), json_content)
            except Exception:
                pass

        except Exception as e:
            print(f"更新活動資料時發生錯誤: {e}")

    # 確保 Bot 準備就緒後才開始跑定時任務，防止初期讀取混亂
    @update_rank_data.before_loop
    async def before_update_rank_data(self):
        await self.bot.wait_until_ready()

    @commands.command()
    async def rank(self, ctx, rank_num):
        rank_num_str = rank_num
        try:
            # 這裡順便改用非同步請求
            async with ctx.typing():
                async with self.session.get("https://api.hisekai.org/tw/event/live/top100") as resp:
                    data = await resp.json()

                event_id = data["id"]
                close_time = data["aggregate_at"]
                close_time_dt = parser.isoparse(close_time)
                close_time_utc8 = parser.isoparse(close_time).astimezone(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S')
                event_name = data["name"]
            
            if self.current_event_close_time is None or close_time_dt != self.current_event_close_time:
                try:
                    # 將結束時間寫入 event_rank_history.json
                    history_path = os.path.join(BOT_DIR, "event_rank_history.json")
                    if os.path.exists(history_path):
                        with open(history_path, "r", encoding="utf-8") as hf:
                            j = json.load(hf)
                    else:
                        j = {}
                    j["close_time"] = close_time_utc8
                    with open(history_path, "w", encoding="utf-8") as hf:
                        json.dump(j, hf, ensure_ascii=False, indent=2)
                    self.current_event_close_time = close_time_dt
                    self.rank_history.clear()
                except Exception:
                    pass
            players = data["player_top_100_rankings"]

            if "-" in rank_num_str:
                start, end = map(int, rank_num_str.split("-"))
                target_ranks = list(range(start, end + 1))
            else:
                target_ranks = [int(rank_num_str)]

            results = []
            for target_rank in target_ranks:
                for p in players:
                    if p["rank"] == target_rank:
                        results.append(p)
                        break
            
            if not results:
                await ctx.send("找不到此名次範圍資料")
                return

            embed = discord.Embed(
                title=f"{event_name}",
                color=discord.Color.from_rgb(int(0.945 * 255), int(0.906 * 255), int(0.486 * 255)),
            )

            for p in results:
                p_2 = next((x for x in players if x["rank"] == p["rank"] + 1), None)

                name = p["name"]
                score = p['score']
                last_score = p["last_score"]
                time = parser.isoparse(p["last_played_at"]).astimezone(timezone(timedelta(hours=8)))

                one_hour = p["last_1h_stats"]
                count = one_hour["count"]
                speed = one_hour['speed']
                average = one_hour["average"]

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
            embed.set_footer(text=f"活動期數：{event_id}\n結束時間：{close_time_utc8} (UTC+8)")
            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.reply(f'查詢範圍太廣，請重新輸入查詢範圍')

    @commands.command()
    async def rh(self, ctx, rank_num):
        try:
            rank_num_int = int(rank_num)
            if rank_num_int not in self.rank_history or not self.rank_history[rank_num_int]:
                await ctx.send(f"暫時找不到該名次 {rank_num_int} 的紀錄，請稍後再試或使用&rank指令更新資料")
                return

            # 取得該名次的最新資料以顯示名稱
            # 先嘗試以已知的活動結束時間判定是否需要向 API 請求；只有在無法判定或仍在活動期間才會請求
            if not self.current_event_close_time:
                self._load_saved_close_time()
            if not self._is_event_active():
                await ctx.send("此指令僅可在活動期間使用，目前沒有進行中的活動")
                return

            async with self.session.get("https://api.hisekai.org/tw/event/live/top100") as resp:
                data = await resp.json()
            # 取得並更新活動結束時間（若 API 有新資料）
            try:
                close_time = data.get("aggregate_at")
                if close_time:
                    try:
                        self.current_event_close_time = parser.isoparse(close_time)
                    except Exception:
                        self.current_event_close_time = None
                self.current_event_name = data.get("name")
            except Exception:
                pass
            players = data.get("player_top_100_rankings", [])
            score = next((p["score"] for p in players if p["rank"] == rank_num_int), None)
            if score is None:
                await ctx.send(f"找不到名次 {rank_num_int} 的資料")
                return
            name = next((p["name"] for p in players if p["rank"] == rank_num_int), f"名次 {rank_num_int}")
            # 固定取最近 11 筆樣本，若不足 11 筆就顯示現有資料
            history = list(self.rank_history[rank_num_int])[-11:]

            embed = discord.Embed(
                title=f"{name} 近十次增加pt",
                color=discord.Color.from_rgb(int(0.945 * 255), int(0.906 * 255), int(0.486 * 255)),
                description=f"當前分數：{score:,}"
            )

            if len(history) < 2:
                latest = history[-1]
                embed.add_field(
                    name="當前紀錄",
                    value=f"分數：{latest['score']:,}\n時間：{latest['time']}\n可計算的分差不足 1 筆",
                    inline=False,
                )
            else:
                for index in range(1, len(history)):
                    previous_record = history[index - 1]
                    current_record = history[index]

                    score_diff = current_record["score"] - previous_record["score"]
                    diff_text = f"{score_diff:+,}"

                    embed.add_field(
                        name=f"{index}",
                        value=(
                        f"{diff_text}\n"
                        f"時間：{current_record['time']}\n"
                        ),
                        inline=False,
                    )

            embed.set_footer(text="資料來源: Hi Sekai")
            await ctx.send(embed=embed)

        except ValueError:
            await ctx.send("請輸入有效的名次數字")
        except Exception as e:
            await ctx.send(f"查詢歷史紀錄時發生錯誤: {e}")

    @commands.command()
    async def rct(self, ctx):
        """手動重新載入活動結束時間，僅在活動期間有效。"""
        async with ctx.typing():
                async with self.session.get("https://api.hisekai.org/tw/event/live/top100") as resp:
                    data = await resp.json()
        data_close_time = data.get("aggregate_at")
        if data_close_time:
            try:
                self.current_event_close_time = parser.isoparse(data_close_time)
            except Exception:
                self.current_event_close_time = None
        #寫入.json檔案
        try:
            close_time_utc8 = self.current_event_close_time.astimezone(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S')
            # 將結束時間寫入 event_rank_history.json
            history_path = os.path.join(BOT_DIR, "event_rank_history.json")
            if os.path.exists(history_path):
                with open(history_path, "r", encoding="utf-8") as hf:
                    j = json.load(hf)
            else:
                j = {}
            j["close_time"] = close_time_utc8
            with open(history_path, "w", encoding="utf-8") as hf:
                json.dump(j, hf, ensure_ascii=False, indent=2)
        except Exception:
            pass
        #清除所有排名原資料
        self.rank_history.clear()
        # 重新載入本地儲存的結束時間，若 API 無法提供或已結束則使用本地資料
        await ctx.send(f"已重新載入活動結束時間: {self.current_event_close_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")

async def setup(bot):
    await bot.add_cog(PJSKEvent(bot)) 