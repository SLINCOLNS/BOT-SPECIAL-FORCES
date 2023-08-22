import disnake
from disnake.ext import commands
import datetime
import aiohttp
import asyncio

intents = disnake.Intents.default()
intents.typing = False
intents.presences = False
intents.voice_states = True
intents.message_content = True

bot = commands.Bot(command_prefix="/", intents=intents)

@bot.event
async def on_ready():
    print(f"Bot is ready: {bot.user}")
    
    ready_channel_id = 1142933434809991198  # ID канала для уведомлений о включении
    ready_channel = bot.get_channel(ready_channel_id)
    
    if ready_channel:
        embed = disnake.Embed(
            title='Бот включен',
            description='Бот был успешно запущен.',
            color=disnake.Color.green()
        )
        embed.add_field(name='Пинг бота', value=f'{bot.latency * 1000:.2f} ms')
        embed.add_field(name='Время запуска', value=datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'))
        
        await ready_channel.send(embed=embed)
        
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

@bot.event
async def on_disconnect():
    disconnect_channel_id = 1142933434809991198  # ID канала для уведомлений о выключении
    disconnect_channel = bot.get_channel(disconnect_channel_id)
    
    if disconnect_channel:
        embed = disnake.Embed(
            title='Бот выключен',
            description=f'Бот был выключен.',
            color=disnake.Color.red()
        )
        embed.add_field(name='Пинг бота', value=f'{bot.latency * 1000:.2f} ms')
        embed.add_field(name='Время выключения', value=datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'))
        
        await disconnect_channel.send(embed=embed)

@bot.event
async def on_raw_reaction_add(payload):
    if payload.message_id == 1142466254611947590:  # ID сообщения
        role_id_to_remove = 1142441100594921532  # ID роли

        guild = bot.get_guild(payload.guild_id)
        member = guild.get_member(payload.user_id)
        role = guild.get_role(role_id_to_remove)

        if member and role:
            await member.remove_roles(role)
            print(f"Role {role.name} removed from {member.name}")

@bot.slash_command()
async def verify(ctx, user: disnake.Member):
    """Выдать пользователю роль верификации"""
    role_id = 1142441100594921532
    log_channel_id = 1142442144787865710
    role = disnake.utils.get(ctx.guild.roles, id=role_id)

    if not role:
        await ctx.send('Не удалось найти указанную роль.')
        return

    try:
        await user.add_roles(role)
        await ctx.send(f'Пользователю {user.mention} выдана роль верификации.')

        log_channel = bot.get_channel(log_channel_id)
        if log_channel:
            embed = disnake.Embed(
                title='Роль выдана',
                description=f'Пользователю {user.mention} выдана роль верификации.',
                color=disnake.Color.green()
            )
            embed.add_field(name='Выдал', value=ctx.author.mention)
            embed.add_field(name='Дата и время', value=datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'))
            await log_channel.send(embed=embed)
    except Exception as e:
        print(e)

@bot.event
async def on_voice_state_update(member, before, after):
    global channel_counter  # Объявляем, что собираемся изменять глобальную переменную channel_counter
    print(f"on_voice_state_update: member={member}, before={before}, after={after}")
    if before.channel != after.channel:
        category_id = 1119580763717906502
        if after.channel and after.channel.id in [
            1119581102932230196,
            1119581149790994442,
            1119581166622744626,
            1119581183546753024,
            1119570085368053760,
            1119581198134546523


        ]:
            category = bot.get_channel(category_id)
            if category:
                if after.channel.id == 1119581102932230196:
                    channel_name = "⚡ | Публичный"
                else:
                    channel_name = "🎮 | Приватный"
                user_limit = after.channel.user_limit if after.channel.id != 1119581102932230196 else None
                new_channel_name = f"{channel_name} #{channel_counter}"
                channel_counter += 1
                new_channel = await category.create_voice_channel(
                    name=new_channel_name,
                    user_limit=user_limit
                )
                created_channels[new_channel.id] = {
                    'name': new_channel_name,
                    'log_message': None,
                    'member_list_message': None,
                    'owner': member
                }  # Сохраняем ID и информацию о созданном канале
                await member.move_to(new_channel)
                log_channel = bot.get_channel(1119583379822755923)
                if log_channel:
                    embed = Embed(title='Канал создан', color=0x00ff00)
                    embed.add_field(name='Название', value=new_channel_name)
                    embed.add_field(name='Создатель', value=member.mention)
                    log_message = await log_channel.send(embed=embed)
                    created_channels[new_channel.id]['log_message'] = log_message

        channel = bot.get_channel(before.channel.id)
        if channel and len(channel.members) == 0 and channel.id in created_channels:
            print(f"No members in channel {channel}, deleting...")
            await channel.delete()
            log_message = created_channels[channel.id]['log_message']
            if log_message:
                await log_message.delete()
            del created_channels[channel.id]  # Удаляем информацию о удаленном канале

    elif before.channel and before.channel.id in created_channels:
        channel = bot.get_channel(before.channel.id)
        if channel:
            member_list_message = created_channels[channel.id]['member_list_message']
            if member_list_message:
                await member_list_message.delete()
                created_channels[channel.id]['member_list_message'] = None

            if len(channel.members) > 0:
                member_list = "\n".join([member.display_name for member in channel.members])
                member_list_message = await channel.send(f"**Участники канала:**\n{member_list}")
                created_channels[channel.id]['member_list_message'] = member_list_message

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
    await ctx.defer()

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
            player_list = "\n".join([player["attributes"]["name"] for player in players])
            player_list_chunks = [player_list[i:i+2000] for i in range(0, len(player_list), 2000)]

            for chunk in player_list_chunks:
                message = f"Players Online - DWS WARP RP:\n{chunk}"
                await disnake.deferred_channel_message(ctx, content=message)

        else:
            await ctx.send("No players online.")
    else:
        await ctx.send("Server not found.")

bot.run("MTEwOTkxMDczMTgwNzI2ODg2NQ.Go-fNw.JAViLdmfINg-d3xXvi_810tSbB72Jm8gJRSv28")

