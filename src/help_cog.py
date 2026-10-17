import discord
from discord.ext import commands

class help_cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.help_message = ""
        self.text_channel_list = []
        self.set_message()

    def set_message(self):
        self.help_message = f"""

**Naredbe**:
{self.bot.command_prefix}stopala
{self.bot.command_prefix}pomoć
{self.bot.command_prefix}igraj

**Naredbe ISKLJUČIVO za kanal "bot-shit"**:
{self.bot.command_prefix}sviraj <ključne riječi>
{self.bot.command_prefix}red
{self.bot.command_prefix}dalje
{self.bot.command_prefix}počisti
{self.bot.command_prefix}bježi
{self.bot.command_prefix}zaustavi
{self.bot.command_prefix}nastavi
{self.bot.command_prefix}ukloni

"""

    @commands.Cog.listener()
    async def on_ready(self):
        await self.bot.change_presence(activity=discord.Game(f"Upiši \"pomoć\" za pomoć"))

    @commands.command(name="pomoć", help="Displays all the available commands")
    async def help(self, ctx):
        await ctx.send(self.help_message)
    
    @commands.command(name="igraj", help="Mijenja što igra")
    async def play_game(self, ctx, *args):
        await self.bot.change_presence(activity=discord.Game(" ".join(args)))

   
    #@commands.command(name="send_to_all", help="send a message to all members")
    #async def send_to_all(self, msg):
    #    for text_channel in self.text_channel_list:
    #        await text_channel.send(msg)

