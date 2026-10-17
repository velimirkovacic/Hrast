
import discord
from discord.ext import commands
from youtubesearchpython import VideosSearch
from yt_dlp import YoutubeDL
import asyncio
import random
import logging
import traceback
from datetime import datetime


# Timestamped logging to Docker stdout
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [MUSIC] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("music_cog")


class music_cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.spam_kanal = "mudrosti-mističnoga-hrasta"

        self.is_playing = False
        self.is_paused = False

        # Queue entries: [song, voice_channel]
        self.music_queue = []

        self.YDL_OPTIONS = {"format": "bestaudio/best"}
        self.FFMPEG_OPTIONS = {"options": "-vn"}

        self.vc = None
        self.ytdl = YoutubeDL(self.YDL_OPTIONS)

        log.info("Music cog initialized")
        log.info("Restricted text channel: %s", self.spam_kanal)
        log.info("FFmpeg executable: /usr/bin/ffmpeg")
        log.info("Discord Opus loaded: %s", discord.opus.is_loaded())

    def search_yt(self, item):
        log.info("YouTube search started: query=%r", item)

        try:
            if item.startswith("https://"):
                log.info("Input appears to be a URL")
                info = self.ytdl.extract_info(item, download=False)
                result = {
                    "source": item,
                    "title": info["title"],
                }
                log.info("URL resolved: title=%r", result["title"])
                return result

            search = VideosSearch(item, limit=1)
            results = search.result().get("result", [])

            if not results:
                log.warning("YouTube search returned no results for %r", item)
                return True

            result = {
                "source": results[0]["link"],
                "title": results[0]["title"],
            }
            log.info(
                "YouTube result: title=%r url=%s",
                result["title"],
                result["source"],
            )
            return result

        except Exception:
            log.exception("YouTube search/extraction failed for query=%r", item)
            raise

    def _playback_finished(self, error):
        """Called by discord.py from the audio player's thread."""
        if error:
            log.error(
                "Audio playback callback received an error: %r",
                error,
            )
        else:
            log.info("Audio playback finished normally")

        try:
            future = asyncio.run_coroutine_threadsafe(
                self.play_next(),
                self.bot.loop,
            )

            def report_result(fut):
                try:
                    fut.result()
                except Exception:
                    log.exception("play_next() failed after playback callback")

            future.add_done_callback(report_result)

        except Exception:
            log.exception("Could not schedule play_next() from playback callback")

    async def play_next(self):
        log.info(
            "play_next called; queue length=%d; voice_client=%r",
            len(self.music_queue),
            self.vc,
        )

        if not self.music_queue:
            self.is_playing = False
            log.info("Queue empty; is_playing=False")
            return

        self.is_playing = True

        try:
            song_info, channel = self.music_queue[0]
            m_url = song_info["source"]

            log.info(
                "Next queued song: title=%r url=%s channel=%s (%s)",
                song_info.get("title"),
                m_url,
                getattr(channel, "name", "unknown"),
                getattr(channel, "id", "unknown"),
            )

            self.music_queue.pop(0)

            loop = asyncio.get_running_loop()
            log.info("Extracting audio stream for next song")

            data = await loop.run_in_executor(
                None,
                lambda: self.ytdl.extract_info(m_url, download=False),
            )

            if not data or not data.get("url"):
                raise RuntimeError("yt-dlp returned no audio stream URL")

            stream_url = data["url"]
            log.info(
                "Audio stream extracted; title=%r",
                data.get("title"),
            )

            if self.vc is None or not self.vc.is_connected():
                log.error("Cannot play next song: voice client is disconnected")
                self.is_playing = False
                return

            log.info(
                "Starting FFmpeg playback; connected=%s playing=%s paused=%s",
                self.vc.is_connected(),
                self.vc.is_playing(),
                self.vc.is_paused(),
            )

            source = discord.FFmpegPCMAudio(
                stream_url,
                executable="/usr/bin/ffmpeg",
                before_options=(
                    "-reconnect 1 -reconnect_streamed 1 "
                    "-reconnect_delay_max 5"
                ),
                options="-vn",
            )

            self.vc.play(source, after=self._playback_finished)
            log.info("vc.play() returned successfully for next song")

        except Exception:
            self.is_playing = False
            log.error("play_next() failed:\n%s", traceback.format_exc())

    async def play_music(self, ctx):
        log.info(
            "play_music called; queue length=%d; is_playing=%s; is_paused=%s",
            len(self.music_queue),
            self.is_playing,
            self.is_paused,
        )

        if not self.music_queue:
            self.is_playing = False
            log.info("play_music: queue is empty")
            return

        try:
            song_info, channel = self.music_queue[0]
            m_url = song_info["source"]

            log.info(
                "Preparing song: title=%r channel=%s channel_id=%s",
                song_info.get("title"),
                getattr(channel, "name", "unknown"),
                getattr(channel, "id", "unknown"),
            )

            if self.vc is None or not self.vc.is_connected():
                log.info("No active voice connection; attempting channel.connect()")
                log.info(
                    "Target voice channel: name=%s id=%s guild_id=%s",
                    getattr(channel, "name", "unknown"),
                    getattr(channel, "id", "unknown"),
                    getattr(getattr(channel, "guild", None), "id", "unknown"),
                )

                self.vc = await channel.connect(timeout=20, reconnect=True)

                log.info(
                    "channel.connect() returned: voice_client=%r connected=%s",
                    self.vc,
                    self.vc.is_connected() if self.vc else False,
                )

                if self.vc is None:
                    self.is_playing = False
                    log.error("channel.connect() returned None")
                    await ctx.send("Ne mogu se spojiti!")
                    return

            else:
                log.info(
                    "Already connected to voice channel %s; moving to %s",
                    getattr(getattr(self.vc, "channel", None), "name", "unknown"),
                    getattr(channel, "name", "unknown"),
                )
                await self.vc.move_to(channel)
                log.info("move_to() completed")

            # Remove the queued song only after connection succeeds.
            self.music_queue.pop(0)
            log.info("Song removed from queue; remaining=%d", len(self.music_queue))

            loop = asyncio.get_running_loop()
            log.info("Extracting audio stream for %r", song_info.get("title"))

            data = await loop.run_in_executor(
                None,
                lambda: self.ytdl.extract_info(m_url, download=False),
            )

            if not data or not data.get("url"):
                raise RuntimeError("yt-dlp returned no audio stream URL")

            stream_url = data["url"]
            log.info("Stream URL extracted; title=%r", data.get("title"))

            if not discord.opus.is_loaded():
                log.warning(
                    "Opus is not loaded. PCM voice playback may fail. "
                    "Check discord.opus.load_opus('libopus.so.0') at startup."
                )

            log.info("Creating FFmpeg audio source")

            source = discord.FFmpegPCMAudio(
                stream_url,
                executable="/usr/bin/ffmpeg",
                before_options=(
                    "-reconnect 1 -reconnect_streamed 1 "
                    "-reconnect_delay_max 5"
                ),
                options="-vn",
            )

            log.info("Calling voice_client.play()")

            self.vc.play(source, after=self._playback_finished)

            self.is_playing = True
            log.info(
                "Playback started; connected=%s playing=%s paused=%s",
                self.vc.is_connected(),
                self.vc.is_playing(),
                self.vc.is_paused(),
            )

        except Exception as e:
            self.is_playing = False
            log.error(
                "play_music failed: %s: %s\n%s",
                type(e).__name__,
                e,
                traceback.format_exc(),
            )
            try:
                await ctx.send(
                    f"Greška pri pokretanju glazbe: {type(e).__name__}: {e}"
                )
            except Exception:
                log.exception("Could not send playback error to Discord")

    @commands.command(
        name="sviraj",
        aliases=["pusti", "pjevaj", "dodaj"],
        help="Plays a selected song from youtube",
    )
    async def play(self, ctx, *args):
        log.info(
            "sviraj command received; user=%s user_id=%s text_channel=%s "
            "guild=%s guild_id=%s args=%r",
            getattr(ctx.author, "name", "unknown"),
            getattr(ctx.author, "id", "unknown"),
            getattr(ctx.channel, "name", "unknown"),
            getattr(ctx.guild, "name", "unknown"),
            getattr(ctx.guild, "id", "unknown"),
            args,
        )

        if str(ctx.channel) != self.spam_kanal:
            log.warning(
                "Command rejected: wrong text channel %r; expected %r",
                str(ctx.channel),
                self.spam_kanal,
            )
            await ctx.send("Krivi kanal, kmico...")
            return

        query = " ".join(args)
        log.info("Search query=%r", query)

        if not query.strip():
            log.warning("Command received without a search query")
            await ctx.send("Napiši koju pjesmu želiš pustiti!")
            return

        voice_state = getattr(ctx.author, "voice", None)
        voice_channel = getattr(voice_state, "channel", None)

        if voice_channel is None:
            log.warning(
                "Command rejected: user %s is not in a voice channel",
                getattr(ctx.author, "name", "unknown"),
            )
            await ctx.send("Nisi u glasovnom kanalu, kmico!")
            return

        log.info(
            "User voice channel: name=%s id=%s guild_id=%s",
            voice_channel.name,
            voice_channel.id,
            voice_channel.guild.id,
        )

        try:
            if random.randint(1, 200) == 59:
                log.info("Random joke-song branch selected")
                await ctx.send("Neću, to je krindž.")
                song = await asyncio.get_running_loop().run_in_executor(
                    None,
                    lambda: self.search_yt("Buba Corelli Gluh i nijem"),
                )
            else:
                log.info("Searching for requested song")
                song = await asyncio.get_running_loop().run_in_executor(
                    None,
                    lambda: self.search_yt(query),
                )

            if song is True:
                log.warning("No song result found")
                await ctx.send("Neš si sjebo.")
                return

            log.info(
                "Song selected: title=%r url=%s",
                song.get("title"),
                song.get("source"),
            )

            if self.is_playing:
                await ctx.send(
                    f"**#{len(self.music_queue) + 2} -'{song['title']}'** "
                    "dodano u red čekanja"
                )
            else:
                await ctx.send(f"**'{song['title']}'** dodano u red čekanja")

            self.music_queue.append([song, voice_channel])
            log.info("Song queued; queue length=%d", len(self.music_queue))

            if not self.is_playing and not self.is_paused:
                log.info("Playback idle; calling play_music()")
                await self.play_music(ctx)
            else:
                log.info(
                    "Not starting playback now; is_playing=%s is_paused=%s",
                    self.is_playing,
                    self.is_paused,
                )

        except Exception:
            log.error(
                "sviraj command failed:\n%s",
                traceback.format_exc(),
            )
            await ctx.send("Došlo je do greške pri traženju pjesme. Pogledaj Docker logove.")

    @commands.command(
        name="zaustavi",
        aliases=["pauziraj"],
        help="Pauses the current song being played",
    )
    async def pause(self, ctx, *args):
        log.info("Pause command received")

        if str(ctx.channel) != self.spam_kanal:
            log.warning("Pause command rejected: wrong text channel")
            return

        if self.is_playing and self.vc and self.vc.is_connected():
            log.info("Pausing playback")
            self.is_playing = False
            self.is_paused = True
            self.vc.pause()
        elif self.is_paused and self.vc and self.vc.is_connected():
            log.info("Resuming playback through pause command")
            self.is_paused = False
            self.is_playing = True
            self.vc.resume()
        else:
            log.warning("Pause command ignored: no active playback")

    @commands.command(
        name="nastavi",
        aliases=["odpauziraj"],
        help="Resumes playing with the Discord bot",
    )
    async def resume(self, ctx, *args):
        log.info("Resume command received")

        if str(ctx.channel) != self.spam_kanal:
            log.warning("Resume command rejected: wrong text channel")
            return

        if self.is_paused and self.vc and self.vc.is_connected():
            self.is_paused = False
            self.is_playing = True
            self.vc.resume()
            log.info("Playback resumed")
        else:
            log.warning("Resume ignored: not paused or voice disconnected")

    @commands.command(
        name="dalje",
        aliases=["sljedeća"],
        help="Skips the current song being played",
    )
    async def skip(self, ctx):
        log.info("Skip command received")

        if str(ctx.channel) != self.spam_kanal:
            log.warning("Skip command rejected: wrong text channel")
            return

        if self.vc and self.vc.is_connected():
            log.info("Stopping current song to skip")
            self.vc.stop()
        else:
            log.warning("Skip requested but voice client is not connected")

    @commands.command(name="red", help="Displays the current songs in queue")
    async def queue(self, ctx):
        log.info("Queue command received")

        if str(ctx.channel) != self.spam_kanal:
            log.warning("Queue command rejected: wrong text channel")
            return

        if self.music_queue:
            retval = ""
            for i, entry in enumerate(self.music_queue):
                retval += f"#{i + 1} - {entry[0]['title']}\n"

            await ctx.send(f"Red:\n{retval}")
            log.info("Queue displayed; items=%d", len(self.music_queue))
        else:
            await ctx.send("Prazan ti je red, bato...")
            log.info("Queue is empty")

    @commands.command(
        name="počisti",
        aliases=["očisti"],
        help="Stops the music and clears the queue",
    )
    async def clear(self, ctx):
        log.info("Clear queue command received")

        if str(ctx.channel) != self.spam_kanal:
            log.warning("Clear command rejected: wrong text channel")
            return

        if self.vc and self.vc.is_connected() and self.vc.is_playing():
            log.info("Stopping current playback")
            self.vc.stop()

        self.music_queue.clear()
        self.is_playing = False
        log.info("Queue cleared")
        await ctx.send("Očistio sam sve!")

    @commands.command(
        name="bježi",
        aliases=["izađi", "mrš"],
        help="Kick the bot from VC",
    )
    async def dc(self, ctx):
        log.info("Disconnect command received")

        if str(ctx.channel) != self.spam_kanal:
            log.warning("Disconnect command rejected: wrong text channel")
            return

        self.is_playing = False
        self.is_paused = False

        if self.vc and self.vc.is_connected():
            log.info("Disconnecting from voice channel")
            await self.vc.disconnect()
            log.info("Disconnected from voice")
        else:
            log.warning("Disconnect requested but bot is not connected")

    @commands.command(
        name="ukloni",
        aliases=["izbaci", "makni"],
        help="Removes last song added to queue",
    )
    async def re(self, ctx):
        log.info("Remove-last-song command received")

        if str(ctx.channel) != self.spam_kanal:
            log.warning("Remove command rejected: wrong text channel")
            return

        if self.music_queue:
            removed = self.music_queue.pop()
            log.info("Removed queued song: %r", removed[0].get("title"))
            await ctx.send("posljednja pjesma uklonjena")
        else:
            log.warning("Remove requested but queue is empty")
            await ctx.send("Red je prazan, nema što ukloniti!")
