import discord
import logging
import random
import re

from redbot.core import checks, Config, commands, bot

log = logging.getLogger("red.cbd-cogs.markov")

__all__ = ["UNIQUE_ID", "Markov"]

UNIQUE_ID = 0x6D61726B6F76
WORD_PATTERN = re.compile(r'(\W+)')
CONTROL = f"{UNIQUE_ID}"

class Markov(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.conf = Config.get_conf(self, identifier=UNIQUE_ID, force_registration=True)
        self.conf.register_user(markov_chain={}, markov_enabled=False)
        self.conf.register_guild(markov_channels=[])

    @commands.Cog.listener()
    async def on_message(self, message):
        # Attempt to load guild channel restrictions
        try:
            channels = await self.conf.guild(message.guild).markov_channels()
            if message.channel.id not in channels:
                return
        except AttributeError:  # Not in a guild
            pass
        # Ignore messages from the bot itself
        if message.author.id == self.bot.user.id:
            return
        # Ignore messages that start with non-alphanumeric characters
        if message.content and not message.content[0].isalnum():
            return
        # Check whether the user has enabled markov modeling
        enabled = await self.conf.user(message.author).markov_enabled()
        if not enabled:
            return
        # Load the user's markov chain
        chain = await self.conf.user(message.author).markov_chain()
        # Begin all state chains with the control marker
        previous_word = CONTROL
        # Iterate over the tokens in the message
        for word in WORD_PATTERN.split(message.content):
            # Remove code block formatting and outer whitespace
            word = word.replace('`', '').strip()
            # Skip if the token was made empty by the previous line
            if not word:
                continue
            # Get the vector distribution for the current state, or new dict
            chain[previous_word] = chain.get(previous_word, {})
            # Get the current weight for this state vector, or 0
            count = chain[previous_word].get(word, 0)
            # Record the new vector weight
            chain[previous_word][word] = count + 1
            previous_word = word
        # Update the chain one more time to record the control transition
        chain[previous_word] = chain.get(previous_word, {})
        count = chain[previous_word].get(CONTROL, 0)
        chain[previous_word][CONTROL] = count + 1
        # Store the model
        await self.conf.user(message.author).markov_chain.set(chain)
    
    async def generate_text(self, chain):
        output = []
        word = CONTROL
        while word:
            # Choose the next word taking into account recorded vector weights
            new_word = random.choices(list(chain[word].keys()),
                                      weights=list(chain[word].values()),
                                      k=1)[0]
            # Don't worry about it ;)
            prepend_space = all((word != CONTROL,
                                 new_word[-1].isalnum() or new_word in "\"([{|",
                                 word not in "\"([{'/-"))
            # End of message has been reached
            if new_word == CONTROL:
                word = None
                continue
            word = new_word
            output.append(f" {word}" if prepend_space else word)
        return "".join(output)

    @commands.command()
    async def markov(self, ctx: commands.Context, user: discord.abc.User = None):
        try:
            channels = await self.conf.guild(ctx.guild).markov_channels()
            if ctx.channel.id not in channels:
                return
        except AttributeError:  # Not in a guild
            pass
        if not isinstance(user, discord.abc.User):
            user = ctx.message.author
        enabled = await self.conf.user(user).markov_enabled()
        if not enabled:
            await ctx.send(f"Sorry, {user} won't let me model their speech")
            return
        chain = await self.conf.user(user).markov_chain()
        try:
            text = None
            i = 0
            while not text:
                text = await self.generate_text(chain)
                if i > 3:
                    break
                i += 1
        except KeyError:
            await ctx.send(f"Sorry, I do not have a markov chain for {user}")
            return
        await ctx.send(text[:2000])

    @commands.command()
    async def markovenable(self, ctx: commands.Context):
        await self.conf.user(ctx.author).markov_enabled.set(True)

    @commands.command()
    async def markovdisable(self, ctx: commands.Context):
        await self.conf.user(ctx.author).markov_enabled.set(False)
        await self.conf.user(ctx.author).markov_chain.set({})

    @checks.admin_or_permissions(manage_guild=True)
    @commands.guild_only()
    @commands.command()
    async def markovchannelenable(self, ctx: commands.Context, channel: str = None):
        if not channel:
            channel = ctx.channel.id
        channels = await self.conf.guild(ctx.guild).markov_channels()
        channels.append(int(channel))
        await self.conf.guild(ctx.guild).markov_channels.set(channels)

    @checks.admin_or_permissions(manage_guild=True)
    @commands.guild_only()
    @commands.command()
    async def markovchanneldisable(self, ctx: commands.Context, channel: str = None):
        if not channel:
            channel = ctx.channel.id
        channels = await self.conf.guild(ctx.guild).markov_channels()
        channels.remove(int(channel))
        await self.conf.guild(ctx.guild).markov_channels.set(channels)

    @checks.is_owner()
    @commands.command(hidden=True)
    async def markovreset(self, ctx: commands.Context, user: discord.abc.User):
        await self.conf.user(user).markov_chain.set({})
