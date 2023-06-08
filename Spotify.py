import disnake
from disnake.ext import commands
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from dotenv import load_dotenv
import os

load_dotenv()

SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
SPOTIFY_REDIRECT_URI = os.getenv('SPOTIFY_REDIRECT_URI')

spotify_credentials = SpotifyClientCredentials(client_id=SPOTIFY_CLIENT_ID, client_secret=SPOTIFY_CLIENT_SECRET)
spotify = spotipy.Spotify(client_credentials_manager=spotify_credentials)

class Sputify(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command()
    async def sp(self, interaction):
        pass

    @sp.sub_command(description='Воспроизведение музыки из Spotify')
    async def url(self, interaction, url):
        if interaction.author.voice is None:
            await interaction.response.send_message(
                "Вы должны находиться в голосовом канале для использования этой команды.", ephemeral=True)
            return

        voice_channel = interaction.author.voice.channel
        voice_client = await voice_channel.connect()

        track_info = spotify.track(url)

        track_id = track_info['id']
        audio_url = spotify.track(track_id)['preview_url']
        if not audio_url:
            await interaction.response.send_message("Произошла ошибка при получении URL аудиофайла.")
            await voice_client.disconnect()
            return

        voice_client.play(disnake.FFmpegPCMAudio(executable="C:/ffmpeg/bin/ffmpeg.exe", source=audio_url))

    @sp.error
    async def play_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Пожалуйста, укажите URL трека.")
        else:
            await ctx.send(f"Произошла ошибка при выполнении команды: {error}")

def setup(bot):
    bot.add_cog(Sputify(bot))
