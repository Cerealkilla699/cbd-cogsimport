# Installation

**Attention:** The cog names in this repo are all TitleCase. This goes against [Red conventions](https://red-discordbot.readthedocs.io/en/stable/guide_cog_creation.html) but I prefer it.

Here are the [Red](https://github.com/Cog-Creators/Red-DiscordBot) commands to add this repository (use your bot's prefix in place of `[p]`):
```
[p]load downloader
[p]repo add CBD-Cogs https://gitlab.com/CrunchBangDev/cbd-cogs
```

You may be prompted to respond with "I agree" after that.


# Cogs

You can install individual cogs like this:
```
[p]cog install CBD-Cogs [cog]
```

Just replace `[cog]` with the name of the cog you want to install.

## Bio

Add information to your player bio and lookup information others have shared.

Bio is basically a key/value store for each user where the allowed keys are determined by server admins.

### Commands

| Command     | Description |
| ----------- | ----------- |
| `bio`       | Display and modify your bio or view someone else's bio |
| `biofields` | List the available bio fields |
| `biosearch` | Find field values across all users |

## Bookmark

Allow users to use a reaction in order to bookmark messages for later review.

Add a reaction to bookmark a message and remove the reaction to remove it from your bookmarks.

### Commands

| Command            | Description |
| ------------------ | ----------- |
| `bookmarks`        | Display your bookmarks |
| `setbookmarkemoji` | Set the emoji to be used for bookmarking |

## Scrub

Applies a set of rules to remove undesireable elements from hyperlinks such as campaign tracking tokens.

Since bots can't edit people's messages, it reposts the cleaned links.

### Commands

| Command           | Description |
| ----------------- | ----------- |
| `scrub update`    | Update Scrub with the latest rules |
| `scrub rules`     | View or set the rules file location to update from |
| `scrub threshold` | View or set the minimum threshold for link changes |

### Credits

Thanks to [Walter](https://github.com/walterl) for making [Uroute](https://github.com/walterl/uroute) from which this borrows heavily.

Thanks to [Kevin](https://gitlab.com/KevinRoebert) for the [ClearURLs](https://gitlab.com/KevinRoebert/ClearUrls) rule set without which this cog wouldn't work.

## Tube

Posts in a channel every time a new video is added to a YouTube channel.

### Commands

| Command            | Description |
| ------------------ | ----------- |
| `tube list`        | List current subscriptions |
| `tube subscribe`   | Subscribe a Discord channel to a YouTube channel |
| `tube unsubscribe` | Unsubscribe a Discord channel from a YouTube channel |
| `tube update`      | Update feeds and post new videos |
| `tube customize`   | Set or delete a custom message for new videos |

### Credits

Thanks to [Sinbad](https://github.com/mikeshardmind) for the [RSS cog](https://github.com/mikeshardmind/SinbadCogs/tree/v3/rss) I based this on.

## Inspire

Obtains inspiration for you from an API. This is entirely normal and not sad.

### Commands

| Command       | Description |
| ------------- | ----------- |
| `inspire`     | Gain inspiration |

### Credits

This cog uses the brilliant [InspiroBot API](https://inspirobot.me).

## Vibe

Bask in deep API-driven thoughts and images streamed right at your face.

### Commands

| Command       | Description |
| ------------- | ----------- |
| `vibe`        | Initiate deep thought immersion therapy |

### Credits

This cog _also_ uses the brilliant [InspiroBot API](https://inspirobot.me).

## Markov

Models user text using markov chains and generates new text from those models. Ngrams included!

Please note that you will have to use the command `[p]markov channelenable` to allow this cog to work in any channel.

### Commands

| Command                 | Description |
| ----------------------- | ----------- |
| `markov generate`       | Generate text based on user language models |
| `markov enable`         | Allow the bot to model your messages and generate text |
| `markov disable`        | Disallow the bot from modeling your messages or generating text |
| `markov mode`           | Set the tokenization mode for model building |
| `markov depth`          | Set the modeling depth (the "n" in "ngrams") |
| `markov show`           | Show your current settings and models, or those of another user |
| `markov delete`         | Delete a specific model from your profile |
| `markov reset`          | Remove all language models from your profile |
| `markov channelenable`  | Allow language modeling on messages in a given channel |
| `markov channeldisable` | Disallow language modeling on messages in a given channel |

### Credits

Named for the Russian mathematician [Andrey Markov](https://en.wikipedia.org/wiki/Andrey_Markov) who came up with the stochastic model this cog was inspired by.
