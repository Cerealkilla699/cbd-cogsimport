import discord
import logging
import random
import re

from redbot.core import checks, Config, commands, bot

log = logging.getLogger("red.cbd-cogs.markov")

__all__ = ["UNIQUE_ID", "Markov"]

UNIQUE_ID = 0x6D61726B6F76
WORD_TOKENIZER = re.compile(r'([\W\']+)')
CONTROL = f"{UNIQUE_ID}"

class Markov(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.conf = Config.get_conf(self, identifier=UNIQUE_ID, force_registration=True)
        self.conf.register_user(markov_chain={}, chain_depth=1, token="word", markov_enabled=False)
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
        # Load the user's markov chain and settings
        chain = await self.conf.user(message.author).markov_chain()
        depth = await self.conf.user(message.author).chain_depth() or 1
        token = (await self.conf.user(message.author).token() or "word").lower()
        if token == "word":
            tokenizer = WORD_TOKENIZER
        elif token.startswith("ngram"):
            ngram_length = 3 if len(token) == 5 else token[5:]
            tokenizer = re.compile(fr'(.{{{ngram_length}}})')
        # Begin all state chains with the control marker
        state = CONTROL
        # Remove code block formatting and outer whitespace
        content = message.content.replace('`', '').strip()
        # Exclude empty or whitespace-only tokens
        tokens = [x for x in tokenizer.split(content) if x.strip()]
        # Iterate over the tokens in the message
        for i in range(1, len(tokens) + 1):
            # Get current token
            token = tokens[i-1]
            # Ensure dict key for vector distribution is created
            chain[state] = chain.get(state, {})
            # Increment the weight for this state vector or initialize it to 1
            chain[state][token] = chain[state].get(token, 0) + 1
            # Produce sliding state window
            j = i - depth if i > depth else 0
            state = "".join(tokens[j:i])
        # Update the chain one more time to record the control transition
        chain[state] = chain.get(state, {})
        count = chain[state].get(CONTROL, 0)
        chain[state][CONTROL] = count + 1
        # Store the model
        await self.conf.user(message.author).markov_chain.set(chain)

    async def generate_text(self, chain: dict, depth: int, mode: str):
        if mode == "word":
            return await self.generate_word_text(chain, depth)
        elif mode.startswith("ngram"):
            return await self.generate_ngram_text(chain, depth)
        else:
            return f"Sorry, I don't have a text generator for token mode '{mode}'"

    async def generate_word_text(self, chain: dict, depth: int):
        output = []
        i = 0
        gram = ""
        state = CONTROL
        while gram != CONTROL:
            log.info(f"New state: {state}")
            # Choose the next word taking into account recorded vector weights
            gram, = random.choices(population=list(chain[state].keys()),
                                   weights=list(chain[state].values()),
                                   k=1)
            # Don't worry about it ;)
            prepend_space = all((state != CONTROL,
                                 gram[-1].isalnum() or gram in "\"([{|",
                                 state[-1] not in "\"([{'/-_"))
            output.append(f" {gram}" if prepend_space else gram)
            i += 1
            j = i - depth if i > depth else 0
            state = "".join(output[j:i]).replace(" ", "")
        if not output:
            return
        return "".join(output[:-1])
    
    async def generate_ngram_text(self, chain: dict, depth: int):
        output = []
        i = 0
        gram = ""
        state = CONTROL
        while gram != CONTROL:
            # Choose a gram
            gram, = random.choices(population=list(chain[state].keys()),
                                   weights=list(chain[state].values()),
                                   k=1)
            output.append(gram)
            # Produce sliding state window
            i += 1
            j = i - depth if i > depth else 0
            state = "".join(output[j:i])
            # Increment pointer
        if not output:
            return
        return "".join(output[:-1])

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
        depth = await self.conf.user(user).chain_depth() or 1
        token = (await self.conf.user(user).token() or "word").lower()
        #try:
        text = None
        i = 0
        while not text:
            text = await self.generate_text(chain, depth, token)
            if i > 3:
                await ctx.send(f"I tried to generate text 3 times, now I'm giving up.")
                return
            i += 1
        #except KeyError:
        #    await ctx.send(f"Sorry, I do not have a markov chain for {user}")
        #    return
        await ctx.send(text[:2000])

    @commands.command()
    async def markovenable(self, ctx: commands.Context):
        await self.conf.user(ctx.author).markov_enabled.set(True)

    @commands.command()
    async def markovdisable(self, ctx: commands.Context):
        await self.conf.user(ctx.author).markov_enabled.set(False)
        await ctx.send("You may also want to run [p]markovreset to delete your language model")

    @commands.command()
    async def markovmode(self, ctx: commands.Context, mode: str):
        await self.conf.user(ctx.author).token.set(mode)
        await ctx.send("You may also want to run [p]markovreset to delete your language model")

    @commands.command()
    async def markovdepth(self, ctx: commands.Context, depth: int):
        await self.conf.user(ctx.author).chain_depth.set(depth)
        await ctx.send("You may also want to run [p]markovreset to delete your language model")

    @commands.command()
    async def markovshow(self, ctx: commands.Context, user: discord.abc.User = None):
        if not isinstance(user, discord.abc.User):
            user = ctx.message.author
        enabled = await self.conf.user(user).markov_enabled()
        chain = await self.conf.user(user).markov_chain()
        depth = await self.conf.user(user).chain_depth()
        token = await self.conf.user(user).token()
        await ctx.send(f"**Enabled:** {enabled}\n"
                       f"**Chain Depth:** {depth}\n"
                       f"**Token Mode:** {token}")

    @commands.command(hidden=True)
    async def markovreset(self, ctx: commands.Context):
        await self.conf.user(ctx.author).markov_chain.set({})

    @checks.admin_or_permissions(manage_guild=True)
    @commands.guild_only()
    @commands.command()
    async def markovchannelenable(self, ctx: commands.Context, channel: str = None):
        self.markov_channels_update(channel or ctx.channel.id, ctx.guild, True)

    @checks.admin_or_permissions(manage_guild=True)
    @commands.guild_only()
    @commands.command()
    async def markovchanneldisable(self, ctx: commands.Context, channel: str = None):
        self.markov_channels_update(channel or ctx.channel.id, ctx.guild, False)

    async def markov_channels_update(self, channel, guild, add: bool = True):
        channels = await self.conf.guild(guild).markov_channels()
        if add:
            channels.append(int(channel))
        else:
            channels.remove(int(channel))
        await self.conf.guild(guild).markov_channels.set(channels)
