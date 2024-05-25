import discord
from discord.ext import commands
from discord_slash import SlashCommand, SlashContext, manage_commands
import yt_dlp as youtube_dl
import os
import asyncio
from collections import deque
import json

# Charger les variables d'environnement depuis le fichier config.json
with open('config.json') as f:
    config = json.load(f)

DISCORD_TOKEN = config['DISCORD_TOKEN']
GUILD_ID = int(config['GUILD_ID'])
CHANNEL_ID = int(config['CHANNEL_ID'])
GENIUS_API_TOKEN = config.get('GENIUS_API_TOKEN')

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.voice_states = True

bot = commands.Bot(command_prefix='!', intents=intents)
slash = SlashCommand(bot, sync_commands=True)

queue = {}  # Dictionnaire pour stocker les files d'attente par guilde

def get_queue(guild_id):
    if guild_id not in queue:
        queue[guild_id] = deque()
    return queue[guild_id]

def load_playlists():
    try:
        with open('playlists.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_playlists(playlists):
    with open('playlists.json', 'w') as f:
        json.dump(playlists, f, indent=4)

playlists = load_playlists()

@bot.event
async def on_ready():
    print(f'Connecté en tant que {bot.user}!')
    await bot.change_presence(activity=discord.Game(name="with music commands"))

@slash.slash(name="download_mp3", description="Télécharge une playlist YouTube en MP3", guild_ids=[GUILD_ID])
async def download_mp3(ctx: SlashContext, url: str):
    channel = bot.get_channel(CHANNEL_ID)
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True
    }

    try:
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)
            playlist_title = info_dict.get('title', 'Unknown Playlist')
            total_videos = len(info_dict['entries'])

            embed = discord.Embed(title=f"Téléchargement de la playlist : {playlist_title}", color=0x00ff00)
            embed.add_field(name="Nombre de pistes", value=str(total_videos))
            await ctx.send(embed=embed)

            for i, video in enumerate(info_dict['entries'], start=1):
                video_url = f"https://www.youtube.com/watch?v={video['id']}"
                video_info = ydl.extract_info(video_url, download=True)
                filename = ydl.prepare_filename(video_info)

                embed.description = f"Téléchargement... ({i}/{total_videos})"
                embed.set_footer(text=f"Progression : {int((i / total_videos) * 100)}%")
                await ctx.send(embed=embed)
                await channel.send(file=discord.File(filename))

            embed.description = "Téléchargement terminé !"
            embed.set_image(url="attachment:C:\\Users\\siali\\Desktop\\youtube convert\\dllyt.jpg")
            await ctx.send(embed=embed, file=discord.File("/mnt/data/dllyt.jpg", filename="dllyt.jpg"))
    except Exception as e:
        await ctx.send(f"Une erreur s'est produite : {e}")

@slash.slash(name="download_video", description="Télécharge une vidéo YouTube en MP4", guild_ids=[GUILD_ID])
async def download_video(ctx: SlashContext, url: str):
    channel = bot.get_channel(CHANNEL_ID)
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegVideoConvertor',
            'preferredformat': 'mp4',
        }],
        'quiet': True
    }

    try:
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info_dict)
            await channel.send(file=discord.File(filename))
            await ctx.send("Téléchargement de la vidéo terminé !")
    except Exception as e:
        await ctx.send(f"Une erreur s'est produite : {e}")

@slash.slash(name="join", description="Rejoint le canal vocal de l'utilisateur", guild_ids=[GUILD_ID])
async def join(ctx: SlashContext):
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        await channel.connect()
        await ctx.send(f"Connecté au canal vocal : {channel.name}")
    else:
        await ctx.send("Vous devez être connecté à un canal vocal.")

@slash.slash(name="play", description="Joue une vidéo ou un streaming YouTube dans le canal vocal", guild_ids=[GUILD_ID])
async def play(ctx: SlashContext, url: str):
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if not voice_client:
        if ctx.author.voice:
            channel = ctx.author.voice.channel
            voice_client = await channel.connect()
        else:
            await ctx.send("Vous devez être connecté à un canal vocal pour jouer de la musique.")
            return

    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True
    }

    try:
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            url2 = info['formats'][0]['url']
            source = discord.FFmpegPCMAudio(url2, executable='ffmpeg', before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5", options="-vn")
            voice_client.play(source)

            await ctx.send(f"En train de jouer : {info['title']}")
    except Exception as e:
        await ctx.send(f"Une erreur s'est produite : {e}")

@slash.slash(name="play_live", description="Diffuse un live YouTube dans le canal vocal", guild_ids=[GUILD_ID])
async def play_live(ctx: SlashContext, url: str):
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if not voice_client:
        if ctx.author.voice:
            channel = ctx.author.voice.channel
            voice_client = await channel.connect()
        else:
            await ctx.send("Vous devez être connecté à un canal vocal pour diffuser un live.")
            return

    ydl_opts = {
        'format': 'best',
        'quiet': True
    }

    try:
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            url2 = info['formats'][0]['url']
            source = discord.FFmpegPCMAudio(url2, executable='ffmpeg', before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5", options="-vn")
            voice_client.play(source)

            await ctx.send(f"En train de diffuser : {info['title']}")
    except Exception as e:
        await ctx.send(f"Une erreur s'est produite : {e}")

@slash.slash(name="stream", description="Diffuse une vidéo YouTube en mode streaming", guild_ids=[GUILD_ID])
async def stream(ctx: SlashContext, url: str):
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if not voice_client:
        if ctx.author.voice:
            channel = ctx.author.voice.channel
            voice_client = await channel.connect()
        else:
            await ctx.send("Vous devez être connecté à un canal vocal pour diffuser une vidéo.")
            return

    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True
    }

    try:
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            url2 = info['formats'][0]['url']
            source = discord.FFmpegPCMAudio(url2, executable='ffmpeg', before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5", options="-vn")
            voice_client.play(source)

            await ctx.send(f"En train de diffuser : {info['title']}")
    except Exception as e:
        await ctx.send(f"Une erreur s'est produite : {e}")

@slash.slash(name="leave", description="Quitte le canal vocal", guild_ids=[GUILD_ID])
async def leave(ctx: SlashContext):
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice_client:
        await voice_client.disconnect()
        await ctx.send("Déconnecté du canal vocal.")

@slash.slash(name="pause", description="Met en pause la lecture de la musique", guild_ids=[GUILD_ID])
async def pause(ctx: SlashContext):
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice_client and voice_client.is_playing():
        voice_client.pause()
        await ctx.send("Lecture mise en pause.")
    else:
        await ctx.send("Aucune musique en cours de lecture.")

@slash.slash(name="resume", description="Reprend la lecture de la musique", guild_ids=[GUILD_ID])
async def resume(ctx: SlashContext):
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice_client and voice_client.is_paused():
        voice_client.resume()
        await ctx.send("Lecture reprise.")
    else:
        await ctx.send("La musique n'est pas en pause actuellement.")

@slash.slash(name="skip", description="Passe à la chanson suivante dans la file d'attente", guild_ids=[GUILD_ID])
async def skip(ctx: SlashContext):
    guild_id = ctx.guild_id
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice_client and voice_client.is_playing():
        voice_client.stop()
        await ctx.send("Chanson suivante...")
    else:
        await ctx.send("Aucune musique en cours de lecture.")

@slash.slash(name="enqueue", description="Ajoute une vidéo YouTube à la file d'attente", guild_ids=[GUILD_ID])
async def enqueue(ctx: SlashContext, url: str):
    guild_id = ctx.guild_id
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)

    if not voice_client:
        if ctx.author.voice:
            channel = ctx.author.voice.channel
            voice_client = await channel.connect()
        else:
            await ctx.send("Vous devez être connecté à un canal vocal pour ajouter de la musique.")
            return

    try:
        with youtube_dl.YoutubeDL({'format': 'bestaudio'}) as ydl:
            info = ydl.extract_info(url, download=False)
            song = {'title': info['title'], 'url': info['formats'][0]['url']}

        q = get_queue(guild_id)
        q.append(song)
        await ctx.send(f"Chanson ajoutée à la file d'attente : {info['title']}")

        if not voice_client.is_playing():
            await play_next_song(ctx, voice_client, guild_id)
    except Exception as e:
        await ctx.send(f"Une erreur s'est produite : {e}")

async def play_next_song(ctx, voice_client, guild_id):
    q = get_queue(guild_id)
    if q:
        song = q.popleft()
        source = discord.FFmpegPCMAudio(song['url'], executable='ffmpeg', before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5", options="-vn")
        voice_client.play(source, after=lambda e: asyncio.run_coroutine_threadsafe(play_next_song(ctx, voice_client, guild_id), bot.loop))
        await ctx.send(f"En train de jouer : {song['title']}")
    else:
        await ctx.send("File d'attente vide. Ajoutez plus de chansons !")

@slash.slash(name="queue", description="Affiche la file d'attente de musique", guild_ids=[GUILD_ID])
async def show_queue(ctx: SlashContext):
    guild_id = ctx.guild_id
    q = get_queue(guild_id)
    if q:
        message = "\n".join([f"{idx + 1}. {song['title']}" for idx, song in enumerate(q)])
        await ctx.send(f"File d'attente :\n{message}")
    else:
        await ctx.send("La file d'attente est vide.")

@slash.slash(name="nowplaying", description="Affiche les informations sur la chanson en cours de lecture", guild_ids=[GUILD_ID])
async def nowplaying(ctx: SlashContext):
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice_client and voice_client.is_playing():
        current_song = voice_client.source.title
        await ctx.send(f"En train de jouer : {current_song}")
    else:
        await ctx.send("Aucune musique en cours de lecture.")

@slash.slash(name="loop", description="Active ou désactive la lecture en boucle de la chanson actuelle", guild_ids=[GUILD_ID])
async def loop(ctx: SlashContext):
    guild_id = ctx.guild_id
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice_client and voice_client.is_playing():
        if guild_id in queue and queue[guild_id]:
            current_song = queue[guild_id][0]
            queue[guild_id].appendleft(current_song)
            await ctx.send("Lecture en boucle activée.")
        else:
            await ctx.send("Aucune musique en cours de lecture.")
    else:
        await ctx.send("Aucune musique en cours de lecture.")

@slash.slash(name="stop", description="Arrête la lecture et vide la file d'attente", guild_ids=[GUILD_ID])
async def stop(ctx: SlashContext):
    guild_id = ctx.guild_id
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice_client:
        get_queue(guild_id).clear()
        voice_client.stop()
        await ctx.send("Lecture arrêtée et file d'attente vidée.")
    else:
        await ctx.send("Aucune musique en cours de lecture.")

@slash.slash(name="search", description="Recherche des vidéos sur YouTube", guild_ids=[GUILD_ID])
async def search(ctx: SlashContext, query: str):
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True
    }

    try:
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch5:{query}", download=False)
            results = info['entries']
            embed = discord.Embed(title=f"Résultats de recherche pour '{query}'", color=0x00ff00)
            for idx, entry in enumerate(results, start=1):
                embed.add_field(name=f"{idx}. {entry['title']}", value=f"https://www.youtube.com/watch?v={entry['id']}", inline=False)
            await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"Une erreur s'est produite : {e}")

import lyricsgenius

genius = lyricsgenius.Genius(GENIUS_API_TOKEN)

@slash.slash(name="lyrics", description="Affiche les paroles de la chanson en cours de lecture", guild_ids=[GUILD_ID])
async def lyrics(ctx: SlashContext):
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice_client and voice_client.is_playing():
        current_song = voice_client.source.title
        song = genius.search_song(current_song)
        if song:
            await ctx.send(f"Paroles de {current_song}:\n{song.lyrics}")
        else:
            await ctx.send("Paroles non trouvées.")
    else:
        await ctx.send("Aucune musique en cours de lecture.")

@slash.slash(name="volume", description="Règle le volume de la musique", guild_ids=[GUILD_ID])
async def volume(ctx: SlashContext, volume: int):
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice_client:
        voice_client.source.volume = volume / 100.0
        await ctx.send(f"Volume réglé à {volume}%")
    else:
        await ctx.send("Aucune musique en cours de lecture.")

@slash.slash(name="save_playlist", description="Enregistre la file d'attente actuelle en tant que playlist", guild_ids=[GUILD_ID])
async def save_playlist(ctx: SlashContext, name: str):
    guild_id = ctx.guild_id
    q = get_queue(guild_id)
    if q:
        playlists[name] = list(q)
        save_playlists(playlists)
        await ctx.send(f"Playlist '{name}' enregistrée.")
    else:
        await ctx.send("La file d'attente est vide.")

@slash.slash(name="load_playlist", description="Charge une playlist enregistrée", guild_ids=[GUILD_ID])
async def load_playlist(ctx: SlashContext, name: str):
    guild_id = ctx.guild_id
    if name in playlists:
        q = get_queue(guild_id)
        q.extend(playlists[name])
        await ctx.send(f"Playlist '{name}' chargée.")
        voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
        if voice_client and not voice_client.is_playing():
            await play_next_song(ctx, voice_client, guild_id)
    else:
        await ctx.send("Playlist non trouvée.")

@slash.slash(name="add_to_playlist", description="Ajoute une vidéo à une playlist enregistrée", guild_ids=[GUILD_ID])
async def add_to_playlist(ctx: SlashContext, name: str, url: str):
    if name in playlists:
        ydl_opts = {
            'format': 'bestaudio/best',
            'quiet': True
        }
        try:
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                song = {'title': info['title'], 'url': info['formats'][0]['url']}
                playlists[name].append(song)
                save_playlists(playlists)
                await ctx.send(f"Ajouté {info['title']} à la playlist '{name}'.")
        except Exception as e:
            await ctx.send(f"Une erreur s'est produite : {e}")
    else:
        await ctx.send("Playlist non trouvée.")

@slash.slash(name="remove_from_playlist", description="Supprime une vidéo d'une playlist enregistrée", guild_ids=[GUILD_ID])
async def remove_from_playlist(ctx: SlashContext, name: str, index: int):
    if name in playlists and 0 <= index < len(playlists[name]):
        removed_song = playlists[name].pop(index)
        save_playlists(playlists)
        await ctx.send(f"Supprimé {removed_song['title']} de la playlist '{name}'.")
    else:
        await ctx.send("Playlist non trouvée ou index invalide.")

@slash.slash(name="playlist_details", description="Affiche les détails d'une playlist enregistrée", guild_ids=[GUILD_ID])
async def playlist_details(ctx: SlashContext, name: str):
    if name in playlists:
        message = "\n".join([f"{idx + 1}. {song['title']}" for idx, song in enumerate(playlists[name])])
        await ctx.send(f"Détails de la playlist '{name}':\n{message}")
    else:
        await ctx.send("Playlist non trouvée.")

@slash.slash(name="trending", description="Affiche les vidéos tendance sur YouTube", guild_ids=[GUILD_ID])
async def trending(ctx: SlashContext):
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True
    }

    try:
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info("https://www.youtube.com/feed/trending", download=False)
            results = info['entries']
            embed = discord.Embed(title="Vidéos tendance sur YouTube", color=0x00ff00)
            for idx, entry in enumerate(results[:10], start=1):
                embed.add_field(name=f"{idx}. {entry['title']}", value=f"https://www.youtube.com/watch?v={entry['id']}", inline=False)
            await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"Une erreur s'est produite : {e}")

bot.run(DISCORD_TOKEN)
