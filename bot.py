"""
Discord bot written in Python.
Tested and working in 3.7.4 and 3.8.0.
Code written to PEP-8 standards.

Requirements:
discord: for bot to run
mcstatus: for query_mc_server() and mc_status()
Google Sheets API Python requirements: for ow_sheet() and sheets.get_excel()
requests, BeautifulSoup4: web scraping for more Overwatch stats
psutil: for get_server_vals() and get_process()
youtube-dl: for sing_yt() and download() - not required for regular sing()

Author - yakasov
"""

from datetime import date
from time import gmtime, strftime
from asyncio import sleep
from subprocess import Popen
import itertools
import socket
import random
import os

from mcstatus import MinecraftServer
from discord.ext import tasks
# from discord.utils import get
import psutil
import discord
import sheets
import overwatch_functions as ow
import audio_functions as music

client = discord.Client()
ADMIN_ID = 135410033524604928
BOT_ID = 427062208795639818
PREFIX = '*'


def clear():
    """Clear console when called."""
    os.system('cls')


def get_file(location):
    """Return contents of file at {location}."""
    with open(location, 'r') as file:
        result = file.read()
        file.close()
    return result


def write_file(location, content):
    """Write contents to file at {location}."""
    with open(location, 'w') as file:
        file.write(content)
        file.close()


MCSERVER = MinecraftServer('84.71.200.226', 25565)
PRESENCE_DELAY = 4  # Too low a delay will cause Discord to stop updating presence

TODAY = date.today()
TODAY_FORMATTED = TODAY.strftime('%d/%m')
CACHE_TIME = get_file('resources/cache')
LYRICS = get_file('resources/8milelyrics').split('\n')
TOM_ID = 269143269336809483

# Load commands file into memory on startup
COMMANDS = get_file('resources/commands')
BIRTHDAYS_RAW = get_file('resources/birthdays').split('\n')
BIRTHDAYS = []
for line in BIRTHDAYS_RAW:
    if '#' not in line:
        BIRTHDAYS.append(line.split(" "))
BIRTHDAYS.pop()  # Adds a blank value add the end, I don't know why yet
# Probably because Atom adds a blank line at the end of the file


def get_process(name):
    """Get the Process ID of a process given it's name."""
    for process in psutil.process_iter():
        process_info = process.as_dict(attrs=['pid', 'name'])

        if name in process_info['name'].lower():
            return process_info['pid']
    return None


def get_name(message, thanks_type):
    """Get name in Thanks command."""
    msg = message.content.upper()
    result = ''
    if thanks_type in msg:
        result = msg[msg.find(thanks_type):].replace(thanks_type, '')

    if result.lower().strip() == '':
        return ' *the spanner above me*'
    if 'ANYONE' in result:
        return f' *{random.choice(message.guild.members)}*'
    return f' *{result.lower().strip()}*'


async def check_birthdays():
    """Check to see if it's someone's birthday! Uses birthday file from resources."""
    bday_channel = client.get_channel(509089139853885440)
    for person in BIRTHDAYS:
        if person[1] == TODAY_FORMATTED:
            if CACHE_TIME != str(TODAY_FORMATTED):
                await bday_channel.send(f'Happy Birthday, {person[0]}! \
({client.get_user(int(person[2])).mention})')
                write_file('resources/cache', TODAY_FORMATTED)


async def get_pfp(message):
    """Get profile picture of user given ID. If no ID, use author."""
    if len(message.content) == 7:
        await message.channel.send(message.author.avatar_url)
    elif 'ANYONE' in message.content.upper():
        await message.channel.send(random.choice(message.guild.members).avatar_url)
    else:
        try:
            user_obj = client.get_user(int(message.content.split(' ')[1]))
            await message.channel.send(user_obj.avatar_url)
        except AttributeError:  # Argument is not a valid ID (but still integer)
            pass
        except ValueError:  # Argument is not an integer
            pass


async def get_all_pfps(message):
    """Sends all profile pictures for everyone in server.
       Only usable by ADMIN_ID.
    """
    if message.author.id == ADMIN_ID:
        for user in message.guild.members:
            await message.channel.send(user.avatar_url)


async def change_nick(message):
    """Change bot nickname for current guild."""
    try:
        await message.guild.get_member(BOT_ID).edit(
            nick=message.content.replace(f'{PREFIX}setnick ', ''))
    except discord.errors.HTTPException:  # Occurs when Discord gets upset with the bot
        await message.channel.send('Nickname must be 32 characters or fewer in length.')


async def change_presence(message):
    """Change bot game presence."""
    await client.change_presence(activity=discord.Game(
        message.content.replace(f'{PREFIX}setstatus ', '')))


async def get_commands(message):
    """Send all commands from commands file using get_file()."""
    await message.channel.send(COMMANDS)


async def mc_status(message):
    """Send lots of information about the Minecraft server."""
    try:
        await message.channel.send(f'There are {MCSERVER.status().players.online} players online!\
        \nThe server replied in {MCSERVER.status().latency}ms!\
        \nPlayers online: {", ".join(MCSERVER.query().players.names)}')
        # For MCSERVER.query() to work, make sure enable-query=true is in server.properties
    except (ConnectionRefusedError, socket.timeout):  # Server can't be reached
        await message.channel.send('Either the server is down or is having latency issues :(')


async def ow_sheet(message):
    """Sends Overwatch rankings from the Google Sheets spreadsheet."""
    await sheets.get_excel(message)


async def happy_katie(message):
    """Happy Katie!"""
    katie = client.get_user(410834613343223818)
    channel = await katie.create_dm()
    await channel.send('Good luck in your Overwatch game, Katie!')


async def restart(message):  # This isn't a great way of restarting the bot
    """Restart bot."""  # But it's the best I could figure out
    if message.author.id == ADMIN_ID:
        Popen('python bot.py')
        raise SystemExit


async def stop(message):
    """Stop bot."""
    if message.author.id == ADMIN_ID:
        raise SystemExit


async def query_mc_server():
    """Query the Minecraft server and set the rich presence to the players online."""
    try:
        players_online = MCSERVER.status().players.online
        if players_online == 1:
            await client.change_presence(activity=discord.Game(
                f'Minecraft [{players_online} player]'))
        else:
            await client.change_presence(activity=discord.Game(
                f'Minecraft [{players_online} players]'))
    except ConnectionRefusedError:  # Server can't be reached
        await client.change_presence(activity=discord.Game(
            'Server might not be running?'))


async def query_mc_server_names():
    """Query the Minecraft server and set the rich presence to the player names."""
    try:
        players = MCSERVER.query().players.names
        player_display = '\n| '.join(players)
        await client.change_presence(activity=discord.Game(player_display))
    except ConnectionRefusedError:  # Server can't be reached
        await client.change_presence(activity=discord.Game(
            'Enable query in server.properties!'))


async def get_server_vals():
    """Get CPU and RAM values for Minecraft server and set the rich presence to these."""
    mcserver_process = psutil.Process(get_process('java'))

    if round(mcserver_process.memory_info()[0] / 1073741824, 2) >= 0.1:
        await client.change_presence(activity=discord.Game(
            f'CPU {mcserver_process.cpu_percent()}% \
RAM {round(mcserver_process.memory_info()[0] / 1073741824, 2)}GB'
        ))  # 1048576 for MB, 1073741824 for GB


async def get_ow_stats(message):
    """Get Overwatch stats from the playoverwatch website."""
    words = message.content.split(' ')
    if len(words) > 2:
        username = words[1]
        criteria = ' '.join(words[2:])

        soup = ow.get_page(username)
        stat_value = ow.search_soup(soup, criteria.lower())

        if stat_value is not None:
            await message.channel.send(f'{criteria} for {username}: {stat_value}')
        else:
            await message.channel.send('No stat to return. Check your username + criteria string!')
    else:
        await message.channel.send('Command syntax: ```*owstats {USERNAME} {STATISTIC}```\
An example statistic is \'Time Played\'.')


async def say_smth(message):
    """Say something given a message."""
    msg = message.content.split(' ', 1)[1]

    banned_words = ['uhoh', 'stinky']  # Or phrases
    # For phrases, remove spaces
    i = ''.join(c[0] for c in itertools.groupby(message.content)).replace(' ', '')

    # I imagine there are cases where this doesn't catch banned words?
    # Spelling mistakes will also not be caught
    for word in banned_words:
        if word in i:
            return None

    await message.channel.send(msg)
    await message.delete()


@ tasks.loop(seconds=PRESENCE_DELAY * 2)
async def rolling_presence():
    """Rotate rich presence through functions below on certain delay."""
    await query_mc_server()
    await sleep(PRESENCE_DELAY)
    await query_mc_server_names()
    await sleep(PRESENCE_DELAY)
    # await get_server_vals()
    # await sleep(PRESENCE_DELAY)


async def change_tom_nick():
    """Changes Tom's nickname to 8 mile lyrics. Don't ask"""
    while True:
        lyric = LYRICS[random.randint(0, len(LYRICS) - 1)][:30]

        await sleep(20)
        await client.get_guild(271381095990296576).get_member(TOM_ID).edit(nick=lyric)


@ client.event
async def on_ready():
    """Run when bot has connected to Discord successfully."""
    clear()
    print(f'Connected and ready to go!\nCurrent date is {TODAY_FORMATTED}')
    psutil.cpu_percent()  # Get first CPU percentage usage (always 0.0)
    await check_birthdays()
    # await change_tom_nick()
    await rolling_presence.start()
    # Anything after the above line will NOT get executed


@ client.event
async def on_message(message):
    """Run when a command has been sent in a channel the bot can see."""
    if not message.author.bot:
        print(f'\n{strftime("[%Y-%m-%d %H:%M:%S] ", gmtime())}\
SERVER: {message.guild.name} | CHANNEL: {message.channel}\n{message.author}: {message.content}')

        cmd = message.content.upper()
        #  words = cmd.split(' ')

        responses = {
            # TEXT RESPONSES
            'LEAGUE': 'league gay',
            'GOOD BOT': ':)',
            'BAD BOT': f'bad {str(message.author)[:-5]}',

            # OBJECT / ATTRIBUTE RESPONSES
            f'{PREFIX}GETPFP': get_pfp,

            # FUNCTION RESPONSES
            f'{PREFIX}GETALL': get_all_pfps,
            f'{PREFIX}SETNICK': change_nick,
            f'{PREFIX}SETSTATUS': change_presence,
            f'{PREFIX}COMMANDS': get_commands,
            f'{PREFIX}MCSTATUS': mc_status,
            f'{PREFIX}OWSHEET': ow_sheet,
            f'{PREFIX}OWSTATS': get_ow_stats,
            f'{PREFIX}KATIE': happy_katie,
            f'{PREFIX}TOMINEM': change_tom_nick,
            f'{PREFIX}SAY': say_smth,

            # MUSIC RESPONSES
            f'{PREFIX}JOIN': music.join_author_vc,
            f'{PREFIX}SING': music.sing,
            f'{PREFIX}SINGYT': music.sing_yt,
            f'{PREFIX}STOP': music.stop_audio,
            f'{PREFIX}DISCONNECT': music.leave_vc,
            f'{PREFIX}SONGS': music.list_songs,
            f'{PREFIX}DOWNLOAD': music.download,

            # ADMIN RESPONSES
            f'{PREFIX}RESTART': restart,
            f'{PREFIX}STOPPLS': stop
        }

        thanks_list = ['THANKS', 'TY', 'THANK YOU', 'THANK']
        # My best method of adding multiple types of Thanks to the dictionary lol
        for thanks_type in thanks_list:
            responses[thanks_type] = f'Thank you,{get_name(message, thanks_type)}\
, for your meaningful contribution!'

        for key in responses:
            if f' {key} ' in f' {cmd} ' or f'{PREFIX}{key} ' in f'{cmd} ':
                # Surround key + cmd in spaces in case of it being start or end of message
                # No start space required for prefix commands
                res = responses[key]
                if callable(res):  # If res is callable, execute as a function and don't send
                    try:
                        await res(message, client)
                    except TypeError:  # This is a dumb workaround
                        await res(message)
                else:
                    try:
                        await message.channel.send(res)
                    except discord.errors.HTTPException:
                        await message.channel.send(
                            'Error sending message back - maybe it was too long?')
                break


@ client.event
async def on_voice_state_update(member, before, after):
    """Things to do when someone updates their voice state, like joining a voice channel."""
    try:
        if before.channel is None and after.channel.id == 376827068723232778:  # Overwatch Gang Bang
            ow_channel = after.channel
            ow_text_channel = client.get_channel(
                541926728268906506)  # token-farming
            if len(ow_channel.members) == 2:
                await ow_text_channel.send(f'Good luck to all in {after.channel.mention}!')
                await sleep(600)
    except AttributeError:  # Happens if leaving, no channel has no ID
        pass


token = get_file('resources/token.discord')
client.run(token)
