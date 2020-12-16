"""
All 'singing' functions ie downloading mp3s from YouTube and streaming them.
"""

import os
import discord
from discord import FFmpegPCMAudio
from discord.utils import get
from youtube_dl import YoutubeDL
import youtube_dl

ADMIN_ID = 135410033524604928
BOT_ID = 427062208795639818
PREFIX = '*'


async def join_author_vc(message, client):
    """Join voice channel of message author."""
    del client  # Unused
    try:
        await message.author.voice.channel.connect()
    except AttributeError:
        await message.channel.send('Author not in a voice channel!')
    except discord.errors.ClientException:
        pass


async def sing(message, client):
    """Played audio given music file name."""
    try:
        channel_voice_stream = get(client.voice_clients, guild=message.guild)
        channel_voice_stream.play(FFmpegPCMAudio(
            f'resources/audio/{message.content.replace(f"{PREFIX}sing ", "")}.mp3'))
    except AttributeError as ex:
        print(ex)
        await message.channel.send('Make sure the bot is connected to a voice channel first!')
    except discord.errors.ClientException:
        pass


async def sing_yt(message, client):
    """Played audio from YouTube given URL."""
    ydl_options = {
        'format': 'bestaudio/best',
        'noplaylist': 'True',
        'extractaudio': 'True',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '96',  # Highest bitrate Discord supports
        }],
    }
    ffmpeg_options = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                      'options': '-vn'}
    link = message.content.replace(f"{PREFIX}singyt ", "")

    try:
        channel_voice_stream = get(client.voice_clients, guild=message.guild)
        if not channel_voice_stream.is_playing():
            with YoutubeDL(ydl_options) as ydl:
                info = ydl.extract_info(link, download=False)
            url = info['formats'][0]['url']
            channel_voice_stream.play(FFmpegPCMAudio(url, **ffmpeg_options))
            channel_voice_stream.is_playing()
    except (AttributeError, discord.errors.ClientException) as ex:
        print(ex)
        await message.channel.send('Make sure the bot is connected to a voice channel first!')
    except (youtube_dl.utils.ExtractorError, youtube_dl.utils.DownloadError):
        await message.channel.send('URL not recognised.')


async def download(message, client):
    """Download video from YouTube given URL."""
    del client  # Unused
    try:
        if message.author.id == ADMIN_ID or message.author.id == 265858230247358465:
            title = message.content.split(':')
            ydl_options = {
                'format': 'bestaudio/best',
                'noplaylist': 'True',
                'outtmpl': f'C:/Users/Angel/Desktop/bot/resources/audio/{title[2]}.mp3',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '64',  # Highest bitrate Discord supports
                }],
            }
            # ffmpeg_options = {
            # 'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            # 'options': '-vn'}
            link = message.content.replace(f"{PREFIX}download ", "")

            try:
                with YoutubeDL(ydl_options) as ydl:
                    ydl.extract_info(link, download=True)
                    # info = ydl.extract_info(link, download=True)
                # url = info['formats'][0]['url']
            except (youtube_dl.utils.ExtractorError, youtube_dl.utils.DownloadError):
                await message.channel.send('URL not recognised.')
    except IndexError:
        pass


async def list_songs(message, client):
    """List all songs on local directory."""
    del client  # Unused
    songs = os.listdir('C:/Users/Angel/Desktop/bot/resources/audio/')
    string = ''
    for song in songs:
        string += f'{song}\n'
    await message.channel.send(f'```{string}```')


async def stop_audio(message, client):
    """Stop playing audio."""
    del message  # Unused
    channel_voice_stream = get(client.voice_clients)
    try:
        channel_voice_stream.stop()
    except (discord.errors.ClientException, AttributeError):
        pass


async def leave_vc(message, client):
    """Leave current voice channel."""
    del client  # Unused
    try:
        await message.guild.voice_client.disconnect()
    except AttributeError:
        pass
