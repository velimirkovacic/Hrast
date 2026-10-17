
import discord
from discord.ext import commands
from youtubesearchpython import VideosSearch
from yt_dlp import YoutubeDL
import asyncio
import random
import logging
import traceback
from datetime import datetime
import os
import shutil
import tempfile

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
        self._current_temp_dir = None
        self._playback_lock = asyncio.Lock()
        # Queue entries: [song, voice_channel]
        self.music_queue = []

        self.YDL_OPTIONS = {"format": "bestaudio/best"}
        self.FFMPEG_OPTIONS = {"options": "-vn"}

        self.vc = None
        self.ytdl = YoutubeDL(self.YDL_OPTIONS)

        # Automatic disconnect timers
        self._idle_task = None
        self._alone_task = None
        self._disconnecting_automatically = False

        log.info("Music cog initialized")
        log.info("Restricted text channel: %s", self.spam_kanal)
        log.info("FFmpeg executable: /usr/bin/ffmpeg")
        log.info("Discord Opus loaded: %s", discord.opus.is_loaded())

    # ---------------------------------------------------------
    # Automatic voice disconnect timers
    # ---------------------------------------------------------

    def _cancel_timer(self, task_name):
        task = getattr(self, task_name)

        if task is not None and not task.done():
            if task is not asyncio.current_task():
                task.cancel()

        setattr(self, task_name, None)

    def _cancel_auto_disconnect_timers(self):
        self._cancel_timer("_idle_task")
        self._cancel_timer("_alone_task")

    def _schedule_idle_disconnect(self):
        """Disconnect after 5 minutes without playing or queued music."""
        vc = self.vc

        if (
            vc is None
            or not vc.is_connected()
            or self.music_queue
            or self.is_playing
            or self.is_paused
            or vc.is_playing()
            or vc.is_paused()
        ):
            self._cancel_timer("_idle_task")
            return

        self._cancel_timer("_idle_task")
        self._idle_task = self.bot.loop.create_task(
            self._idle_disconnect_after_delay()
        )
        log.info("Idle timer started: disconnect in 5 minutes")

    async def _idle_disconnect_after_delay(self):
        try:
            await asyncio.sleep(300)

            if self._disconnecting_automatically:
                log.info("Idle disconnect skipped: automatic disconnect already in progress")
                return

            vc = self.vc

            if (
                vc is None
                or not vc.is_connected()
                or self.music_queue
                or self.is_playing
                or self.is_paused
                or vc.is_playing()
                or vc.is_paused()
            ):
                log.info("Idle timer expired, but music is no longer idle")
                return

            log.info("5-minute idle timeout reached; disconnecting")
            await vc.disconnect()

            if self.vc is vc:
                self.vc = None

            self.is_playing = False
            self.is_paused = False

        except asyncio.CancelledError:
            raise
        except Exception:
            log.exception("Idle auto-disconnect failed")
        finally:
            if self._idle_task is asyncio.current_task():
                self._idle_task = None

    def _schedule_alone_disconnect(self):
        """Disconnect after 1 minute with no human members in voice."""
        vc = self.vc

        if vc is None or not vc.is_connected():
            self._cancel_timer("_alone_task")
            return

        humans_present = any(
            not member.bot for member in vc.channel.members
        )

        if humans_present:
            self._cancel_timer("_alone_task")
            return

        # Do not restart an existing countdown on unrelated voice events.
        if self._alone_task is not None and not self._alone_task.done():
            return

        self._alone_task = self.bot.loop.create_task(
            self._alone_disconnect_after_delay()
        )
        log.info(
            "Bot is alone; disconnect timer started for 1 minute "
            "(playback state does not matter)"
        )


    async def _alone_disconnect_after_delay(self):
        try:
            await asyncio.sleep(60)

            vc = self.vc

            if vc is None or not vc.is_connected():
                return

            humans_present = any(
                not member.bot for member in vc.channel.members
            )

            if humans_present:
                log.info("Alone timer expired; a human is present")
                return

            self._disconnecting_automatically = True

            try:
                log.info(
                    "1-minute alone timeout reached; disconnecting "
                    "(stopping playback if necessary)"
                )

                self.music_queue.clear()

                if vc.is_playing() or vc.is_paused():
                    vc.stop()

                self.is_playing = False
                self.is_paused = False

                await vc.disconnect()

                if self.vc is vc:
                    self.vc = None

                log.info("Disconnected because no humans remained in voice")

            finally:
                self._disconnecting_automatically = False

        except asyncio.CancelledError:
            raise
        except Exception:
            log.exception("Alone auto-disconnect failed")
        finally:
            if self._alone_task is asyncio.current_task():
                self._alone_task = None



    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """Start or cancel the alone timer when people change voice channels."""
        vc = self.vc

        if vc is None or not vc.is_connected():
            return

        if member.guild.id != vc.guild.id:
            return

        # Only react to changes involving the bot's current voice channel.
        if (
            member.id != self.bot.user.id
            and before.channel != vc.channel
            and after.channel != vc.channel
        ):
            return

        self._schedule_alone_disconnect()

    # ---------------------------------------------------------
    # YouTube search
    # ---------------------------------------------------------
    def _download_song(self, url, temp_dir):
        """Download a song and return its local file path and metadata."""
        options = dict(self.YDL_OPTIONS)
        options.update({
            "outtmpl": os.path.join(temp_dir, "%(id)s.%(ext)s"),
            "noplaylist": True,
        })

        log.info("Downloading song to temporary directory: %s", temp_dir)

        with YoutubeDL(options) as ytdl:
            data = ytdl.extract_info(url, download=True)

            if not data:
                raise RuntimeError("yt-dlp returned no song metadata")

            downloads = data.get("requested_downloads") or []
            filepath = downloads[0].get("filepath") if downloads else None

            if not filepath:
                filepath = ytdl.prepare_filename(data)

        if not os.path.isfile(filepath):
            raise FileNotFoundError(
                f"Downloaded audio file was not found: {filepath}"
            )

        log.info(
            "Download completed: title=%r file=%s size=%d bytes",
            data.get("title"),
            filepath,
            os.path.getsize(filepath),
        )

        return filepath, data

    def _cleanup_current_download(self):
        """Delete the temporary directory for the finished song."""
        temp_dir = self._current_temp_dir
        self._current_temp_dir = None

        if not temp_dir:
            return

        try:
            shutil.rmtree(temp_dir)
            log.info("Deleted temporary audio directory: %s", temp_dir)
        except FileNotFoundError:
            log.info("Temporary audio directory already deleted: %s", temp_dir)
        except Exception:
            log.exception(
                "Failed to delete temporary audio directory: %s",
                temp_dir,
            )


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

    # ---------------------------------------------------------
    # Audio playback callbacks
    # ---------------------------------------------------------


    def _playback_finished(self, error):
        """Called by discord.py from the audio player's thread."""
        if error:
            log.error(
                "Audio playback callback received an error: %r",
                error,
            )
        else:
            log.info("Audio playback finished normally")

        # FFmpeg has finished reading this song. Linux allows the file to
        # be unlinked even if the FFmpeg process is finishing its cleanup.
        self._cleanup_current_download()

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
        await self._start_next_downloaded_song()

    async def play_music(self, ctx):
        await self._start_next_downloaded_song(ctx)

    async def _start_next_downloaded_song(self, ctx=None):
        """Serialize playback startup so only one task starts a song."""
        async with self._playback_lock:
            await self._start_next_downloaded_song_locked(ctx)


    async def _start_next_downloaded_song_locked(self, ctx=None):
        """Download and play queued songs, skipping songs that fail."""
        log.info(
            "Starting downloaded-file playback; queue length=%d "
            "voice_client=%r",
            len(self.music_queue),
            self.vc,
        )

        if self._disconnecting_automatically:
            log.info("Playback skipped: automatic disconnect in progress")
            return

        self._cancel_timer("_idle_task")

        while self.music_queue:
            song_info, channel = self.music_queue[0]
            m_url = song_info["source"]

            log.info(
                "Preparing queued song: title=%r url=%s channel=%s (%s)",
                song_info.get("title"),
                m_url,
                getattr(channel, "name", "unknown"),
                getattr(channel, "id", "unknown"),
            )

            # Ensure the bot is connected to the song's voice channel.
            try:
                if self.vc is None or not self.vc.is_connected():
                    log.info(
                        "Connecting to voice channel: %s",
                        getattr(channel, "name", "unknown"),
                    )
                    self.vc = await channel.connect(
                        timeout=20,
                        reconnect=True,
                    )

                elif self.vc.channel != channel:
                    log.info(
                        "Moving voice connection from %s to %s",
                        getattr(self.vc.channel, "name", "unknown"),
                        getattr(channel, "name", "unknown"),
                    )
                    await self.vc.move_to(channel)

            except Exception:
                self.is_playing = False
                log.exception(
                    "Could not connect to the voice channel for %r",
                    song_info.get("title"),
                )

                if ctx is not None:
                    try:
                        await ctx.send("Ne mogu se spojiti na glasovni kanal!")
                    except Exception:
                        log.exception("Could not report voice connection failure")

                # Keep the song queued so a later command can retry.
                self._schedule_idle_disconnect()
                return

            # Remove this song before attempting the download. If the
            # download fails, the loop continues to the next queued song.
            self.music_queue.pop(0)
            temp_dir = tempfile.mkdtemp(prefix="hrast-")

            try:
                loop = asyncio.get_running_loop()

                log.info(
                    "Downloading queued song: title=%r",
                    song_info.get("title"),
                )

                filepath, data = await loop.run_in_executor(
                    None,
                    self._download_song,
                    m_url,
                    temp_dir,
                )

                if not self.vc or not self.vc.is_connected():
                    raise RuntimeError(
                        "Voice connection was lost during the download"
                    )

                if not discord.opus.is_loaded():
                    log.warning(
                        "Opus is not loaded. Check "
                        "discord.opus.load_opus('libopus.so.0') at startup."
                    )

                log.info(
                    "Creating FFmpeg source from downloaded file: %s",
                    filepath,
                )

                source = discord.FFmpegPCMAudio(
                    filepath,
                    executable="/usr/bin/ffmpeg",
                    options="-vn",
                )

                # Track the directory before starting playback so the
                # callback can clean it up when playback finishes.
                self._current_temp_dir = temp_dir

                log.info("Starting local-file playback: title=%r", data.get("title"))

                self.vc.play(
                    source,
                    after=self._playback_finished,
                )

                self.is_playing = True
                self.is_paused = False

                log.info(
                    "Local-file playback started; title=%r connected=%s "
                    "playing=%s paused=%s",
                    data.get("title"),
                    self.vc.is_connected(),
                    self.vc.is_playing(),
                    self.vc.is_paused(),
                )
                return

            except Exception:
                log.exception(
                    "Download or playback setup failed for title=%r; "
                    "skipping to the next queued song",
                    song_info.get("title"),
                )

                if self._current_temp_dir == temp_dir:
                    self._current_temp_dir = None

                try:
                    shutil.rmtree(temp_dir)
                    log.info("Deleted failed song's temporary files: %s", temp_dir)
                except FileNotFoundError:
                    pass
                except Exception:
                    log.exception(
                        "Failed to delete temporary files for %r",
                        song_info.get("title"),
                    )

                # Continue the loop to try the next song in the queue.

        self.is_playing = False
        self.is_paused = False

        log.info("Queue empty; is_playing=False")
        self._schedule_idle_disconnect()

    # ---------------------------------------------------------
    # Commands
    # ---------------------------------------------------------

    @commands.command(
        name="sviraj",
        aliases=["pusti", "pjevaj", "dodaj"],
        help="Plays a selected song from YouTube",
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
            self._cancel_timer("_idle_task")

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
            log.error("sviraj command failed:\n%s", traceback.format_exc())
            await ctx.send(
                "Neću, to je slop..."
            )

    @commands.command(
        name="zaustavi",
        aliases=["pauziraj"],
        help="Pauses or resumes the current song",
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
        help="Skips the current song",
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

    @commands.command(name="red", help="Displays the current queue")
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
        help="Stops music and clears the queue",
    )
    async def clear(self, ctx):
        log.info("Clear queue command received")

        if str(ctx.channel) != self.spam_kanal:
            log.warning("Clear command rejected: wrong text channel")
            return

        self.music_queue.clear()

        if (self.vc
                and self.vc.is_connected()
                and (self.vc.is_playing() or self.vc.is_paused())
            ):            
            log.info("Stopping current playback")
            self.vc.stop()
        else:
            self.is_playing = False
            self.is_paused = False
            self._schedule_idle_disconnect()
        
        log.info("Queue cleared")
        await ctx.send("Očistio sam sve!")

    @commands.command(
        name="bježi",
        aliases=["izađi", "mrš"],
        help="Disconnects the bot from voice",
    )
    async def dc(self, ctx):
        log.info("Disconnect command received")

        if str(ctx.channel) != self.spam_kanal:
            log.warning("Disconnect command rejected: wrong text channel")
            return

        self._cancel_auto_disconnect_timers()
        self.is_playing = False
        self.is_paused = False
        self.music_queue.clear()

        if self.vc and self.vc.is_connected():
            log.info("Disconnecting from voice channel")
            vc = self.vc
            await vc.disconnect()
            self._cleanup_current_download()

            if self.vc is vc:
                self.vc = None

            log.info("Disconnected from voice")
        else:
            log.info("Disconnect requested, but bot is not connected")

    @commands.command(
        name="ukloni",
        aliases=["izbaci", "makni"],
        help="Removes the last queued song",
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

            if not self.music_queue and not self.is_playing and not self.is_paused:
                self._schedule_idle_disconnect()
        else:
            log.warning("Remove requested but queue is empty")
            await ctx.send("Red je prazan, nema što ukloniti!")
