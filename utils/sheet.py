"""
Character sheet math, embed building, and stat recalculation helpers.
"""
import discord
import database
from data.reference import (
    CLASSES, SKILLS, WEAPONS, ARMOR, RACE_TRAITS, CLASS_FEATURES_L1,
    FULL_CASTER_SLOTS, HALF_CASTER_SLOTS, PACT_CASTER_SLOTS,
    SPELLCASTING_ABILITY, SPELLS, ability_modifier, proficiency_bonus
)

ABILITY_TO_FIELD = {"STR": "str", "DEX": "dex", "CON": "con", "INT": "intl", "WIS": "wis", "CHA": "cha"}


def compute_hp(hit_die: int, con_score: int, level: int = 1) -> int:
    con_mod = ability_modifier(con_score)
    hp = hit_die + con_mod
    if level > 1:
        avg_per_level = (hit_die // 2) + 1
        hp += (avg_per_level + con_mod) * (level - 1)
    return max(hp, 1)


def add_safe_field(embed: discord.Embed, name: str, lines: list, inline: bool = False):
    if not lines:
        return
    current_chunk = ""
    for line in lines:
        if len(current_chunk) + len(line) + 1 > 1000:
            embed.add_field(name=name, value=current_chunk.strip(), inline=inline)
            current_chunk = line + "\n"
            name = f"{name} (cont.)"
        else:
            current_chunk += line + "\n"
    if current_chunk:
        embed.add_field(name=name, value=current_chunk.strip(), inline=inline)


async def recalculate_character_stats(character: dict) -> dict:
    if character.get("is_homebrew_class"):
        custom = await database.get_custom_class_by_name(character["guild_id"], character["class_name"])
        hit_die = custom["hit_die"] if custom else 8
    else:
        hit_die = CLASSES.get(character["class_name"], {}).get("hit_die", 8)

    character["max_hp"] = compute_hp(hit_die, character["con"], level=character["level"])
    if character["current_hp"] > character["max_hp"]:
        character["current_hp"] = character["max_hp"]

    dex_mod = ability_modifier(character["dex"])
    armor_data = ARMOR.get(character.get("armor", "None"), ARMOR["None"])
    dex_cap = armor_data["dex_cap"]
    effective_dex_bonus = dex_mod if dex_cap is None else min(dex_mod, dex_cap)

    ac = armor_data["base_ac"] + effective_dex_bonus
    if character.get("has_shield"):
        ac += ARMOR["Shield"]["ac_bonus"]
    character["ac"] = ac

    return character


async def get_homebrew_features_for(character: dict):
    if not character.get("is_homebrew_class"):
        return None
    custom = await database.get_custom_class_by_name(character["guild_id"], character["class_name"])
    return custom.get("features", []) if custom else None


async def get_homebrew_race_traits_for(character: dict):
    if not character.get("is_homebrew_race"):
        return None
    custom = await database.get_custom_race_by_name(character["guild_id"], character["race"])
    return custom.get("traits", []) if custom else None


def format_ability_table(character: dict) -> str:
    order = ["STR", "DEX", "CON", "INT", "WIS", "CHA"]
    cells = []
    for a in order:
        score = character[ABILITY_TO_FIELD[a]]
        mod = ability_modifier(score)
        sign = "+" if mod >= 0 else ""
        cells.append(f"{a} {score:>2} ({sign}{mod})")
    row1 = "  ".join(cells[0:3])
    row2 = "  ".join(cells[3:6])
    return f"```\n{row1}\n{row2}\n```"


def build_sheet_embed(character: dict, homebrew_features: list = None, homebrew_race_traits: list = None) -> discord.Embed:
    embed = discord.Embed(
        title=character["name"],
        description=f"Level {character['level']} {character['race']} {character['class_name']}",
        color=discord.Color.dark_gold()
    )
    embed.add_field(name="Ability Scores", value=format_ability_table(character), inline=False)

    combat_line = (f"HP: {character['current_hp']}/{character['max_hp']}   "
                   f"AC: {character['ac']}   Prof: +{proficiency_bonus(character['level'])}")
    embed.add_field(name="Combat", value=f"```\n{combat_line}\n```", inline=False)

    weapon = character.get("weapon", "Unarmed Strike")
    weapon_stats = WEAPONS.get(weapon, WEAPONS["Unarmed Strike"])
    armor_label = character.get("armor", "None")
    if character.get("has_shield"):
        armor_label += " + Shield"
    gear_lines = f"Weapon: {weapon} ({weapon_stats['dice']} {weapon_stats['damage_type']})\nArmor:  {armor_label}"
    embed.add_field(name="Gear", value=f"```\n{gear_lines}\n```", inline=False)

    saves = character.get("save_proficiencies", [])
    if saves:
        embed.add_field(name="Save Proficiencies", value=", ".join(saves), inline=False)

    skill_profs = character.get("skill_proficiencies", [])
    prof_bonus = proficiency_bonus(character["level"])
    skill_lines = []
    for skill_name, governing_ability in SKILLS.items():
        score = character[ABILITY_TO_FIELD[governing_ability]]
        bonus = ability_modifier(score)
        is_proficient = skill_name in skill_profs
        if is_proficient:
            bonus += prof_bonus
        sign = "+" if bonus >= 0 else ""
        marker = "⭐ " if is_proficient else ""
        skill_lines.append(f"{marker}{skill_name} ({governing_ability}): {sign}{bonus}")

    add_safe_field(embed, "Skills", skill_lines, inline=False)

    if character.get("is_homebrew_race"):
        race_traits = homebrew_race_traits or ["This is a custom race with no traits written yet."]
    else:
        race_traits = RACE_TRAITS.get(character["race"], [])

    if character.get("is_homebrew_class"):
        class_features = homebrew_features or ["This is a homebrew class with no features written yet."]
    else:
        class_features = CLASS_FEATURES_L1.get(character["class_name"], [])

    feature_lines = [f"🏷️ {t}" for t in race_traits] + [f"⚔️ {f}" for f in class_features]
    add_safe_field(embed, "Features & Traits", feature_lines, inline=False)

    caster_type = None if character.get("is_homebrew_class") else CLASSES.get(character["class_name"], {}).get("caster")
    if caster_type:
        spell_ability = SPELLCASTING_ABILITY[character["class_name"]]
        spell_mod = ability_modifier(character[ABILITY_TO_FIELD[spell_ability]])
        spell_dc = 8 + prof_bonus + spell_mod
        spell_attack = prof_bonus + spell_mod
        level = character["level"]

        if caster_type == "pact":
            count, slot_level = PACT_CASTER_SLOTS.get(level, (0, 0))
            slots_text = f"{count} slot(s) of level {slot_level} (recharge on a short rest)" if count else "None yet"
        else:
            table = FULL_CASTER_SLOTS if caster_type == "full" else HALF_CASTER_SLOTS
            slots_list = table.get(level, [])
            slots_text = (", ".join(f"L{i+1}: {n}" for i, n in enumerate(slots_list) if n)
                          if slots_list else "None yet")

        known_spells = character.get("known_spells", [])

        def label_spell(name):
            info = SPELLS.get(name)
            if not info:
                return name
            level_label = "Cantrip" if info["level"] == 0 else f"L{info['level']}"
            return f"{name} ({level_label} {info['school']})"

        spells_text = ", ".join(label_spell(s) for s in known_spells) if known_spells else "*(none entered)*"

        embed.add_field(
            name="Spellcasting",
            value=(f"Ability: **{spell_ability}** | Save DC: **{spell_dc}** | Attack: **+{spell_attack}**\n"
                   f"Slots: {slots_text}\nKnown: {spells_text}"),
            inline=False
        )

    return embed