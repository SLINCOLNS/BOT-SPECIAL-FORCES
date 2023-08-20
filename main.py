import keep_alive
import discord
import datetime
from discord.ext import commands
from discord import Embed


intents = discord.Intents.default()
intents.typing = False
intents.presences = False
intents.voice_states = True
intents.message_content = True

bot = commands.Bot(command_prefix="/", intents=intents)

# Список для хранения ID созданных каналов и соответствующих сообщений лога
created_channels = {}
channel_counter = 1
restricted_role_id = 1142574526241189919

@bot.event
async def on_ready():
    print(f"Bot is ready: {bot.user}")
    activity = discord.Game(name="DWS | Unturned")
    await bot.change_presence(activity=activity)
  
@bot.command()
async def verify(ctx, *, user: discord.Member):
    role_id = 1142441100594921532
    log_channel_id = 1142442144787865710
    role = discord.utils.get(ctx.guild.roles, id=role_id)

    if not role:
        await ctx.send('Не удалось найти указанную роль.')
        return

    try:
        await user.add_roles(role)
        await ctx.send(f'Пользователю {user.mention} выдана роль.')

        # Отправка информации в лог-канал
        log_channel = bot.get_channel(log_channel_id)
        if log_channel:
            embed = discord.Embed(
                title='Роль выдана',
                description=f'Пользователю {user.mention} выдана роль верификации.',
                color=discord.Color.green()
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

keep_alive.keep_alive()
bot.run("MTEwOTkxMDczMTgwNzI2ODg2NQ.Go-fNw.JAViLdmfINg-d3xXvi_810tSbB72Jm8gJRSv28")
