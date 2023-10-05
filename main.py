import disnake
from disnake.ext import commands
import sqlite3
import asyncio
import time
import datetime
import discord 
import aiohttp

bot = commands.Bot(command_prefix="+", help_command=None, intents=disnake.Intents.all())

# Создаем подключение к базе данных
conn = sqlite3.connect('reputation.db', check_same_thread=False)
cursor = conn.cursor()
allowed_channels = [967445056250322964, 1120359666535383040]

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

@bot.event
async def on_message(message):
    # Проверяем, что сообщение не отправлено ботом, чтобы избежать зацикливания
    if message.author.bot:
        return

    allowed_channels = [967445056250322964, 1120359666535383040]

    # Проверяем, является ли сообщение командой
    ctx = await bot.get_context(message)

    if message.channel.id in allowed_channels:
        if message.content.startswith('-rep'):
            # Разбиваем сообщение на части по пробелу
            parts = message.content.split()
            if len(parts) >= 2:
                # Получаем упоминание пользователя из сообщения
                user_mention = parts[1]
                # Пробуем получить пользователя из упоминания
                member = discord.utils.get(message.guild.members, mention=user_mention)
                if member and member.id != message.author.id:
                    # Выполняем действия как в команде +unrep
                    # Уменьшаем репутацию пользователя на 1
                    cursor.execute("INSERT OR IGNORE INTO reputation (user_id, reputation, last_used) VALUES (?, 0, ?)", (member.id, int(time.time())))
                    cursor.execute("UPDATE reputation SET reputation = reputation - ?, last_used = ? WHERE user_id = ?", (1, int(time.time()), member.id))
                    conn.commit()
                    # Добавляем реакцию ✅ под сообщением пользователя
                    await message.add_reaction('✅')
        else:
            await bot.invoke(ctx)  # Если сообщение - это команда, обрабатываем его

    # Обработка команды, если сообщение начинается с префикса '/'
    if message.content.startswith('/'):
        await bot.process_commands(message)

@bot.slash_command()
async def top(ctx):
    """Получить топ 10 пользователей с наибольшим рейтингом"""
    # Выполняем SQL-запрос для получения топ-10 пользователей по рейтингу
    cursor.execute("SELECT user_id, reputation FROM reputation ORDER BY reputation DESC LIMIT 10")
    top_users = cursor.fetchall()

    if not top_users:
        await ctx.send("На данный момент еще нет пользователей с рейтингом.")
        return

    # Создаем сообщение с топ-10 пользователями
    embed = disnake.Embed(
        title="Топ 10 пользователей по рейтингу",
        color=disnake.Color.gold()
    )

    for rank, (user_id, reputation) in enumerate(top_users, start=1):
        member = ctx.guild.get_member(user_id)
        if member:
            embed.add_field(
                name=f"{rank}. {member.display_name}",
                value=f"Рейтинг: {reputation}",
                inline=False
            )
        else:
            # Если пользователя нет на сервере, используем его ID
            embed.add_field(
                name=f"{rank}. User ID: {user_id}",
                value=f"Рейтинг: {reputation}",
                inline=False
            )

    await ctx.send(embed=embed)

@bot.slash_command()
async def lowtop(ctx):
    """Получить топ 10 пользователей с наименьшим рейтингом"""
    # Выполняем SQL-запрос для получения пользователей с наименьшим рейтингом
    cursor.execute("SELECT user_id, reputation FROM reputation ORDER BY reputation ASC LIMIT 10")
    low_rating_users = cursor.fetchall()

    if not low_rating_users:
        await ctx.send("На данный момент нет пользователей с наименьшим рейтингом.")
        return

    # Создаем сообщение с пользователями с наименьшим рейтингом
    embed = disnake.Embed(
        title="Пользователи с наименьшим рейтингом",
        color=disnake.Color.red()
    )

    for rank, (user_id, reputation) in enumerate(low_rating_users, start=1):
        member = ctx.guild.get_member(user_id)
        if member:
            embed.add_field(
                name=f"{rank}. {member.display_name}",
                value=f"Рейтинг: {reputation}",
                inline=False
            )
        else:
            # Если пользователя нет на сервере, используем его ID
            embed.add_field(
                name=f"{rank}. User ID: {user_id}",
                value=f"Рейтинг: {reputation}",
                inline=False
            )

    await ctx.send(embed=embed)

@bot.command()
async def rep(ctx, *, args: str = ""):
    # Проверяем, что команда вызвана в нужном канале
    allowed_channels = [967445056250322964, 1120359666535383040]

    if ctx.channel.id not in allowed_channels:
        return
    
    if not args:
        await ctx.send("Вы не упомянули пользователя, которому хотите дать репутацию, или не указали комментарий.")
        await ctx.message.delete()
        return

    member = ctx.author
    if ctx.message.mentions:
        member = ctx.message.mentions[0]

    if member.id == ctx.author.id:
        await ctx.send("Вы не можете дать репутацию самому себе!")
        await ctx.message.delete()
        return

    # Получаем текущую репутацию пользователя из базы данных
    cursor.execute("SELECT reputation FROM reputation WHERE user_id = ?", (member.id,))
    result = cursor.fetchone()
    current_reputation = result[0] if result else 0

    # Увеличиваем репутацию пользователя на 1
    cursor.execute("INSERT OR IGNORE INTO reputation (user_id, reputation, last_used) VALUES (?, 0, ?)", (member.id, int(time.time())))
    cursor.execute("UPDATE reputation SET reputation = reputation + ?, last_used = ? WHERE user_id = ?", (1, int(time.time()), member.id))
    conn.commit()

    await ctx.message.add_reaction('✅')


@bot.command()
async def unrep(ctx, *, args: str = ""):
    allowed_channels = [967445056250322964, 1120359666535383040]

    if ctx.channel.id not in allowed_channels:
        return
      
    if not args:
        user_avatar_url = ctx.author.avatar_url
        embed = disnake.Embed(
            title="Ошибка",
            description="Вы не упомянули пользователя, у которого хотите убрать репутацию, или не указали комментарий.",
            color=disnake.Color.red()
        )
        embed.set_thumbnail(url=user_avatar_url)
        await ctx.send(embed=embed)
        await ctx.message.delete()
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
        await ctx.message.delete()
        return

    # Получаем текущую репутацию пользователя из базы данных
    cursor.execute("SELECT reputation FROM reputation WHERE user_id = ?", (member.id,))
    result = cursor.fetchone()
    current_reputation = result[0] if result else 0

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
        color=disnake.Color.red()
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
    allowed_roles = [967112931735126036, 956192778134650920, 358551967838109698, 412597708608634881]  # Замените ID ролей на свои
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
async def help(ctx):
    """Получить список доступных команд"""
    # Создаем список команд с их описанием
    commands_list = [
        ("/help", "Получить список доступных команд."),
        ("/online", "Получить количество онлайн-игроков на сервере."),
        ("+rating @пользователь", "Получить рейтинг пользователя."),
        ("+rep @пользователь [комментарий]", "Повысить репутацию пользователя."),
        ("-rep @пользователь [комментарий]", "Понизить репутацию пользователя."),
        ("/top", "Топ 10 пользователей по рейтингу."),
        ("/lowtop", "Топ 10 пользователей с наименьшим количеством рейтинга."),
    ]

    # Создаем embed с списком команд
    embed = disnake.Embed(
        title="Список команд бота",
        description="Список доступных команд и их описаний:",
        color=disnake.Color.blue()
    )

    for command, description in commands_list:
        embed.add_field(name=command, value=description, inline=False)

    await ctx.send(embed=embed)

  
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
    await ctx.message.delete()

bot.run("MTEwOTkxMDczMTgwNzI2ODg2NQ.G5NgO8.5JeaC0jfyYpChGAV0wVznQIlz6UY8CSD199zUw")
