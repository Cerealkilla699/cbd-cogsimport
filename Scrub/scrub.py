# -*- coding: utf-8 -*-
import aiohttp
import asyncio
import json
import logging
import re
from collections import namedtuple
from typing import Optional, Union
from urllib.parse import parse_qsl, unquote, urlencode, urlparse, urlunparse

import discord
from redbot.core import Config, bot, checks, commands

log = logging.getLogger("red.cbd-cogs.scrub")

__all__ = ["UNIQUE_ID", "Scrub"]

UNIQUE_ID = 0x7363727562626572
URL_PATTERN = re.compile(r'(https?://\S+)')
DEFAULT_URL = "https://kevinroebert.gitlab.io/ClearUrls/data/data.minify.json"


class Scrub(commands.Cog):
    """ Applies a set of rules to remove undesireable elements from hyperlinks
    
    URL parsing and processing functions based on code from \
        [Uroute](https://github.com/walterl/uroute)
    
    By default, this cog uses the URL cleaning rules provided by \
        [ClearURLs](https://gitlab.com/KevinRoebert/ClearUrls)
    """
    def __init__(self, bot: bot.Red, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bot = bot
        self.conf = Config.get_conf(self,
                                    identifier=UNIQUE_ID,
                                    force_registration=True)
        self.conf.register_global(rules={},
                                  threshold=2,
                                  url=DEFAULT_URL)

    def clean_url(self, url: str, rules: dict, loop: bool = True):
        """ Clean the given URL with the provided rules data.

        URLs matching a provider's `urlPattern` and one or more of that \
            provider's redirection patterns will cause the URL to be replaced \
            with the match's first matched group.
        """
        for provider_name, provider in rules.get('providers', {}).items():
            # Check provider urlPattern against provided URI
            if not re.match(provider['urlPattern'], url, re.IGNORECASE):
                continue

            # completeProvider is a boolean that determines if every url that
            # matches will be blocked. If you want to specify rules, exceptions
            # and/or redirections, the value of completeProvider must be false.
            if provider.get('completeProvider'):
                return False

            # If any exceptions are matched, this provider is skipped
            if any(re.match(exc, url, re.IGNORECASE)
                   for exc in provider.get('exceptions', [])):
                continue

            # If redirect found, recurse on target (only once)
            for redir in provider.get('redirections', []):
                match = re.match(redir, url, re.IGNORECASE)
                try:
                    if match and match.group(1):
                        if loop:
                            return self.clean_url(unquote(match.group(1)), rules, False)
                        else:
                            url = unquote(match.group(1))
                except IndexError:
                    log.warning(f"Redirect target match failed [{provider_name}]: {redir}")
                    pass

            # Explode query parameters to be checked against rules
            parsed_url = urlparse(url)
            query_params = parse_qsl(parsed_url.query)

            # Check regular rules and referral marketing rules
            for rule in (*provider.get('rules', []), *provider.get('referralMarketing', [])):
                query_params = [
                    param for param in query_params
                    if not re.match(rule, param[0], re.IGNORECASE)
                ]

            # Rebuild valid URI string with remaining query parameters
            url = urlunparse((
                parsed_url.scheme,
                parsed_url.netloc,
                parsed_url.path,
                parsed_url.params,
                urlencode(query_params),
                parsed_url.fragment,
            ))

            # Run raw rules against the full URI string
            for raw_rule in provider.get('rawRules', []):
                url = re.sub(raw_rule, '', url)
        return url

    @commands.Cog.listener()
    async def on_message(self, message):
        # Don't run under certain conditions
        if any((
            message.author.bot,
            await self.bot.cog_disabled_in_guild(self, message.guild),
            not await self.bot.allowed_by_whitelist_blacklist(message.author),
        )):
            return
        links = list(set(URL_PATTERN.findall(message.content)))
        if not links:
            return
        rules = await self.conf.rules() or await self._update()
        threshold = await self.conf.threshold()
        clean_links = []
        for link in links:
            clean_link = self.clean_url(link, rules)
            # Apply a threshold to avoid annoying users with trivial alterations
            if ((len(link) <= len(clean_link) - threshold or
                 len(link) >= len(clean_link) + threshold) and
                 link.lower() not in (clean_link.lower(),
                                      unquote(clean_link).lower())):
                clean_links.append(clean_link)
        if not len(clean_links):
            return
        plural = 'is' if len(clean_links) == 1 else 'ese'
        payload = "\n".join([f"<{link}>" for link in clean_links])
        response = f"I scrubbed th{plural} for you:\n{payload}"
        await self.bot.send_filtered(message.channel, content=response)

    async def view_or_set(self, attribute: str, value = None):
        """ View or set a given config attribute """
        config_element = getattr(self.conf, attribute)
        if value is not None:
            await config_element.set(value)
            return f"set to {value}"
        else:
            value = await config_element()
            return f"is {value}"

    @commands.group()
    async def scrub(self, ctx: commands.Context):
        """ Scrub tracking elements from hyperlinks """
        pass

    @scrub.command()
    @checks.admin_or_permissions(manage_guild=True)
    async def threshold(self, ctx: commands.Context, threshold: int = None):
        """ View or set the minimum threshold for link changes
        
        The default value of 2 should handle most decoding errors. A higher \
            value can be used to exclude short, mostly unobtrusive tracking \
            elements such as Twitter's device type ID.
        """
        action = await self.view_or_set("threshold", threshold)
        await ctx.send(f"Scrub threshold {action}")

    @scrub.command()
    @checks.admin_or_permissions(manage_guild=True)
    async def rules(self, ctx: commands.Context, location: str = None):
        """ View or set the rules file location to update from
        
        The format of the rules file is defined by \
            [ClearURLs](https://gitlab.com/KevinRoebert/ClearUrls/-/wikis/Specifications/Rules)
        
        By default, Scrub will get rules from: \
            https://kevinroebert.gitlab.io/ClearUrls/data/data.minify.json
        """
        action = await self.view_or_set("url", location)
        await ctx.send(f"Scrub rules file location {action}")

    @scrub.command()
    @checks.admin_or_permissions(manage_guild=True)
    async def update(self, ctx: commands.Context):
        """ Update Scrub with the latest rules """
        url = await self.conf.url()
        try:
            await self._update(url)
        except Exception as e:
            await ctx.send("Rules update failed (see log for details)")
            log.exception("Rules update failed", exc_info=e)
            return
        await ctx.send("Rules updated")

    async def _update(self, url):
        log.debug(f'Downloading rules data from {url}')
        session = aiohttp.ClientSession()
        async with session.get(url) as request:
            rules = json.loads(await request.read())
        await session.close()
        await self.conf.rules.set(rules)
