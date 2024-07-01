# PvP Tier List Discord Bot

Do you want to make your own Minecraft Tier Listing discord server? But you can't find a bot to give ranks and you want something to remember what rank everyone has, like mctiers?

Well look no further - This is the bot for you.

This bot is open-source, licensed with the Apache 2.0 license, meaning you can clone this repository and host this bot yourself.

## Features

- Online User data storage using Google Cloud Firestore

- Image manipulation commands

- Easy to use and understand commands

- Manages roles automatically

- Displays information in a appealling format

- Works with all mctiers official kits

- Prevents tester abuse, such as boosting ranks or retesting too quickly

## Commands

- `/rank give` - Tester command to give rank to a player. Automatically syncs with cloud database, sends message to results channel _and_ assigns approrpriate roles to the user

- `/rank remove` - Admin command to remove a rank from a player (syncs with discord roles)

- `/ranks` - Displays an embed showing every rank a user has

- `/elo` - Displays the ELO of a player

- `/leaderboard` - Displays the top 10 best overall PvPers using image manipulation

- `/history` - Checks when a player was last tested in a kit

- `/info website` - Links to the PvP Practice and Tier Testing Rankings Website (If you hae a website, feel free to modify this command in the file `cogs/info_cog.py`)

- `/info servers` - Shows a list of minecraft PvP servers to test on. (Feel free to modify in `cogs/info_cog.py`)

- `/config cooldown` - Set the number of days between tests

- `/config roles` - Required command to configure roles for the bot.

- `/config resultschannel` - Change the channel where results are sent

## How Leaderboard rankings are determined

When a rank is awarded to a user, in the background, a number, which we call the ELO, is computed. If we convert the tiers to numbers (Where LT5 is 1 and HT1 is 10), then the formula to compute ELO in pseudocode looks a bit like this:

```
loop through every kit the user has been tested to:
  Add <number form of tier> * 2 to total ELO
```

From there, rankings are simply ordered, ELO descending.

# Running Locally

## Local Setup

**Make sure you have python 3.11 installed on your system**

**1.** Clone the project

```bash
  git clone "https://github.com/SoumyaCodes2020/PvP-Practice-Bot"
```

**2.** Go to the project directory

```bash
  cd "PvP Practice Bot"
```

**3.** Install dependencies

```bash
  python3 -m pip install -r requirements.txt
```

**4.** Create an `.env` file in the same directory as main.py

```
PvP Practice Bot
├── .env (here)
├── main.py
...
```

Inside, add your discord bot token (there are many tutorials to get a bot token and invite it to your server, so I won't add) such that .env looks a bit like this:

```py
DISCORD_TOKEN=MTP0NXIxNjM1OFgyOTByNDcxMA.GNsh1N.e1OKnl9AEqa2Gy3zp2puDXulrTqSwNQJElBxCg
```

_(don't worry, it's not a real token)_

**5.** Use your Google account to create a new firebase project, then enable Cloud Firestore. (Search online if you're stuck) Then, go to:

```
Firebase Console -> Your Project -> Project Settings -> Service Accounts -> Click Generate New Private Key
```

When you do this, you will download a json file. Rename this file to `service_account.json` and move it to the same directory as main.py:

```
PvP Practice Bot
├── .env
├── main.py
└── service_account.json (<-- here)
```

## Discord Setup

**1.** Make sure that the bot has the following permissions in your server:

- Permission to send messages in your results channel
- The Manage Roles Permission
- Permission to use External Emojis

**2.** Use each of the commands in the `/config` subgroup to set up the bot. For `/config roles`, I'll provide you a list of roles you need to create for the bot:

- A role for admins
- A role for tier testers
- A role for tier testing managers (the bot doesn't use it now, but it will in the future)
- A role for each tier, from LT5 all the way to HT1

**3.** Go to `Discord Developer Portal -> Applications -> your Bot -> Bot -> Privileged Gateway Intents -> Enable "Server Members"`

## Starting the Bot

**On a local machine**

```bash
python main.py
```

**On a Pterodactyl server**:

Make sure that, if set, the main file is changed from `app.py` to `main.py`
