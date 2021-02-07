import discord
import inspirobot
from redbot.core import commands

class Inspire(commands.Cog):
    """ Provides inspiration from the InspiroBot API """
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def inspire(self, ctx: commands.Context):
        """ Become someone who is inspired """
        inspiration = inspirobot.generate()
        embed = discord.Embed(url=inspiration.url, title = f"Inspiration for {ctx.author.display_name}")
        embed.set_image(url=inspiration.url)
        await ctx.send(embed=embed)
