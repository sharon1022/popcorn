import time, discord, datetime
from discord.ext import tasks, commands
import pygsheets
from datetime import datetime, timezone, timedelta, time
import pandas as pd
import matplotlib.pyplot as plt
from pandas.plotting import table
from PIL import Image, ImageDraw
from matplotlib.font_manager import FontProperties, findSystemFonts
import matplotlib.colors as mcolors
import asyncio
from gtts import gTTS
import os
from matplotlib.table import Table
import matplotlib.image as mpimg
import re


gc = pygsheets.authorize(service_file='/2TB/sharon/心願音符/python.json')

car_server_id = 1036267533428326540 #leon私車
my_server_id = 1018898779635720293
sht1 = gc.open_by_url('https://docs.google.com/spreadsheets/d/11IbwKM0FvjWMoZZ7Ha4MKaYaTUoIPU25slAallFg6OM/') #目前是leon班表，開活記得換
wks = sht1.worksheet_by_title('班表名稱')

def set_chinese_font():
    # 優先使用微軟正黑體 msjh.ttc，若不存在再 fallback
    font_paths = [
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-TC-Regular.otf",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/truetype/arphic/ukai.ttc",
        "/usr/share/fonts/truetype/arphic/uming.ttc",
    ]
    for path in font_paths:
        if os.path.exists(path):
            return FontProperties(fname=path)
    # 若都找不到，回傳系統預設
    return FontProperties()

def get_bg_colors(sheet, start, end):
    cells = sheet.range(start + ":" + end, returnas='cells')
    colors = []
    for row in cells:
        row_colors = []
        for cell in row:
            if cell.color is not None:
                red = cell.color[0] if cell.color[0] is not None else 1
                green = cell.color[1] if cell.color[1] is not None else 1
                blue = cell.color[2] if cell.color[2] is not None else 1
                row_colors.append((red, green, blue))
            else:
                row_colors.append((1, 1, 1))  # 默认白色背景
        colors.append(row_colors)
    return colors

def process_image(date, date2, column_ranges):
    date_sht = sht1.worksheet_by_title(date)

    data1 = date_sht.get_values(column_ranges[0], column_ranges[1])  # A1:F1
    data2 = date_sht.get_values(column_ranges[2], column_ranges[3])  # A8:F33

    if not data1:
        data1 = [[''] * 6]
    if not data2:
        data2 = [[''] * 6]

    if date2:
        date_sht2 = sht1.worksheet_by_title(date2)
        data3 = date_sht2.get_values(column_ranges[4], column_ranges[5])  # A1:F1
        if not data3:
            data3 = [[''] * 6]
        combined_data = data1 + data2 + data3
    else:
        combined_data = data1 + data2

    headers = combined_data[0]
    rows = combined_data[1:]
    df = pd.DataFrame(rows, columns=headers)

    font = set_chinese_font()
    plt.rcParams['font.sans-serif'] = [font.get_name()]
    plt.rcParams['axes.unicode_minus'] = False

    fig, ax = plt.subplots(figsize=(7, 4))
    fig.patch.set_alpha(0)   # 透明背景
    ax.patch.set_alpha(0)
    ax.axis('tight')
    ax.axis('off')

    col_widths = [1 / len(df.columns)] * len(df.columns)
    tbl = table(ax, df, loc='center', cellLoc='center', colWidths=col_widths)
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(17)
    tbl.scale(1.7, 2.0)

    colors1 = get_bg_colors(date_sht, column_ranges[0], column_ranges[1])
    colors2 = get_bg_colors(date_sht, column_ranges[2], column_ranges[3])
    if date2:
        colors3 = get_bg_colors(date_sht2, column_ranges[4], column_ranges[5])
        combined_colors = colors1 + colors2 + colors3
    else:
        combined_colors = colors1 + colors2

    while len(combined_colors) < len(df):
        combined_colors.append([(1, 1, 1)] * len(df.columns))

    for (i, j), cell in tbl.get_celld().items():
        if j == -1:
            cell.set_text_props(text='')
            cell.set_facecolor((0, 0, 0, 0))  # 透明背景
        else:
            color = combined_colors[i][j] if i < len(combined_colors) and j < len(combined_colors[i]) else (1, 1, 1)
            if color == (1, 1, 1):  # 白色背景改透明
                cell.set_facecolor((0, 0, 0, 0))
            else:
                cell_color = mcolors.to_rgba(color, alpha=0.3)  # 螢光筆透明度
                cell.set_facecolor(cell_color)

    output_image_path = 'output_image.png'
    plt.savefig(output_image_path, bbox_inches='tight', pad_inches=0.05, dpi=300, transparent=True)
    plt.close(fig)

    return output_image_path



class Register(commands.Cog):
    every_hour_time = [
        time(hour=t, minute=50, tzinfo=timezone(timedelta(hours=8)))
        for t in range(24)
    ]
    every_hour_L1 = [
        time(hour=t, minute=58, tzinfo=timezone(timedelta(hours=8)))
        for t in range(24)
    ]
    def __init__(self, bot):
        self.bot = bot
        self.reminder.start()
        #self.everyday.start()
        #self.L1.start()

    @commands.command()
    async def reg(self, ctx, name, sk): #登記原推
        user_id = ctx.author.id
        id_cell = wks.find(f'{user_id}')
        try:
            if ctx.guild.id in [car_server_id,my_server_id]:
                if id_cell:
                    await ctx.reply('已登記過資料，請勿重複登記')
                else:        
                    values = [f'{name}', f'<@{user_id}>', f'{sk}']
                    await ctx.message.add_reaction('<a:emoji_40:1305829128955760680>')
                    wks.append_table([values])
        except Exception as e:
            print(e)

    @commands.command()
    async def regs6(self, ctx, str1, str2): #登記S6
        try:
            if ctx.guild.id in [car_server_id,my_server_id]:
                user_id = ctx.author.id
                id_cell = wks.find(f'{user_id}')
                if id_cell:
                    rows = [cell.row for cell in id_cell]
                    row = rows[0]
                    imfoS6 = wks.cell(f'D{row}').value
                    if imfoS6 == '':
                        sk = str1
                        po = str2
                        values = [f'{sk}', f'{po}']
                        wks.update_values(f'D{row}', [values])
                        await ctx.message.add_reaction('<a:emoji_40:1305829128955760680>')
                    else:
                        await ctx.reply('已登記過S6資料，請勿重複登記')
                else:
                    await ctx.reply('尚未登記原推資料，麻煩請先登記再使用此指令')
        except Exception as e:
            print(e)

    @commands.Cog.listener()
    async def on_message(self, message): #報班&砍班
        try:

            now = datetime.now(timezone(timedelta(hours=8)))
            today = now.date()
            yesterday = today - timedelta(days=1)
            tomorrow = today + timedelta(days=1)

            pattern = re.compile(r'^(1[0-2]|0?[1-9])/(3[01]|[12][0-9]|0?[1-9])\s(2[0-4]|1[0-9]|0?[0-9])-(2[0-4]|1[0-9]|0?[0-9])$')
            if message.author == self.bot.user:
                return
            if message.channel.id == 1301503222430830663: #leon
                if message.content.startswith('-'): #砍班
                    text = message.content[1:]
                    if not pattern.match(text.strip()):
                        return 
                    parts1 = text.split(' ') 
                    date = parts1[0]
                    
                    # 將輸入的日期字串轉換為 date 物件進行比較
                    try:
                        month, day = map(int, date.split('/'))
                        input_date = datetime(year=now.year, month=month, day=day).date()
                    except ValueError:
                        await message.reply("日期格式錯誤")
                        return
                    
                    date_sht = sht1.worksheet_by_title(f'{date}')

                    # 禁止昨天
                    if input_date == today:
                        await message.reply("今日班表已發布，不可砍班")
                        return
                    
                    # 禁止今天8點前的班
                    if input_date == tomorrow:
                        parts2 = parts1[1].split('-')
                        if int(parts2[0]) <= 8 and int(parts2[1]) <= 8:
                            await message.reply("今日班表已發布，不可砍8點前的班")
                            return

                    time = parts1[1].split('-')
                    time2_int = int(time[1])
                    k_time2 = time2_int + 1
                    time1_int = int(time[0])
                    k_time1 = time1_int + 2

                    user_id = message.author.id
                    id_cell = wks.find(f'{user_id}')
                    user_cell = id_cell[0]
                    row = user_cell.row
                    imfo = wks.cell(f'A{row}').value
                    cells = date_sht.range(f'B{k_time1}:Z{k_time2}')
                    for cell in cells:
                        for name in cell:
                            if name.value == imfo:
                                name.value = ''
                    await message.add_reaction('<:emoji_28:1308760446102142997>')

            if message.channel.id == 1301502986551296010: #leon報班頻道
                if pattern.match(message.content.strip()): #報班
                    user_id = message.author.id
                    id_cell = wks.find(f'{user_id}')
                    if id_cell:
                        rows = [cell.row for cell in id_cell]
                        row = rows[0]
                        name = wks.cell(f'A{row}').value
                        parts1 = message.content.split(' ')
                        date = parts1[0]

                        # 將輸入的日期字串轉換為 date 物件進行比較
                        try:
                            month, day = map(int, date.split('/'))
                            input_date = datetime(year=now.year, month=month, day=day).date()
                        except ValueError:
                            await message.reply("日期格式錯誤")
                            return

                        # 禁止今天
                        if input_date == today:
                            await message.reply("今日班表已發布，不可報班")
                            return

                        # 禁止明天8點前的班
                        if input_date == tomorrow:
                            parts2 = parts1[1].split('-')
                            if int(parts2[0]) <= 8 and int(parts2[1]) <= 8:
                                await message.reply("今日8-32班表已發布，不可報8點前的班")
                                return

                        parts2 = parts1[1].split('-')
                        time2_int = int(parts2[1])
                        time1_int = int(parts2[0])
                        k_time1 = time1_int + 2
                        k_time2 = time2_int + 1

                        value = [f'{name}']
                        date_sht = sht1.worksheet_by_title(f'{date}')

                        # 取得 A 欄的時間範圍
                        time_values = date_sht.get_values(f'A{k_time1}', f'A{k_time2}')
                        time_values = [t[0] for t in time_values]  # 取出時間字串

                        # 紀錄重複時間
                        duplicate_times = []

                        for row_offset, time_str in enumerate(time_values):  # row_offset: 0-based
                            row = k_time1 + row_offset  # 真正的 row index
                            # 取得 B~Z 欄該列的所有值
                            row_values = date_sht.get_values(f'B{row}', f'Z{row}')
                            row_values = row_values[0] if row_values else []

                            if name in row_values:
                                duplicate_times.append(time_str)

                        if duplicate_times:
                            # 提醒使用者重複
                            duplicate_text = '、'.join(duplicate_times)
                            await message.reply(f'以下時段重複報班：\n**__{duplicate_text}__**\n請調整報班時段<a:emoji_25:1305806356858798090>')
                        else:
                            # 沒重複，填寫資料
                            for col in range(ord('B'), ord('Z') + 1):
                                col_range = f'{chr(col)}{k_time1}:{chr(col)}{k_time2}'
                                values = date_sht.get_values(f'{chr(col)}{k_time1}', f'{chr(col)}{k_time2}')
                                if values == [['']]:
                                    date_sht.update_values(col_range, [value] * (time2_int - time1_int))
                                    await message.add_reaction('<:emoji_28:1308760446102142997>')
                                    return

                    else:
                        await message.reply('尚未登記資料，麻煩請先登記再使用此指令')
            #if message.channel.id == 1420400524083200130:
            #    if pattern.match(message.content.strip()): #S6報班
            #        user_id = message.author.id
            #        id_cell = wks.find(f'{user_id}')
            #        if id_cell:
            #            rows = [cell.row for cell in id_cell]
            #            row = rows[0]
            #            name = wks.cell(f'A{row}').value
            #            parts1 = message.content.split(' ')
            #            date = parts1[0]
#
            #            # 將輸入的日期字串轉換為 date 物件進行比較
            #            try:
            #                month, day = map(int, date.split('/'))
            #                input_date = datetime(year=now.year, month=month, day=day).date()
            #            except ValueError:
            #                await message.reply("日期格式錯誤")
            #                return
#
            #            # 禁止今天
            #            if input_date == today:
            #                await message.reply("今日班表已發布，不可報班")
            #                return
#
            #            # 禁止明天8點前的班
            #            if input_date == tomorrow:
            #                parts2 = parts1[1].split('-')
            #                if int(parts2[0]) <= 8 and int(parts2[1]) <= 8:
            #                    await message.reply("今日8-32班表已發布，不可報8點前的班")
            #                    return
#
            #            parts2 = parts1[1].split('-')
            #            time2_int = int(parts2[1])
            #            time1_int = int(parts2[0])
            #            k_time1 = time1_int + 2
            #            k_time2 = time2_int + 1
#
            #            value = [f'{name}']
            #            date_sht = sht1.worksheet_by_title(f'{date}')
#
            #            # 取得 A 欄的時間範圍
            #            time_values = date_sht.get_values(f'A{k_time1}', f'A{k_time2}')
            #            time_values = [t[0] for t in time_values]  # 取出時間字串
#
            #            # 紀錄重複時間
            #            duplicate_times = []
#
            #            for row_offset, time_str in enumerate(time_values):  # row_offset: 0-based
            #                row = k_time1 + row_offset  # 真正的 row index
            #                # 取得 B~Z 欄該列的所有值
            #                row_values = date_sht.get_values(f'B{row}', f'Z{row}')
            #                row_values = row_values[0] if row_values else []
#
            #                if name in row_values:
            #                    duplicate_times.append(time_str)
#
            #            if duplicate_times:
            #                # 提醒使用者重複
            #                duplicate_text = '、'.join(duplicate_times)
            #                await message.reply(f'以下時段重複報班：\n**__{duplicate_text}__**\n請調整報班時段<a:emoji_25:1305806356858798090>')
            #            else:
            #                # 沒重複，填寫資料
            #                for col in range(ord('B'), ord('Z') + 1):
            #                    col_range = f'{chr(col)}{k_time1}:{chr(col)}{k_time2}'
            #                    values = date_sht.get_values(f'{chr(col)}{k_time1}', f'{chr(col)}{k_time2}')
            #                    if values == [['']]:
            #                        date_sht.update_values(col_range, [value] * (time2_int - time1_int))
            #                        for row in (date_sht.range(f'{chr(col)}{k_time1}:{chr(col)}{k_time2}')):
            #                            for cell in row:
            #                                cell.color = (0.945, 0.906, 0.486)  # 淡黃色
            #                        await message.add_reaction('<:emoji_28:1308760446102142997>')
            #                        return
#
            #        else:
            #            await message.reply('尚未登記資料，麻煩請先登記再使用此指令')
        except Exception as e:
            print(e)
            await message.reply(f'可能輸入有誤，請再輸入一次\n若確認輸入沒錯誤，請@鯛魚')
    
    @commands.command()
    async def vac(self, ctx, date): #查詢缺額
        try:

            now = datetime.now(timezone(timedelta(hours=8)))
            today = now.date()
            tomorrow = today + timedelta(days=1)
            af_tomorrow = today + timedelta(days=2)

            # 解析 MM/DD 或 M/D
            match = re.match(r'^(\d{1,2})/(\d{1,2})$', date)
            if not match:
                await ctx.reply("請輸入以下格式：\n&vac MM/DD\n例如：&vac 9/15")
                return

            month, day = map(int, match.groups())
            try:
                input_date = datetime(year=now.year, month=month, day=day).date()
            except ValueError:
                await ctx.reply("可能輸入有誤，請再輸入一次\n若確認輸入沒錯誤，請@鯛魚")
                return

            # 禁止今天以及今天之前的日期
            if input_date <= today:
                await ctx.reply("今日及之前的班表已發布，不可查詢")
                return

            # 檢查明天的班表查詢限制
            if input_date == tomorrow:
                if now.hour >= 22:
                    await ctx.reply("明日8-32班表將發布，不可查詢")
                    return

            if ctx.guild.id in [car_server_id,my_server_id]:
                date_sht = sht1.worksheet_by_title(f'{date}')
                data = date_sht.get_all_values()

                # 過濾掉空白行
                data = [row for row in data if any(cell.strip() for cell in row)]

                # 如果是明天且22點前，過濾掉8點前的資料
                if input_date == tomorrow and now.hour <= 22 and len(data) > 10:
                    data = [data[0]] + data[9:]  # 保留欄位標題 row[0]，刪掉 row[1]-row[9]
                elif input_date == af_tomorrow and now.hour >= 22 and len(data) > 10:
                    data = [data[0]] + data[9:]  # 保留欄位標題 row[0]，刪掉 row[1]-row[9]

                # 轉換成 DataFrame
                df = pd.DataFrame(data[1:], columns=data[0])

                # 過濾掉空白欄
                df = df.loc[:, (df != '').any(axis=0)]

                # 設定字體
                font = set_chinese_font()
                plt.rcParams['font.sans-serif'] = [font.get_name()]
                plt.rcParams['axes.unicode_minus'] = False

                # 繪製表格
                fig, ax = plt.subplots(figsize=(10, 4))  # 調整大小
                ax.axis('tight')
                ax.axis('off')

                # 在圖片上繪製表格
                tbl = table(ax, df, loc='center', cellLoc='center', colWidths=[0.1] * len(df.columns))
                tbl.auto_set_font_size(False)
                tbl.set_fontsize(17)
                tbl.scale(1.7, 2.0)
                
                for key, cell in tbl.get_celld().items():
                    if key[1] == -1:
                        cell.visible_edges = 'open'
                        cell.set_text_props(text='')

                # 儲存圖片
                image_path = 'vac_output_image.png'
                plt.savefig(image_path, bbox_inches='tight', pad_inches=0.05, dpi=300)
                plt.close(fig)

                with open(image_path, 'rb') as f:
                    picture = discord.File(f)
                    await ctx.send(file=picture)
        except Exception as e:
            print(e)
            await ctx.reply('可能輸入有誤，請再輸入一次\n若確認輸入沒錯誤，請@鯛魚')
            
    @commands.command()
    async def scd(self, ctx, date, date2=None):
        try:
            if ctx.guild.id in [car_server_id, my_server_id]:
                if date2:
                    image_path = process_image(date, date2, ('A1', 'F1', 'A10', 'F25', 'A1', 'F9'))
                else:
                    image_path = process_image(date, None, ('A1', 'F1', 'A10', 'F25', 'A1', 'F9'))

            # 開啟背景
            background = Image.open('/2TB/sharon/popcorn/output_image.png').convert("RGBA")

            # 讀取角色圖片 (確保有透明背景)
            overlay = Image.open('/home/sharon/public_html/character.png').convert("RGBA")

            # 調整角色大小
            bg_width, bg_height = background.size
            overlay_width, overlay_height = overlay.size
            new_height = int(bg_width * 0.8)
            new_width = int(overlay_width * (new_height / overlay_height))
            overlay = overlay.resize((new_width, new_height), Image.Resampling.LANCZOS)

            # 設定透明度
            r, g, b, a = overlay.split()
            alpha = 1
            a = Image.new("L", overlay.size, alpha)
            overlay = Image.merge("RGBA", (r, g, b, a))

            # === 角色先貼上去（在下層） ===
            y_offset = 700 if date2 else 300
            position = ((bg_width - overlay.width) // 2, y_offset)
            background.alpha_composite(overlay, position)
            background.save('/2TB/sharon/popcorn/output_image.png', 'png')

            # 儲存結果
            background = background.convert("RGB")
            background.save('/2TB/sharon/popcorn/output_image.jpg', 'JPEG')
            image_path = '/2TB/sharon/popcorn/output_image.jpg'
            with open(image_path, 'rb') as f:
                picture1 = discord.File(f)
                await ctx.send(file=picture1)
        except Exception as e:
            print(e)
            await ctx.reply(f'{e}')

    @commands.command()
    async def che(self,ctx):
        try:
            if ctx.guild.id in [car_server_id,my_server_id]:
                def get_member_info(value):
                    df = pd.DataFrame(wks.get_all_records())  # 整張表讀進來
                    if df.empty or '名稱' not in df.columns:
                        return None
                    target = str(value).strip()
                    row = df[df['名稱'].astype(str).str.strip() == target]
                    if not row.empty:
                        return row.iloc[0]['discord ID']
                    return None
                
                ctime = datetime.now(timezone(timedelta(hours=8)))
                date = ctime.strftime('%-m/%-d')
                date_sht = sht1.worksheet_by_title(date)
                row = ctime.strftime('%H')
                k_time = int(row)+2
                members = [date_sht.get_value(f'{chr(ord("C") + i)}{k_time}') for i in range(4)]
                imfos = [get_member_info(member) for member in members if member]
                if imfos:
                    await ctx.send(' '.join(imfos) + '\n目前周回速度不理想，請大家回報結算前的數字(?/5)，若為5/5再麻煩協助重啟遊戲')
        except Exception as e:
            print(e)
            await ctx.reply(f'可能輸入有誤，請再輸入一次\n若確認輸入沒錯誤，請@鯛魚')

    @commands.command()
    async def sub(self,ctx,date,time):
        try:
            if ctx.guild.id in [car_server_id,my_server_id]:
                def get_member_info(value):
                    df = pd.DataFrame(wks.get_all_records())  # 整張表讀進來
                    if df.empty or '名稱' not in df.columns:
                        return None
                    target = str(value).strip()
                    row = df[df['名稱'].astype(str).str.strip() == target]
                    if not row.empty:
                        return row.iloc[0]['discord ID']
                    return None
                
                times = time.split('-')
                k_time = int(times[0]) + 2

                date_sht = sht1.worksheet_by_title(date)
                members = [date_sht.get_value(f'{chr(ord("G") + i)}{k_time}') for i in range(19)]
                imfos = [get_member_info(member) for member in members if member]
                if imfos:
                    await ctx.send(f'{date} {time}\n'+' '.join(imfos) + '\n為此時段的候補，請求臨時協助。')
                else:
                    await ctx.reply('此時段無候補，請自行尋求協助<a:emoji_27:1305806384478289930>')
        except Exception as e:
            print(e)
            await ctx.reply(f'可能輸入有誤，請再輸入一次\n若確認輸入沒錯誤，請@鯛魚')

    

    @tasks.loop(time=every_hour_time)
    async def reminder(self): #提醒上車
        channel_id_1 = 1481344372560891975  #leon家的上車提醒頻道
        channel_1 = self.bot.get_channel(channel_id_1)
        
        try:
            def get_member_info(value):
                df = pd.DataFrame(wks.get_all_records())  # 整張表讀進來
                if df.empty or '名稱' not in df.columns:
                    return None
                target = str(value).strip()
                row = df[df['名稱'].astype(str).str.strip() == target]
                if not row.empty:
                    return row.iloc[0]['discord ID']
                return None

            ctime = datetime.now(timezone(timedelta(hours=8)))
            row = ctime.strftime('%H')
            
            ttime = int((ctime + timedelta(hours=1)).strftime('%H'))
            ttime_2 = int((ctime + timedelta(hours=2)).strftime('%H'))
            if ttime == 0:
                k_time = 2
                ctime1d = ctime + timedelta(days=1)
                date = ctime1d.strftime('%-m/%-d')
                date_sht = sht1.worksheet_by_title(date)
            else:
                k_time = int(row)+3
                date = ctime.strftime('%-m/%-d')
                date_sht = sht1.worksheet_by_title(date)

            if date_sht:
                P1_1 = date_sht.cell(f'B{k_time}').value
                if P1_1 != '':
                    members = [date_sht.get_value(f'{chr(ord("B") + i)}{k_time}') for i in range(5)]
                    imfos = [get_member_info(member) for member in members if member]
                    imfos = [info for info in imfos if info is not None]
                    message = await channel_1.send(
                        content=f'{date} {ttime}-{ttime_2} \n' + ' '.join(imfos) + '\n# 請於10分鐘後上車，並請確認已換上推隊、關火、鎖蝦後按下表符，S6推者請不要站P4、5'
                    )
                    await message.add_reaction('<a:usagi:1297150428043284490>')

        except Exception as e:
            print(e)


    #@tasks.loop(time=time(hour=22,minute=0,second=0,tzinfo=timezone(timedelta(hours = 8))))
    #async def everyday(self): #報班截止拉線
    #    channel1_id = 1353669243660533810 
    #    channel1 = self.bot.get_channel(channel1_id)
    #    channel = self.bot.get_channel(1389886916228419664) #我家
    #    ctime = datetime.today()
    #    ttime = ctime + timedelta(days=1)
    #    ttime2 = ctime + timedelta(days=2)
    #    date = ttime.strftime('%Y/%m/%d')
    #    date2 = ttime2.strftime('%Y/%m/%d')
    #    embed = discord.Embed(
    #        title = f'已截止報{date} 0-24、{date2} 0-8的班',
    #        description = f'除缺人外報班一概不受理\n稍後班表將公布在當日班表頻道',
    #        color = discord.Color.from_str("#FFDD44")
    #    )
    #    await channel1.send(embed=embed)
    
    #@tasks.loop(time=every_hour_L1)
    #async def L1(self): #L1
    #    ctime = datetime.now(timezone(timedelta(hours=8)))
    #    date = ctime.strftime('%-m/%-d')
    #    hour = ctime.strftime('%H')
    #    c_hour = int(hour) + 1
    #    date_sht = sht1.worksheet_by_title(date)
    #    if date_sht: 
    #        P1_1 = date_sht.cell(f'B{c_hour}').value
    #        if P1_1 != '':
    #            channel1_id = 1136689631644106856
    #            channel1 = self.bot.get_channel(channel1_id)
    #            await channel1.send('L1，請下一小的推者準備撞房\n本小結束的推者請記得跳車<:emoji_4:1250109312609685624>')

    def cog_unload(self):
        self.reminder.cancel()
        #self.everyday.cancel()
        #self.L1.cancel()

async def setup(bot:commands.bot):
    await bot.add_cog(Register(bot))