"""
Persistent storage for characters and homebrew classes, using SQLite.
"""
import json
import aiosqlite

DB_PATH = "dnd_bot.db"


def _parse_json(value, default):
    """Safely parses JSON strings into Python objects."""
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return default
    return value if value is not None else default


def parse_character_row(row: dict) -> dict:
    """Ensures JSON-encoded fields are consistently returned as Python data structures."""
    if not row:
        return None
    data = dict(row)
    data["skill_proficiencies"] = _parse_json(data.get("skill_proficiencies"), [])
    data["save_proficiencies"] = _parse_json(data.get("save_proficiencies"), [])
    data["known_spells"] = _parse_json(data.get("known_spells"), [])
    return data


def parse_custom_row(row: dict, list_fields: list) -> dict:
    """Ensures custom class/race JSON fields are consistently decoded."""
    if not row:
        return None
    data = dict(row)
    for field in list_fields:
        data[field] = _parse_json(data.get(field), [])
    return data


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS characters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                guild_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                race TEXT NOT NULL,
                class_name TEXT NOT NULL,
                is_homebrew_class INTEGER NOT NULL DEFAULT 0,
                level INTEGER NOT NULL DEFAULT 1,
                str INTEGER NOT NULL,
                dex INTEGER NOT NULL,
                con INTEGER NOT NULL,
                intl INTEGER NOT NULL,
                wis INTEGER NOT NULL,
                cha INTEGER NOT NULL,
                max_hp INTEGER NOT NULL,
                current_hp INTEGER NOT NULL,
                ac INTEGER NOT NULL,
                skill_proficiencies TEXT NOT NULL DEFAULT '[]',
                save_proficiencies TEXT NOT NULL DEFAULT '[]',
                weapon TEXT NOT NULL DEFAULT 'Unarmed Strike',
                armor TEXT NOT NULL DEFAULT 'None',
                has_shield INTEGER NOT NULL DEFAULT 0,
                known_spells TEXT NOT NULL DEFAULT '[]',
                is_homebrew_race INTEGER NOT NULL DEFAULT 0,
                notes TEXT NOT NULL DEFAULT ''
            )
        """)
        for column, definition in [
            ("weapon", "TEXT NOT NULL DEFAULT 'Unarmed Strike'"),
            ("armor", "TEXT NOT NULL DEFAULT 'None'"),
            ("has_shield", "INTEGER NOT NULL DEFAULT 0"),
            ("known_spells", "TEXT NOT NULL DEFAULT '[]'"),
            ("is_homebrew_race", "INTEGER NOT NULL DEFAULT 0"),
        ]:
            try:
                await db.execute(f"ALTER TABLE characters ADD COLUMN {column} {definition}")
            except Exception:
                pass
        await db.execute("""
            CREATE TABLE IF NOT EXISTS custom_classes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                created_by INTEGER NOT NULL,
                name TEXT NOT NULL,
                hit_die INTEGER NOT NULL,
                saves TEXT NOT NULL,
                skill_choices INTEGER NOT NULL,
                skill_list TEXT NOT NULL,
                is_caster INTEGER NOT NULL DEFAULT 0,
                caster_type TEXT,
                features TEXT NOT NULL DEFAULT '[]',
                UNIQUE(guild_id, name)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS custom_races (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                created_by INTEGER NOT NULL,
                name TEXT NOT NULL,
                asi TEXT NOT NULL DEFAULT '[]',
                speed INTEGER NOT NULL DEFAULT 30,
                traits TEXT NOT NULL DEFAULT '[]',
                UNIQUE(guild_id, name)
            )
        """)
        await db.commit()


async def save_character(data: dict) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            INSERT INTO characters
            (user_id, guild_id, name, race, class_name, is_homebrew_class, level,
             str, dex, con, intl, wis, cha, max_hp, current_hp, ac,
             skill_proficiencies, save_proficiencies, weapon, armor, has_shield, known_spells,
             is_homebrew_race, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data["user_id"], data["guild_id"], data["name"], data["race"],
            data["class_name"], int(data.get("is_homebrew_class", False)), data.get("level", 1),
            data["str"], data["dex"], data["con"], data["intl"], data["wis"], data["cha"],
            data["max_hp"], data["max_hp"], data["ac"],
            json.dumps(data.get("skill_proficiencies", [])),
            json.dumps(data.get("save_proficiencies", [])),
            data.get("weapon", "Unarmed Strike"), data.get("armor", "None"),
            int(data.get("has_shield", False)), json.dumps(data.get("known_spells", [])),
            int(data.get("is_homebrew_race", False)), data.get("notes", "")
        ))
        await db.commit()
        return cursor.lastrowid


async def get_characters_for_user(user_id: int, guild_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM characters WHERE user_id = ? AND guild_id = ?",
            (user_id, guild_id)
        )
        rows = await cursor.fetchall()
        return [parse_character_row(dict(r)) for r in rows]


async def get_character_by_name(user_id: int, guild_id: int, name: str):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM characters WHERE user_id = ? AND guild_id = ? AND LOWER(name) = LOWER(?)",
            (user_id, guild_id, name)
        )
        row = await cursor.fetchone()
        return parse_character_row(dict(row)) if row else None


async def update_hp(character_id: int, current_hp: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE characters SET current_hp = ? WHERE id = ?", (current_hp, character_id))
        await db.commit()


async def update_character(data: dict) -> bool:
    """Updates an existing character record in the database."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            UPDATE characters SET
                name = ?, level = ?, str = ?, dex = ?, con = ?, intl = ?, wis = ?, cha = ?,
                max_hp = ?, current_hp = ?, ac = ?, weapon = ?, armor = ?, has_shield = ?,
                known_spells = ?, skill_proficiencies = ?, save_proficiencies = ?
            WHERE id = ? AND user_id = ?
        """, (
            data["name"], data["level"], data["str"], data["dex"], data["con"],
            data["intl"], data["wis"], data["cha"], data["max_hp"],
            min(data["current_hp"], data["max_hp"]), data["ac"],
            data["weapon"], data["armor"], int(data["has_shield"]),
            json.dumps(data.get("known_spells", [])),
            json.dumps(data.get("skill_proficiencies", [])),
            json.dumps(data.get("save_proficiencies", [])),
            data["id"], data["user_id"]
        ))
        await db.commit()
        return cursor.rowcount > 0

async def delete_character(character_id: int, user_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "DELETE FROM characters WHERE id = ? AND user_id = ?", (character_id, user_id)
        )
        await db.commit()
        return cursor.rowcount > 0


async def save_custom_class(data: dict) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            INSERT INTO custom_classes
            (guild_id, created_by, name, hit_die, saves, skill_choices, skill_list,
             is_caster, caster_type, features)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data["guild_id"], data["created_by"], data["name"], data["hit_die"],
            json.dumps(data["saves"]), data["skill_choices"], json.dumps(data["skill_list"]),
            int(data.get("is_caster", False)), data.get("caster_type"),
            json.dumps(data.get("features", []))
        ))
        await db.commit()
        return cursor.lastrowid


async def get_custom_classes(guild_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM custom_classes WHERE guild_id = ?", (guild_id,))
        rows = await cursor.fetchall()
        return [parse_custom_row(dict(r), ["saves", "skill_list", "features"]) for r in rows]


async def get_custom_class_by_name(guild_id: int, name: str):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM custom_classes WHERE guild_id = ? AND LOWER(name) = LOWER(?)",
            (guild_id, name)
        )
        row = await cursor.fetchone()
        return parse_custom_row(dict(row), ["saves", "skill_list", "features"]) if row else None


async def save_custom_race(data: dict) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            INSERT INTO custom_races (guild_id, created_by, name, asi, speed, traits)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            data["guild_id"], data["created_by"], data["name"],
            json.dumps(data.get("asi", [])), data.get("speed", 30),
            json.dumps(data.get("traits", []))
        ))
        await db.commit()
        return cursor.lastrowid


async def get_custom_races(guild_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM custom_races WHERE guild_id = ?", (guild_id,))
        rows = await cursor.fetchall()
        return [parse_custom_row(dict(r), ["asi", "traits"]) for r in rows]


async def get_custom_race_by_name(guild_id: int, name: str):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM custom_races WHERE guild_id = ? AND LOWER(name) = LOWER(?)",
            (guild_id, name)
        )
        row = await cursor.fetchone()
        return parse_custom_row(dict(row), ["asi", "traits"]) if row else None