import disnake
from disnake.ext import commands
import sqlite3
import asyncio
import time
import datetime
import aiohttp

bot = commands.Bot(command_prefix="+", help_command=None, intents=disnake.Intents.all())

# Создаем подключение к базе данных
conn = sqlite3.connect('reputation.db', check_same_thread=False)
cursor = conn.cursor()

# Проверяем существование таблицы, если её нет, создаем её
cursor.execute('''
    CREATE TABLE IF NOT EXISTS reputation (
        user_id INTEGER PRIMARY KEY,
        reputation INTEGER,
        last_used INTEGER
    )
''')

# Убираем conn.commit() после создания таблицы

async def update_activity():
    await bot.wait_until_ready()

    ip = "194.147.90.86"
    port = 25544

    while not bot.is_closed():
        server = await get_server_info(ip, port)
        if server:
            player_count = server["attributes"]["players"]
            max_players = server["attributes"]["maxPlayers"]
            activity = disnake.Activity(
                type=disnake.ActivityType.watching,
                name=f"{player_count}/{max_players} игроков"
            )
            await bot.change_presence(activity=activity)
        await asyncio.sleep(300)  # Обновление активности каждые 5 минут

bot.loop.create_task(update_activity())

# Остальной код остается без изменений

@bot.command()
async def rep(ctx, *, args: str = ""):
        if ctx.channel.id != 967445056250322964:
        return
    
    if not args:
        embed = disnake.Embed(
            title="Ошибка",
            description="Вы не упомянули пользователя, которому хотите дать репутацию, или не указали комментарий.",
            color=disnake.Color.red()
        )
        await ctx.send(embed=embed)
        return

    member = ctx.author
    if ctx.message.mentions:
        member = ctx.message.mentions[0]

    if member.id == ctx.author.id:
        embed = disnake.Embed(
            title="Ошибка",
            description="Вы не можете дать репутацию самому себе!",
            color=disnake.Color.red()
        )
        await ctx.send(embed=embed)
        return

    # Получаем текущую репутацию пользователя из базы данных
    cursor.execute("SELECT reputation FROM reputation WHERE user_id = ?", (member.id,))
    result = cursor.fetchone()
    current_reputation = result[0] if result else 0

    # Проверяем, была ли команда уже использована в последний час
    cursor.execute("SELECT last_used FROM reputation WHERE user_id = ?", (ctx.author.id,))
    result = cursor.fetchone()
    last_used = result[0] if result else 0

    if time.time() - last_used < 3600:
        embed = disnake.Embed(
            title="Ошибка",
            description=f"Вы уже использовали команду +rep. Подождите еще {int(3600 - (time.time() - last_used))} секунд.",
            color=disnake.Color.red()
        )
        await ctx.send(embed=embed)
        return

    # Увеличиваем репутацию пользователя на 1
    cursor.execute("INSERT OR IGNORE INTO reputation (user_id, reputation, last_used) VALUES (?, 0, ?)", (member.id, int(time.time())))
    cursor.execute("UPDATE reputation SET reputation = reputation + ?, last_used = ? WHERE user_id = ?", (1, int(time.time()), member.id))
    conn.commit()

    # Удаление упоминаний из комментария
    cleaned_args = args
    for mention in ctx.message.mentions:
        cleaned_args = cleaned_args.replace(mention.mention, "")

    comment = f"Комментарий: {cleaned_args.strip()}"
    embed = disnake.Embed(
        title="Репутация",
        description=f'📈 Пользователь **{ctx.author.mention}** поблагодарил пользователя **{member.mention}**\nВсего у пользователя репутации: **{current_reputation + 1}**\n{comment}',
        color=disnake.Color.green()
    )
    await ctx.send(embed=embed)

    # Удаляем оригинальное сообщение отправителя
    await ctx.message.delete()

    
@bot.command()
async def unrep(ctx, *, args: str = ""):
        # Проверяем, что команда вызвана в нужном канале
    if ctx.channel.id != 967445056250322964:
        return
        
    if not args:
        embed = disnake.Embed(
            title="Ошибка",
            description="Вы не упомянули пользователя, у которого хотите убрать репутацию, или не указали комментарий.",
            color=disnake.Color.red()
        )
        await ctx.send(embed=embed)
        return

    member = ctx.author
    if ctx.message.mentions:
        member = ctx.message.mentions[0]

    if member.id == ctx.author.id:
        embed = disnake.Embed(
            title="Ошибка",
            description="Вы не можете убрать репутацию самому себе!",
            color=disnake.Color.red()
        )
        await ctx.send(embed=embed)
        return

    # Получаем текущую репутацию пользователя из базы данных
    cursor.execute("SELECT reputation FROM reputation WHERE user_id = ?", (member.id,))
    result = cursor.fetchone()
    current_reputation = result[0] if result else 0

    # Проверяем, была ли команда уже использована в последний час
    cursor.execute("SELECT last_used FROM reputation WHERE user_id = ?", (ctx.author.id,))
    result = cursor.fetchone()
    last_used = result[0] if result else 0

    if time.time() - last_used < 3600:
        embed = disnake.Embed(
            title="Ошибка",
            description=f"Вы уже использовали команду unrep. Подождите еще {int(3600 - (time.time() - last_used))} секунд.",
            color=disnake.Color.red()
        )
        await ctx.send(embed=embed)
        return

    # Уменьшаем репутацию пользователя на 1
    cursor.execute("INSERT OR IGNORE INTO reputation (user_id, reputation, last_used) VALUES (?, 0, ?)", (member.id, int(time.time())))
    cursor.execute("UPDATE reputation SET reputation = reputation - ?, last_used = ? WHERE user_id = ?", (1, int(time.time()), member.id))
    conn.commit()

    # Создаем комментарий
    cleaned_args = args
    for mention in ctx.message.mentions:
        cleaned_args = cleaned_args.replace(mention.mention, "")

    comment = f"Комментарий: {cleaned_args.strip()}"
    embed = disnake.Embed(
        title="Репутация",
        description=f'📉 Пользователь **{ctx.author.mention}** убрал одну репутацию у пользователя **{member.mention}**\nТекущая репутация пользователя: **{current_reputation - 1}**.\n{comment}',
        color=disnake.Color.orange()
    )
    await ctx.send(embed=embed)

    # Удаляем оригинальное сообщение отправителя
    await ctx.message.delete()


@bot.command()
async def setrep(ctx, member: disnake.Member = None, amount: int = 0):
    # Проверяем, что команда вызвана в нужном канале
    if ctx.channel.id != 967445056250322964:
        return

    # Проверяем роли у пользователя
    allowed_roles = [967112931735126036, 956192778134650920, 358551967838109698]  # Замените ID ролей на свои
    user_roles = [role.id for role in ctx.author.roles]

    if not any(role_id in user_roles for role_id in allowed_roles):
        embed = disnake.Embed(
            title="Ошибка",
            description="У вас нет разрешения на использование этой команды.",
            color=disnake.Color.red()
        )
        await ctx.send(embed=embed)
        return

    if member is None:
        embed = disnake.Embed(
            title="Ошибка",
            description="Вы не упомянули пользователя, у которого хотите установить репутацию.",
            color=disnake.Color.red()
        )
        await ctx.send(embed=embed)
        return

    sender = ctx.author
    if member.id == sender.id:
        embed = disnake.Embed(
            title="Ошибка",
            description="Вы не можете устанавливать репутацию самому себе!",
            color=disnake.Color.red()
        )
        await ctx.send(embed=embed)
        return

    # Устанавливаем новую репутацию пользователя
    cursor.execute("INSERT OR IGNORE INTO reputation (user_id, reputation, last_used) VALUES (?, 0, ?)", (member.id, int(time.time())))
    cursor.execute("UPDATE reputation SET reputation = ?, last_used = ? WHERE user_id = ?", (amount, int(time.time()), member.id))
    conn.commit()

    embed = disnake.Embed(
        title="Репутация",
        description=f'📊 Пользователь **{sender.mention}** установил репутацию **{amount}** для пользователя **{member.mention}**.',
        color=disnake.Color.red()
    )
    await ctx.send(embed=embed)

async def get_server_info(ip, port):
    url = f"https://api.battlemetrics.com/servers?filter[game]=unturned&filter[search]={ip}:{port}"
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data = await response.json()
            if data.get("data"):
                server = data["data"][0]
                return server
            else:
                return None

@bot.slash_command()
async def online(ctx):
    """Получить количество онлайна на сервере"""
    ip = "194.147.90.86"
    port = 25544

    server = await get_server_info(ip, port)

    if server:
        attributes = server["attributes"]
        player_count = attributes["players"]
        max_players = attributes["maxPlayers"]

        embed = disnake.Embed(
            title=f"Server Status - DWS WAR RP",
            description=f"Online Players: {player_count}/{max_players}",
            color=disnake.Color.green()
        )

        await ctx.send(embed=embed)
    else:
        await ctx.send("The server was not found.")
        
@bot.slash_command()
async def players(ctx):
    """Список игроков в онлайне"""
    ip = "194.147.90.86"
    port = 25544

    response = await aiohttp.ClientSession().get(f"https://api.battlemetrics.com/servers?filter[game]=unturned&filter[search]={ip}:{port}")
    data = await response.json()

    if "data" in data and len(data["data"]) > 0:
        server_id = data["data"][0]["id"]
        players_response = await aiohttp.ClientSession().get(f"https://api.battlemetrics.com/players?filter[servers]={server_id}&filter[online]=true")
        players_data = await players_response.json()

        if "data" in players_data and len(players_data["data"]) > 0:
            players = players_data["data"]
            player_list = [player["attributes"]["name"] for player in players]

            # Разбиение списка игроков на группы по 20
            player_groups = [player_list[i:i + 20] for i in range(0, len(player_list), 20)]

            for group in player_groups:
                player_names = "\n".join(group)
                await ctx.send(f"Players Online - DWS WARP RP:\n{player_names}")
        else:
            await ctx.send("No players online.")
    else:
        await ctx.send("Server not found.")
  
@bot.command()
async def rating(ctx, member: disnake.Member):
    # Получаем текущую репутацию пользователя из базы данных
    cursor.execute("SELECT reputation FROM reputation WHERE user_id = ?", (member.id,))
    result = cursor.fetchone()
    current_reputation = result[0] if result else 0

    embed = disnake.Embed(
        title="Репутация",
        description=f"У пользователя {member.mention} репутация: {current_reputation}",
        color=disnake.Color.blue()
    )
    await ctx.send(embed=embed)

bot.run("MTEwOTkxMDczMTgwNzI2ODg2NQ.Go-fNw.JAViLdmfINg-d3xXvi_810tSbB72Jm8gJRSv28")
