# D&D Character Sheet & Dice Bot

A Discord bot that makes creating a D&D 5e character sheet as easy as clicking
through a few dropdowns — no math, no memorizing rules. Built so a 12-year-old
can make a character on their own.

## What it does

- **`/newcharacter`** — guided wizard: name → race (dropdown) → class (dropdown,
  including your server's homebrew classes) → assign ability scores using the
  standard array by tapping buttons. The bot computes HP, AC, and saving throw
  proficiencies automatically.
- **`/newclass`** (via the "Create a new homebrew class..." option inside
  `/newcharacter`) — build a fully custom class: name it, pick a hit die,
  pick 2 saving throw proficiencies. It's saved for the whole server to reuse.
- **`/sheet`** — view a character's full sheet as a clean embed.
- **`/roll <dice>`** — raw dice notation, e.g. `/roll 1d20+5`.
- **`/check`** and **`/save`** — pick your character and an ability from a
  dropdown; the bot already knows the modifier and rolls for you.

## Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
```
### 2. Create a Discord bot application
1. Go to https://discord.com/developers/applications and click **New Application**.
2. Go to the **Bot** tab, click **Add Bot**.
3. Under **Privileged Gateway Intents**, you don't need to enable anything extra —
   this bot only uses slash commands.
4. Click **Reset Token** to reveal your bot token, and copy it. **Keep this secret.**
5. Go to **OAuth2 → URL Generator**, check scopes `bot` and `applications.commands`,
   then under Bot Permissions check `Send Messages`, `Use Slash Commands`,
   and `Embed Links`. Copy the generated URL and open it to invite the bot
   to your server.

### 3. Set your token
Set it as an environment variable rather than pasting it into any file:
```bash
export DISCORD_BOT_TOKEN="your-token-here"
```
(On Windows: `set DISCORD_BOT_TOKEN=your-token-here`)

### 4. Run the bot
```bash
python bot.py
```
The first time it starts, it'll create `dnd_bot.db` (a SQLite file — this is
where all characters and homebrew classes live) and register its slash
commands with Discord. It can take up to an hour for global slash commands
to show up everywhere the first time, but they usually appear within a
minute or two.

## Project structure
```
dnd-bot/
├── bot.py              # entry point
├── database.py         # SQLite storage (characters + homebrew classes)
├── requirements.txt
├── data/
│   └── reference.py     # 5e tables: races, classes, hit dice, skills
└── cogs/
    ├── character.py     # /newcharacter wizard, homebrew builder, /sheet
    └── dice.py           # /roll, /check, /save
```
- Skill proficiency picking during character creation (skills exist in the
  data but aren't yet part of the wizard flow)
