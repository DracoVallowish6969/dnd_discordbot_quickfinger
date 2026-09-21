"""
Dice rolling commands: raw notation rolls and automated ability/skill/save checks.
"""
import re
import random
import discord
from discord import app_commands
from discord.ext import commands

import database
from data.reference import ability_modifier, proficiency_bonus, SKILLS, WEAPONS
from utils.sheet import ABILITY_TO_FIELD
from views.character_ui import PickCharacterView

DICE_PATTERN = re.compile(r"^(\d*)d(\d+)([+-]\d+)?$", re.IGNORECASE)


def roll_expression(expr: str):
    match = DICE_PATTERN.match(expr.strip().replace(" ", ""))
    if not match:
        raise ValueError(f"'{expr}' doesn't look like dice notation (try something like `1d20+5`)")
    num_dice = int(match.group(1)) if match.group(1) else 1
    die_size = int(match.group(2))
    modifier = int(match.group(3)) if match.group(3) else 0
    if num_dice > 100 or die_size > 1000:
        raise ValueError("That's a lot of dice — keep it under 100 dice / d1000.")
    rolls = [random.randint(1, die_size) for _ in range(num_dice)]
    total = sum(rolls) + modifier
    breakdown = f"[{', '.join(str(r) for r in rolls)}]"
    if modifier:
        breakdown += f" {'+' if modifier >= 0 else ''}{modifier}"
    return total, breakdown


class AbilitySelect(discord.ui.Select):
    def __init__(self, on_pick, mode: str, character: dict):
        options = [discord.SelectOption(label=a, value=a) for a in ["STR", "DEX", "CON", "INT", "WIS", "CHA"]]
        super().__init__(placeholder=f"Choose ability for the {mode}...", options=options)
        self.on_pick = on_pick
        self.mode = mode
        self.character = character

    async def callback(self, interaction: discord.Interaction):
        await self.on_pick(interaction, self.character, self.values[0], self.mode)


class PickAbilityView(discord.ui.View):
    def __init__(self, on_pick, mode, character):
        super().__init__(timeout=60)
        self.add_item(AbilitySelect(on_pick, mode, character))


class CheckOptionSelect(discord.ui.Select):
    def __init__(self, on_pick, character):
        options = []
        for ability in ["STR", "DEX", "CON", "INT", "WIS", "CHA"]:
            options.append(discord.SelectOption(label=f"{ability} (raw check)", value=f"RAW::{ability}"))
        for skill_name, governing_ability in SKILLS.items():
            options.append(discord.SelectOption(label=f"{skill_name} ({governing_ability})", value=f"SKILL::{skill_name}"))
        super().__init__(placeholder="Check what?", options=options[:25])
        self.on_pick = on_pick
        self.character = character

    async def callback(self, interaction: discord.Interaction):
        await self.on_pick(interaction, self.character, self.values[0])


class PickCheckView(discord.ui.View):
    def __init__(self, on_pick, character):
        super().__init__(timeout=60)
        self.add_item(CheckOptionSelect(on_pick, character))


class Dice(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="roll", description="Roll dice using standard notation, e.g. 1d20+5")
    async def roll(self, interaction: discord.Interaction, dice: str):
        try:
            total, breakdown = roll_expression(dice)
        except ValueError as e:
            await interaction.response.send_message(f"⚠️ {e}", ephemeral=True)
            return
        await interaction.response.send_message(
            f"🎲 **{interaction.user.display_name}** rolls `{dice}`: {breakdown} = **{total}**"
        )

    @app_commands.command(name="attack", description="Attack with your equipped weapon")
    @app_commands.describe(target_ac="Optional: the target's AC, to see if it's a hit")
    async def attack(self, interaction: discord.Interaction, target_ac: int = None):
        characters = await database.get_characters_for_user(interaction.user.id, interaction.guild_id)
        if not characters:
            await interaction.response.send_message(
                "You don't have any characters yet — try `/newcharacter` first!", ephemeral=True
            )
            return

        async def character_chosen(inter, character):
            weapon_name = character.get("weapon", "Unarmed Strike")
            weapon = WEAPONS.get(weapon_name, WEAPONS["Unarmed Strike"])
            ability_key = weapon["ability"]

            if ability_key == "finesse":
                mod = max(ability_modifier(character["str"]), ability_modifier(character["dex"]))
            else:
                mod = ability_modifier(character[ABILITY_TO_FIELD[ability_key]])

            attack_mod = mod + proficiency_bonus(character["level"])
            to_hit_total, to_hit_breakdown = roll_expression(f"1d20{'+' if attack_mod >= 0 else ''}{attack_mod}")

            hit_text = ""
            if target_ac is not None:
                hit_text = " ✅ **HIT**" if to_hit_total >= target_ac else " ❌ **MISS**"

            dmg_total, dmg_breakdown = roll_expression(f"{weapon['dice']}{'+' if mod >= 0 else ''}{mod}")

            content = (
                f"⚔️ **{character['name']}** attacks with **{weapon_name}**\n"
                f"To-hit: {to_hit_breakdown} = **{to_hit_total}**{hit_text}\n"
                f"Damage: {dmg_breakdown} = **{dmg_total}** {weapon['damage_type']}"
            )
            await inter.response.edit_message(content="✅ Rolled — see below!", view=None)
            await inter.followup.send(content=content)

        await interaction.response.send_message(
            "Which character is attacking?", view=PickCharacterView(characters, character_chosen), ephemeral=True
        )

    @app_commands.command(name="check", description="Roll an ability or skill check for one of your characters")
    async def check(self, interaction: discord.Interaction):
        characters = await database.get_characters_for_user(interaction.user.id, interaction.guild_id)
        if not characters:
            await interaction.response.send_message(
                "You don't have any characters yet — try `/newcharacter` first!", ephemeral=True
            )
            return

        async def option_chosen(inter, character, value):
            kind, key = value.split("::", 1)
            skill_profs = character.get("skill_proficiencies", [])

            if kind == "RAW":
                ability = key
                label = f"{ability} check"
                modifier = ability_modifier(character[ABILITY_TO_FIELD[ability]])
            else:
                skill_name = key
                ability = SKILLS[skill_name]
                label = f"{skill_name} check"
                modifier = ability_modifier(character[ABILITY_TO_FIELD[ability]])
                if skill_name in skill_profs:
                    modifier += proficiency_bonus(character["level"])

            total, breakdown = roll_expression(f"1d20{'+' if modifier >= 0 else ''}{modifier}")
            content = f"🎲 **{character['name']}** rolls a **{label}**: {breakdown} = **{total}**"
            await inter.response.edit_message(content="✅ Rolled — see below!", view=None)
            await inter.followup.send(content=content)

        async def character_chosen(inter, character):
            await inter.response.edit_message(
                content=f"What is {character['name']} checking?",
                view=PickCheckView(option_chosen, character)
            )

        await interaction.response.send_message(
            "Which character?", view=PickCharacterView(characters, character_chosen), ephemeral=True
        )

    @app_commands.command(name="save", description="Roll a saving throw for one of your characters")
    async def save(self, interaction: discord.Interaction):
        characters = await database.get_characters_for_user(interaction.user.id, interaction.guild_id)
        if not characters:
            await interaction.response.send_message(
                "You don't have any characters yet — try `/newcharacter` first!", ephemeral=True
            )
            return

        async def ability_chosen(inter, character, ability, mode):
            score = character[ABILITY_TO_FIELD[ability]]
            modifier = ability_modifier(score)
            proficient_saves = character.get("save_proficiencies", [])
            if ability in proficient_saves:
                modifier += proficiency_bonus(character["level"])
            total, breakdown = roll_expression(f"1d20{'+' if modifier >= 0 else ''}{modifier}")
            content = f"🛡️ **{character['name']}** rolls a **{ability}** save: {breakdown} = **{total}**"
            await inter.response.edit_message(content="✅ Rolled — see below!", view=None)
            await inter.followup.send(content=content)

        async def character_chosen(inter, character):
            await inter.response.edit_message(
                content=f"Which ability is {character['name']} saving with?",
                view=PickAbilityView(ability_chosen, "save", character)
            )

        await interaction.response.send_message(
            "Which character?", view=PickCharacterView(characters, character_chosen), ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(Dice(bot))