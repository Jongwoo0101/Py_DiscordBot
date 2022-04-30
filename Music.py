import asyncio

import discord
from discord.ext import commands

from youtube_downloader import YoutubeDownloader


# 이 명령을 실행하려면 PyNaCl패키지를 설치해야 합니다.
class Music(commands.Cog):
    def __init__(self, bot):
        self.search_request_user = None
        self.search_response = None
        self.bot = bot
        self.volume = 0.5
        self.music_queue = asyncio.Queue()

    @commands.command(aliases = ['move', 'j', 'm'])
    async def join(self, ctx, *, channel: discord.VoiceChannel):
        if ctx.voice_client is not None:
            return await ctx.voice_client.move_to(channel)

        await channel.connect()

    @commands.command(aliases = ['play', 'p'])
    async def stream(self, ctx, *, url):
        async with ctx.typing():
            player = await YoutubeDownloader.from_url(url, loop = self.bot.loop, stream = True)
            await self.music_queue.put(player)

            # 큐가 비어있었으므로 수동으로 재생합니다.
            if not ctx.voice_client.is_playing() and self.music_queue.qsize() == 1:
                return await self.on_play_completed(ctx)

        if ctx.voice_client.is_playing():
            embed = discord.Embed(title = f':notes: {player.title}',
                                  description = f'음원 링크: [Url]({player.url})',
                                  colour = discord.Colour.blue())
            embed.set_thumbnail(url = player.thumbnail)
            embed.add_field(name = 'Queue', value = f'대기열: {self.music_queue.qsize()}', inline = False)
            embed.set_footer(text = ctx.author, icon_url = ctx.author.avatar)
            await ctx.reply(embed = embed)

    async def on_play_completed(self, ctx, force_complete = False, invoke_self = False):
        if self.music_queue.qsize() == 0 or (ctx.voice_client.is_playing() and not force_complete):
            return

        pending_player = await self.music_queue.get()

        async with ctx.typing():
            ctx.voice_client.play(pending_player, after = lambda e: asyncio.run_coroutine_threadsafe(
                self.on_play_completed(ctx, invoke_self = True), self.bot.loop))
            ctx.voice_client.source.volume = self.volume

        if not invoke_self:
            embed = discord.Embed(title = f':notes: {pending_player.title}',
                                  description = f'음원 링크: [Url]({pending_player.url})',
                                  colour = discord.Colour.green())
            embed.set_thumbnail(url = pending_player.thumbnail)
            embed.set_footer(text = ctx.author, icon_url = ctx.author.avatar)
            await ctx.send(embed = embed)

    @commands.command(aliases = ['q'])
    async def search(self, ctx, *, query):
        self.search_request_user = ctx.author
        async with ctx.typing():
            self.search_response = YoutubeDownloader.search(query)
            embed = discord.Embed(title = ':mag: Search', description = '원하는 것을 번호로 골라주세요.',
                                  colour = discord.Colour.blue())

        for i in range(0, len(self.search_response)):
            video = self.search_response[i]
            embed.add_field(name = f'*{i + 1}.*', value = f'**[{video["title"]}]({video["url"]})**', inline = False)
        else:
            embed.set_footer(text = ctx.author, icon_url = ctx.author.avatar)
            await ctx.reply(embed = embed)

    @commands.command(aliases = ['sel', '1', '2', '3', '4', '5'])
    async def select(self, ctx, *, number = ''):
        if self.search_request_user != ctx.author:
            return

        if not number.isdigit():
            if ctx.invoked_with.isdigit():
                number = int(ctx.invoked_with)
            else:
                return await ctx.reply('?')

        self.search_request_user = None
        await self.ensure_voice(ctx)
        return await self.stream(ctx, url = self.search_response[int(number) - 1]['url'])

    @commands.command(aliases = ['v'])
    async def volume(self, ctx, volume: int):
        if ctx.voice_client is None:
            return await ctx.reply('음성채널에 연결되어있지 않습니다.')

        if ctx.voice_client.source is None:
            return await ctx.reply('재생 중인 음악이 없습니다.')

        old_volume = ctx.voice_client.source.volume
        ctx.voice_client.source.volume = self.volume = volume / 100
        await ctx.reply(
            embed = discord.Embed(title = ':speaker: Volume',
                                  description = f'**{round(old_volume * 100)}%** :arrow_right: **{volume}%**',
                                  colour = discord.Colour.blue()))

    @commands.command(aliases = ['s'])
    async def skip(self, ctx):
        if ctx.voice_client is None:
            return

        if ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            await self.on_play_completed(ctx, True)

    @commands.command(aliases = ['l'])
    async def leave(self, ctx):
        self.music_queue = asyncio.Queue()  # 나가면 음악 대기열을 비우도록 합니다.
        await ctx.voice_client.disconnect()

    @leave.before_invoke
    @stream.before_invoke
    async def ensure_voice(self, ctx):
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.reply('음성채널에 연결되어있지 않습니다.')
