"""
Static D&D 5e reference tables.

These exist so the bot can COMPUTE things (HP, saves, skill bonuses)
instead of asking the user to type them in. A 12-year-old should never
have to know what "hit die" or "proficiency bonus" means to use this bot —
they just pick a class from a list and the bot does the math.
"""

ABILITIES = ["STR", "DEX", "CON", "INT", "WIS", "CHA"]

SKILLS = {
    # skill_name: governing ability
    "Acrobatics": "DEX",
    "Animal Handling": "WIS",
    "Arcana": "INT",
    "Athletics": "STR",
    "Deception": "CHA",
    "History": "INT",
    "Insight": "WIS",
    "Intimidation": "CHA",
    "Investigation": "INT",
    "Medicine": "WIS",
    "Nature": "INT",
    "Perception": "WIS",
    "Performance": "CHA",
    "Persuasion": "CHA",
    "Religion": "INT",
    "Sleight of Hand": "DEX",
    "Stealth": "DEX",
    "Survival": "WIS",
}

RACES = {
    "Human":        {"asi": {"STR": 1, "DEX": 1, "CON": 1, "INT": 1, "WIS": 1, "CHA": 1}, "speed": 30},
    "Forest Gnome": {"asi": {"INT": 2, "DEX": 1}, "speed": 25},
    "Rock Gnome":   {"asi": {"INT": 2, "CON": 1}, "speed": 25},
    "Half-Orc":     {"asi": {"STR": 2, "CON": 1}, "speed": 30},
    "High Elf":     {"asi": {"DEX": 2, "INT": 1}, "speed": 30},
    "Wood Elf":     {"asi": {"DEX": 2, "WIS": 1}, "speed": 35},
    "Hill Dwarf":   {"asi": {"CON": 2, "WIS": 1}, "speed": 25},
    "Mountain Dwarf": {"asi": {"CON": 2, "STR": 2}, "speed": 25},
    "Halfling":     {"asi": {"DEX": 2}, "speed": 25},
    "Dragonborn":   {"asi": {"STR": 2, "CHA": 1}, "speed": 30},
    "Half-Elf":     {"asi": {"CHA": 2}, "speed": 30},  # +1/+1 to two others, simplified for now
    "Tiefling":     {"asi": {"CHA": 2, "INT": 1}, "speed": 30},
}

# Short, plain-language race traits — just enough to know what your race actually
# DOES at the table, not the full rulebook text.
RACE_TRAITS = {
    "Human":          ["Versatile — no special abilities, but well-rounded stats"],
    "Forest Gnome":   ["Darkvision 60 ft", "Advantage on saves vs. magic (Gnome Cunning)",
                        "Know the Minor Illusion cantrip"],
    "Rock Gnome":     ["Darkvision 60 ft", "Advantage on saves vs. magic (Gnome Cunning)",
                        "Tinker: can build tiny clockwork devices"],
    "Half-Orc":       ["Darkvision 60 ft", "Relentless Endurance — drop to 1 HP instead of 0, once per long rest",
                        "Savage Attacks — extra damage die on a critical hit"],
    "High Elf":       ["Darkvision 60 ft", "Advantage on saves vs. being charmed, can't be magically put to sleep",
                        "Know one Wizard cantrip"],
    "Wood Elf":       ["Darkvision 60 ft", "Advantage on saves vs. being charmed, can't be magically put to sleep",
                        "Mask of the Wild — can hide even lightly obscured by nature"],
    "Hill Dwarf":     ["Darkvision 60 ft", "Advantage on saves vs. poison, resistance to poison damage",
                        "+1 extra HP per level"],
    "Mountain Dwarf":  ["Darkvision 60 ft", "Advantage on saves vs. poison, resistance to poison damage",
                        "Proficient with light and medium armor"],
    "Halfling":       ["Lucky — reroll a 1 on an attack, check, or save",
                        "Brave — advantage on saves vs. being frightened",
                        "Can move through the space of larger creatures"],
    "Dragonborn":     ["Breath Weapon — replaces an action with an elemental damage blast",
                        "Damage resistance tied to draconic ancestry"],
    "Half-Elf":       ["Darkvision 60 ft", "Advantage on saves vs. being charmed, can't be magically put to sleep"],
    "Tiefling":       ["Darkvision 60 ft", "Resistance to fire damage",
                        "Know the Thaumaturgy cantrip"],
}


# Standard 5e classes: hit die, saving throw proficiencies, and how many/which
# skills they choose from. "caster" marks full/half/third/none for spell slot lookup.
CLASSES = {
    "Barbarian": {"hit_die": 12, "saves": ["STR", "CON"], "skill_choices": 2,
                  "skill_list": ["Animal Handling", "Athletics", "Intimidation", "Nature", "Perception", "Survival"],
                  "caster": None},
    "Bard":      {"hit_die": 8, "saves": ["DEX", "CHA"], "skill_choices": 3,
                  "skill_list": list(SKILLS.keys()), "caster": "full"},
    "Cleric":    {"hit_die": 8, "saves": ["WIS", "CHA"], "skill_choices": 2,
                  "skill_list": ["History", "Insight", "Medicine", "Persuasion", "Religion"], "caster": "full"},
    "Druid":     {"hit_die": 8, "saves": ["INT", "WIS"], "skill_choices": 2,
                  "skill_list": ["Arcana", "Animal Handling", "Insight", "Medicine", "Nature", "Perception", "Religion", "Survival"],
                  "caster": "full"},
    "Fighter":   {"hit_die": 10, "saves": ["STR", "CON"], "skill_choices": 2,
                  "skill_list": ["Acrobatics", "Animal Handling", "Athletics", "History", "Insight", "Intimidation", "Perception", "Survival"],
                  "caster": None},
    "Monk":      {"hit_die": 8, "saves": ["STR", "DEX"], "skill_choices": 2,
                  "skill_list": ["Acrobatics", "Athletics", "History", "Insight", "Religion", "Stealth"],
                  "caster": None},
    "Paladin":   {"hit_die": 10, "saves": ["WIS", "CHA"], "skill_choices": 2,
                  "skill_list": ["Athletics", "Insight", "Intimidation", "Medicine", "Persuasion", "Religion"],
                  "caster": "half"},
    "Ranger":    {"hit_die": 10, "saves": ["STR", "DEX"], "skill_choices": 3,
                  "skill_list": ["Animal Handling", "Athletics", "Insight", "Investigation", "Nature", "Perception", "Stealth", "Survival"],
                  "caster": "half"},
    "Rogue":     {"hit_die": 8, "saves": ["DEX", "INT"], "skill_choices": 4,
                  "skill_list": ["Acrobatics", "Athletics", "Deception", "Insight", "Intimidation", "Investigation", "Perception", "Performance", "Persuasion", "Sleight of Hand", "Stealth"],
                  "caster": None},
    "Sorcerer":  {"hit_die": 6, "saves": ["CON", "CHA"], "skill_choices": 2,
                  "skill_list": ["Arcana", "Deception", "Insight", "Intimidation", "Persuasion", "Religion"],
                  "caster": "full"},
    "Warlock":   {"hit_die": 8, "saves": ["WIS", "CHA"], "skill_choices": 2,
                  "skill_list": ["Arcana", "Deception", "History", "Intimidation", "Investigation", "Nature", "Religion"],
                  "caster": "pact"},
    "Wizard":    {"hit_die": 6, "saves": ["INT", "WIS"], "skill_choices": 2,
                  "skill_list": ["Arcana", "History", "Insight", "Investigation", "Medicine", "Religion"],
                  "caster": "full"},
}

# Short, plain-language level-1 class features — what your class can actually
# DO at the table, not full rules text. Kept to the headline 1-2 features
# so a new player isn't overwhelmed.
CLASS_FEATURES_L1 = {
    "Barbarian": ["Rage — bonus action, extra damage, resistance to physical damage (limited uses/day)",
                  "Unarmored Defense — AC = 10 + DEX mod + CON mod when not wearing armor"],
    "Bard":      ["Bardic Inspiration — give an ally a bonus die to add to a roll",
                  "Spellcasting — knows a handful of spells, casts using CHA"],
    "Cleric":    ["Spellcasting — knows a handful of spells, casts using WIS",
                  "Divine Domain — a themed set of bonus abilities from your deity"],
    "Druid":     ["Spellcasting — knows a handful of spells, casts using WIS",
                  "Druidic — knows a secret language of druids"],
    "Fighter":   ["Fighting Style — a permanent combat bonus (e.g. +2 to ranged attacks)",
                  "Second Wind — bonus action to heal yourself once per short rest"],
    "Monk":      ["Martial Arts — can use DEX instead of STR for unarmed strikes",
                  "Unarmored Defense — AC = 10 + DEX mod + WIS mod when unarmored"],
    "Paladin":   ["Divine Sense — detect celestials, fiends, and undead nearby",
                  "Lay on Hands — a pool of HP you can spend to heal by touch"],
    "Ranger":    ["Favored Enemy — bonus knowledge/tracking vs. a chosen creature type",
                  "Natural Explorer — expertise moving through a chosen terrain type"],
    "Rogue":     ["Sneak Attack — extra damage once per turn when you have advantage",
                  "Expertise — double proficiency bonus on 2 chosen skills"],
    "Sorcerer":  ["Spellcasting — knows a handful of spells, casts using CHA",
                  "Sorcerous Origin — a themed set of bonus abilities from your bloodline"],
    "Warlock":   ["Otherworldly Patron — a themed set of bonus abilities from your patron",
                  "Pact Magic — a small number of spell slots that recharge on a short rest"],
    "Wizard":    ["Spellcasting — knows a handful of spells, casts using INT",
                  "Arcane Recovery — recover some spell slots once per day on a short rest"],
}


# Weapons: dice (damage), damage_type, ability used for attack/damage rolls
# ("finesse" means the player can use whichever of STR/DEX is higher),
# and whether it's melee or ranged (affects flavor text only for now).
WEAPONS = {
    "Dagger":         {"dice": "1d4", "damage_type": "piercing", "ability": "finesse", "category": "melee"},
    "Shortsword":     {"dice": "1d6", "damage_type": "piercing", "ability": "finesse", "category": "melee"},
    "Scimitar":       {"dice": "1d6", "damage_type": "slashing", "ability": "finesse", "category": "melee"},
    "Rapier":         {"dice": "1d8", "damage_type": "piercing", "ability": "finesse", "category": "melee"},
    "Longsword":      {"dice": "1d8", "damage_type": "slashing", "ability": "STR", "category": "melee"},
    "Battleaxe":      {"dice": "1d8", "damage_type": "slashing", "ability": "STR", "category": "melee"},
    "Warhammer":      {"dice": "1d8", "damage_type": "bludgeoning", "ability": "STR", "category": "melee"},
    "Greatsword":     {"dice": "2d6", "damage_type": "slashing", "ability": "STR", "category": "melee"},
    "Greataxe":       {"dice": "1d12", "damage_type": "slashing", "ability": "STR", "category": "melee"},
    "Quarterstaff":   {"dice": "1d6", "damage_type": "bludgeoning", "ability": "STR", "category": "melee"},
    "Mace":           {"dice": "1d6", "damage_type": "bludgeoning", "ability": "STR", "category": "melee"},
    "Warhammer (versatile)": {"dice": "1d8", "damage_type": "bludgeoning", "ability": "STR", "category": "melee"},
    "Shortbow":       {"dice": "1d6", "damage_type": "piercing", "ability": "DEX", "category": "ranged"},
    "Longbow":        {"dice": "1d8", "damage_type": "piercing", "ability": "DEX", "category": "ranged"},
    "Light Crossbow": {"dice": "1d8", "damage_type": "piercing", "ability": "DEX", "category": "ranged"},
    "Unarmed Strike": {"dice": "1d4", "damage_type": "bludgeoning", "ability": "STR", "category": "melee"},
}

# Armor: base_ac, dex_cap (None = full DEX bonus applies, an int = DEX bonus
# capped at that value, 0 = no DEX bonus at all — heavy armor)
ARMOR = {
    "None":            {"base_ac": 10, "dex_cap": None, "category": "none"},
    "Padded Armor":    {"base_ac": 11, "dex_cap": None, "category": "light"},
    "Leather Armor":   {"base_ac": 11, "dex_cap": None, "category": "light"},
    "Studded Leather": {"base_ac": 12, "dex_cap": None, "category": "light"},
    "Hide Armor":      {"base_ac": 12, "dex_cap": 2, "category": "medium"},
    "Chain Shirt":     {"base_ac": 13, "dex_cap": 2, "category": "medium"},
    "Scale Mail":      {"base_ac": 14, "dex_cap": 2, "category": "medium"},
    "Chain Mail":      {"base_ac": 16, "dex_cap": 0, "category": "heavy"},
    "Shield":          {"ac_bonus": 2, "category": "shield"},
}

# Starting gear choices offered during character creation, kept to a short,
# easy-to-pick list per class rather than the full 5e "choose A or B" tables.
STARTING_GEAR = {
    "Barbarian":  {"weapons": ["Greataxe", "Battleaxe", "Warhammer"], "armor": ["None"]},
    "Bard":       {"weapons": ["Rapier", "Shortsword", "Dagger"], "armor": ["Leather Armor", "None"]},
    "Cleric":     {"weapons": ["Mace", "Warhammer"], "armor": ["Scale Mail", "Chain Shirt", "Leather Armor"]},
    "Druid":      {"weapons": ["Scimitar", "Quarterstaff", "Mace"], "armor": ["Leather Armor", "Hide Armor"]},
    "Fighter":    {"weapons": ["Longsword", "Battleaxe", "Warhammer", "Greatsword", "Greataxe"],
                   "armor": ["Chain Mail", "Scale Mail", "Leather Armor"]},
    "Monk":       {"weapons": ["Shortsword", "Quarterstaff", "Unarmed Strike"], "armor": ["None"]},
    "Paladin":    {"weapons": ["Longsword", "Warhammer", "Battleaxe"], "armor": ["Chain Mail", "Scale Mail"]},
    "Ranger":     {"weapons": ["Longbow", "Shortsword", "Scimitar"], "armor": ["Leather Armor", "Studded Leather"]},
    "Rogue":      {"weapons": ["Rapier", "Shortsword", "Dagger", "Shortbow"], "armor": ["Leather Armor"]},
    "Sorcerer":   {"weapons": ["Dagger", "Quarterstaff", "Light Crossbow"], "armor": ["None"]},
    "Warlock":    {"weapons": ["Dagger", "Light Crossbow", "Quarterstaff"], "armor": ["Leather Armor", "None"]},
    "Wizard":     {"weapons": ["Dagger", "Quarterstaff"], "armor": ["None"]},
}
DEFAULT_HOMEBREW_GEAR = {
    "weapons": ["Dagger", "Shortsword", "Quarterstaff", "Shortbow"],
    "armor": ["Leather Armor", "None"],
}


# Proficiency bonus by character level (5e is the same for every class)
def proficiency_bonus(level: int) -> int:
    return 2 + (level - 1) // 4


def ability_modifier(score: int) -> int:
    return (score - 10) // 2


# Spell slots by caster level, keyed by [caster_type][class_level] -> list of slots per spell level 1-9
# Simplified full/half/third progressions (standard 5e tables), used for full/half/third casters.
FULL_CASTER_SLOTS = {
    1: [2], 2: [3], 3: [4, 2], 4: [4, 3], 5: [4, 3, 2],
    6: [4, 3, 3], 7: [4, 3, 3, 1], 8: [4, 3, 3, 2], 9: [4, 3, 3, 3, 1],
    10: [4, 3, 3, 3, 2], 11: [4, 3, 3, 3, 2, 1], 12: [4, 3, 3, 3, 2, 1],
    13: [4, 3, 3, 3, 2, 1, 1], 14: [4, 3, 3, 3, 2, 1, 1], 15: [4, 3, 3, 3, 2, 1, 1, 1],
    16: [4, 3, 3, 3, 2, 1, 1, 1], 17: [4, 3, 3, 3, 2, 1, 1, 1, 1],
    18: [4, 3, 3, 3, 3, 1, 1, 1, 1], 19: [4, 3, 3, 3, 3, 2, 1, 1, 1],
    20: [4, 3, 3, 3, 3, 2, 2, 1, 1],
}

# Half-casters (Paladin, Ranger) get no spells at level 1, starting at level 2.
HALF_CASTER_SLOTS = {
    1: [], 2: [2], 3: [3], 4: [3], 5: [4, 2],
    6: [4, 2], 7: [4, 3], 8: [4, 3], 9: [4, 3, 2],
    10: [4, 3, 2], 11: [4, 3, 3], 12: [4, 3, 3],
    13: [4, 3, 3, 1], 14: [4, 3, 3, 1], 15: [4, 3, 3, 2],
    16: [4, 3, 3, 2], 17: [4, 3, 3, 3, 1], 18: [4, 3, 3, 3, 1],
    19: [4, 3, 3, 3, 2], 20: [4, 3, 3, 3, 2],
}

# Warlock's Pact Magic works differently: a small, fixed number of slots that
# are all the SAME level (and recharge on a short rest, not a long one).
# Keyed by level -> (number_of_slots, slot_level).
PACT_CASTER_SLOTS = {
    1: (1, 1), 2: (2, 1), 3: (2, 2), 4: (2, 2), 5: (2, 3),
    6: (2, 3), 7: (2, 4), 8: (2, 4), 9: (2, 5), 10: (2, 5),
    11: (3, 5), 12: (3, 5), 13: (3, 5), 14: (3, 5), 15: (3, 5),
    16: (3, 5), 17: (4, 5), 18: (4, 5), 19: (4, 5), 20: (4, 5),
}

# Which ability each caster class uses for spellcasting (spell DC / attack bonus)
SPELLCASTING_ABILITY = {
    "Bard": "CHA", "Cleric": "WIS", "Druid": "WIS", "Paladin": "CHA",
    "Ranger": "WIS", "Sorcerer": "CHA", "Warlock": "CHA", "Wizard": "INT",
}

# A curated set of well-known spells the bot can actually roll damage/healing
# for with /cast. This is NOT the full 5e spell list — building and maintaining
# accurate mechanics for all ~400 spells is out of scope. Spells not in this
# table still show as "known" on the sheet, but /cast falls back to just
# showing the caster's attack bonus/save DC so the player can roll manually.
#
# cast_type meanings:
#   "attack"  - roll a spell attack, then roll damage on a hit
#   "save"    - target rolls a save against the DC; damage rolls regardless
#               (half_on_save marks whether a successful save halves it,
#               or in a few cases like Sacred Flame/Vicious Mockery, negates it)
#   "auto"    - no attack or save, always hits (e.g. Magic Missile)
#   "heal"    - restores HP instead of dealing damage
#   "utility" - no damage/healing to roll (e.g. Shield); shown for completeness
#
# For leveled spells, "scaling_dice" is the extra dice added per spell slot
# level above the spell's minimum (upcasting). Cantrips instead scale by
# character level via CANTRIP_DICE_COUNT, not by slot.
SPELLS = {
    # Cantrips (level 0 — no slot required)
    "Fire Bolt":       {"level": 0, "school": "Evocation", "cast_type": "attack",
                         "damage_dice_base": "1d10", "damage_type": "fire"},
    "Ray of Frost":    {"level": 0, "school": "Evocation", "cast_type": "attack",
                         "damage_dice_base": "1d8", "damage_type": "cold"},
    "Eldritch Blast":  {"level": 0, "school": "Evocation", "cast_type": "attack",
                         "damage_dice_base": "1d10", "damage_type": "force"},
    "Sacred Flame":    {"level": 0, "school": "Evocation", "cast_type": "save",
                         "save_ability": "DEX", "half_on_save": False,
                         "damage_dice_base": "1d8", "damage_type": "radiant"},
    "Vicious Mockery":  {"level": 0, "school": "Enchantment", "cast_type": "save",
                         "save_ability": "WIS", "half_on_save": False,
                         "damage_dice_base": "1d4", "damage_type": "psychic"},

    # 1st level
    "Magic Missile":   {"level": 1, "school": "Evocation", "cast_type": "auto",
                         "darts_base": 3, "extra_dart_per_slot": 1,
                         "die_per_dart": "1d4", "flat_per_dart": 1, "damage_type": "force"},
    "Burning Hands":   {"level": 1, "school": "Evocation", "cast_type": "save",
                         "save_ability": "DEX", "half_on_save": True,
                         "damage_dice_base": "3d6", "scaling_dice": "1d6", "damage_type": "fire"},
    "Guiding Bolt":    {"level": 1, "school": "Evocation", "cast_type": "attack",
                         "damage_dice_base": "4d6", "scaling_dice": "1d6", "damage_type": "radiant"},
    "Cure Wounds":     {"level": 1, "school": "Evocation", "cast_type": "heal",
                         "heal_dice_base": "1d8", "scaling_dice": "1d8", "add_ability_mod": True},
    "Shield":          {"level": 1, "school": "Abjuration", "cast_type": "utility",
                         "description": "Reaction: +5 AC until the start of your next turn."},

    # 3rd level
    "Fireball":        {"level": 3, "school": "Evocation", "cast_type": "save",
                         "save_ability": "DEX", "half_on_save": True,
                         "damage_dice_base": "8d6", "scaling_dice": "1d6", "damage_type": "fire"},
    "Lightning Bolt":  {"level": 3, "school": "Evocation", "cast_type": "save",
                         "save_ability": "DEX", "half_on_save": True,
                         "damage_dice_base": "8d6", "scaling_dice": "1d6", "damage_type": "lightning"},
}


def cantrip_dice_multiplier(character_level: int) -> int:
    """Cantrips deal more dice at higher character levels (not slot levels)."""
    if character_level >= 17:
        return 4
    if character_level >= 11:
        return 3
    if character_level >= 5:
        return 2
    return 1
