# PvP Discord Bot

This is the custom discord bot used in the PvP Practice discord server. It has been open-sourced and was programmed using python and py-cord.

The bot is simple; Storing its data on a local sqlite database.

This bot currently can:

- add tiers to a player
- remove tiers from a player
- show a leaderboard of all players

I will continue to work on this bot in the future.

## Environment Variables

To run this project, you will need to add the following environment variables to your .env file

`DISCORD_TOKEN` - Your discord bot token

## Run Locally

Clone the project

```bash
  git clone "https://github.com/SoumyaCodes2020/PvP-Practice-Bot"
```

Go to the project directory

```bash
  cd "PvP Practice Bot"
```

Install dependencies

```bash
  python3 -m pip install -r requirements.txt
```

Start the server

```bash
  python3 main.py
```
