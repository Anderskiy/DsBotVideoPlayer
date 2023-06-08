import disnake
from disnake.ext import commands
from pytube import YouTube, Playlist
from youtubesearchpython import VideosSearch
import asyncio
import os

if not os.path.exists("temp"):
    os.makedirs("temp")

class MusicQueue:
    def __init__(self):
        self.queue = []
        self.is_paused = False

    def add_to_queue(self, url):
        self.queue.append(url)

    def get_next_url(self):
        if self.queue:
            return self.queue.pop(0)
        else:
            return None

music_queue = MusicQueue()

async def play_next_song(voice_client):
    next_url = music_queue.get_next_url()

    if next_url:
        try:
            video = YouTube(next_url)
            video_stream = video.streams.filter(only_audio=True).first()
            video_stream.download(output_path="temp")
            video_title = video.title.replace(" ", "_").replace("\\", "").replace("|", "")

            original_path = os.path.join("temp", video_stream.default_filename)
            renamed_path = os.path.join("temp", video_title + ".mp4")
            os.rename(original_path, renamed_path)

        except Exception as e:
            print(e)
            await play_next_song(voice_client)
            return

        mp4_path = renamed_path
        mp3_path = os.path.join("temp", video_title + ".mp3")
        os.system(f"ffmpeg -i {mp4_path} -vn -ar 44100 -ac 2 -b:a 192k {mp3_path}")

        if not voice_client.is_playing():
            voice_client.play(disnake.FFmpegPCMAudio(executable="C:/ffmpeg/bin/ffmpeg.exe", source=mp3_path))

        while voice_client.is_playing():
            if music_queue.is_paused:
                await asyncio.sleep(1)
            else:
                await asyncio.sleep(1)

        os.remove(mp4_path)
        os.remove(mp3_path)

        await play_next_song(voice_client)
    else:
        await voice_client.disconnect()

class YouTubeMusic(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command()
    async def yt(self, interaction):
        pass

    @yt.sub_command(name='url', description='Воспроизведение музыки с YouTube')
    async def url(self, interaction, url: str):
        await interaction.response.defer()
        if interaction.author.voice is None:
            await interaction.send(
                "Вы должны находиться в голосовом канале для использования этой команды.", ephemeral=True)
            return

        voice_channel = interaction.author.voice.channel
        voice_client = disnake.utils.get(self.bot.voice_clients, guild=interaction.guild)
        if voice_client:
            await voice_client.move_to(voice_channel)
        else:
            voice_client = await voice_channel.connect()

        search_results = VideosSearch(url, limit=1).result()['result']
        if not search_results:
            await interaction.send(f"Не удалось найти видео с юрл '`{url}`'.")
            return
        video_info = search_results[0]
        banner = video_info['thumbnails'][0]['url']
        duration = video_info['duration']
        author = video_info['channel']['name']
        video_title = video_info['title']

        embed = disnake.Embed(title="Информация о треке", color=0x2B2D31)
        embed.set_thumbnail(url=banner)
        embed.add_field(name="Название:", value=video_title, inline=False)
        embed.add_field(name="Длительность:", value=duration, inline=True)
        embed.add_field(name="Автор:", value=author, inline=True)

        await interaction.send("Видео добавлено в очередь.", embed=embed)

        music_queue.add_to_queue(url)

        if not voice_client.is_playing():
            await play_next_song(voice_client)

    @yt.sub_command(description='Поиск и воспроизведение музыки с YouTube')
    async def search(self, interaction, title: str):
        await interaction.response.defer()

        if interaction.author.voice is None:
            await interaction.send(
                "Вы должны находиться в голосовом канале для использования этой команды.", ephemeral=True)
            return

        search_results = VideosSearch(title, limit=1).result()['result']
        if not search_results:
            await interaction.send(f"Не удалось найти видео с названием '{title}'.")
            return
        video_info = search_results[0]
        url = video_info['link']
        banner = video_info['thumbnails'][0]['url']
        duration = video_info['duration']
        author = video_info['channel']['name']
        video_title = video_info['title']

        voice_channel = interaction.author.voice.channel
        voice_client = disnake.utils.get(self.bot.voice_clients, guild=interaction.guild)

        if voice_client:
            await voice_client.move_to(voice_channel)
        else:
            voice_client = await voice_channel.connect()

        embed = disnake.Embed(title="Информация о треке", color=0x2B2D31)
        embed.set_thumbnail(url=banner)
        embed.add_field(name="Название:", value=video_title, inline=False)
        embed.add_field(name="Длительность:", value=duration, inline=True)
        embed.add_field(name="Автор:", value=author, inline=True)

        await interaction.send(embed=embed, content=f"Видео '{title}' добавлено в очередь.")

        music_queue.add_to_queue(url)

        if not voice_client.is_playing():
            await play_next_song(voice_client)

    @yt.sub_command(description='Воспроизведение плейлиста с YouTube')
    async def playlist(self, interaction, url: str):
        await interaction.response.defer()

        if interaction.author.voice is None:
            await interaction.send(
                "Вы должны находиться в голосовом канале для использования этой команды.",
                ephemeral=True)
            return

        playlist = Playlist(url)

        voice_channel = interaction.author.voice.channel
        voice_client = disnake.utils.get(self.bot.voice_clients, guild=interaction.guild)

        if voice_client:
            await voice_client.move_to(voice_channel)
        else:
            voice_client = await voice_channel.connect()

        for video in playlist.videos:
            music_queue.add_to_queue(video.watch_url)

        await interaction.send(f"Плейлист '{playlist.title}' добавлен в очередь.")

        if not voice_client.is_playing():
            await play_next_song(voice_client)

    @yt.sub_command(description="Приостанавливает воспроизведение музыки")
    async def pause(self, interaction):
        voice_client = disnake.utils.get(self.bot.voice_clients, guild=interaction.guild)
        if interaction.author.voice is None:
            await interaction.response.send_message(
                "Вы должны находиться в голосовом канале для использования этой команды.", ephemeral=True)
            return

        if voice_client and voice_client.is_playing():
            voice_client.pause()
            music_queue.is_paused = True
            await interaction.response.send_message("Музыка приостановлена.")
        else:
            await interaction.response.send_message("В данный момент ничего не воспроизводится.")

    @yt.sub_command(description="Возобновляет воспроизведение музыки")
    async def resume(self, interaction):
        voice_client = disnake.utils.get(self.bot.voice_clients, guild=interaction.guild)
        if interaction.author.voice is None:
            await interaction.response.send_message(
                "Вы должны находиться в голосовом канале для использования этой команды.", ephemeral=True)
            return

        if voice_client and voice_client.is_paused():
            voice_client.resume()
            music_queue.is_paused = False
            await interaction.response.send_message("Музыка возобновлена.")
        else:
            await interaction.response.send_message("Музыка не приостановлена.")

    @yt.sub_command(description="Пропускает текущий трек и проигрывает следующий")
    async def skip(self, interaction):
        await interaction.response.defer()
        voice_client = disnake.utils.get(self.bot.voice_clients, guild=interaction.guild)
        if interaction.author.voice is None:
            await interaction.send(
                "Вы должны находиться в голосовом канале для использования этой команды.", ephemeral=True)
            return

        if voice_client and voice_client.is_playing():
            voice_client.stop()
            await interaction.send("Текущий трек был пропущен.")
            await play_next_song(voice_client)
        else:
            await interaction.send("В данный момент ничего не воспроизводится.")

    @yt.sub_command_group()
    async def queue(self, interaction):
        pass

    @queue.sub_command(description="Очищает очередь воспроизведения")
    async def clear(self, interaction):
        if interaction.author.voice is None:
            await interaction.response.send_message(
                "Вы должны находиться в голосовом канале для использования этой команды.", ephemeral=True)
            return
        music_queue.queue.clear()
        await interaction.response.send_message("Очередь воспроизведения очищена.")

    @queue.sub_command(description="Показывает текущую очередь воспроизведения")
    async def show(self, interaction):
        if interaction.author.voice is None:
            await interaction.response.send_message(
                "Вы должны находиться в голосовом канале для использования этой команды.", ephemeral=True)
            return
        if music_queue.queue:
            queue_text = "Текущая очередь воспроизведения:\n"
            for index, url in enumerate(music_queue.queue, start=1):
                queue_text += f"{index}. {url}\n"
            await interaction.response.send_message(queue_text)
        else:
            await interaction.response.send_message("Очередь воспроизведения пуста.")

    @yt.error
    async def play_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Пожалуйста, укажите URL трека.")
        else:
            await ctx.send(f"Произошла ошибка при выполнении команды: {error}")


def setup(bot):
    bot.add_cog(YouTubeMusic(bot))
