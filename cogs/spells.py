"""
Spellcasting mechanics: handles spell slot calculations, upcasting, and roll resolution.
"""
import discord
from discord import app_commands
from discord.ext import commands

import database
from data.reference import (
    SPELLS, SPELLCASTING_ABILITY, CLASSES, FULL_CASTER_SLOTS, HALF_CASTER_SLOTS,
    PACT_CASTER_SLOTS, cantrip_dice_multiplier, ability_modifier, proficiency_bonus
)
from utils.sheet import ABILITY_TO_FIELD
from views.character_ui import PickCharacterView
from cogs.dice import roll_expression


def get_known_spells(character):
    return character.get("known_spells", [])


def max_available_slot_level(character):
    caster_type = CLASSES.get(character["class_name"], {}).get("caster")
    level = character["level"]
    if caster_type == "full":
        slots = FULL_CASTER_SLOTS.get(level, [])
        return len([s for s in slots if s])
    if caster_type == "half":
        slots = HALF_CASTER_SLOTS.get(level, [])
        return len([s for s in slots if s])
    if caster_type == "pact":
        _, slot_level = PACT_CASTER_SLOTS.get(level, (0, 0))
        return slot_level
    return 0


def scale_dice_expr(base_expr: str, scaling_die_expr: str, extra_levels: int) -> str:
    base_count, faces = base_expr.lower().split("d")
    scale_count, scale_faces = scaling_die_expr.lower().split("d")
    total_count = int(base_count) + int(scale_count) * max(0, extra_levels)
    return f"{total_count}d{faces}"


def format_school_header(spell_name: str, data: dict) -> str:
    level_label = "Cantrip" if data["level"] == 0 else f"Level {data['level']}"
    return f"**{spell_name}** ({level_label} {data['school']})"


class SpellSelect(discord.ui.Select):
    def __init__(self, on_pick, spell_names):
        options = [discord.SelectOption(label=s) for s in spell_names[:25]]
        super().__init__(placeholder="Which spell?", options=options)
        self.on_pick = on_pick

    async def callback(self, interaction: discord.Interaction):
        await self.on_pick(interaction, self.values[0])


class SpellPickView(discord.ui.View):
    def __init__(self, on_pick, spell_names):
        super().__init__(timeout=60)
        self.add_item(SpellSelect(on_pick, spell_names))


class SlotLevelSelect(discord.ui.Select):
    def __init__(self, on_pick, min_level, max_level):
        options = [discord.SelectOption(label=f"Level {n} slot", value=str(n))
                   for n in range(min_level, max_level + 1)]
        super().__init__(placeholder="Cast using which slot level?", options=options)
        self.on_pick = on_pick

    async def callback(self, interaction: discord.Interaction):
        await self.on_pick(interaction, int(self.values[0]))


class SlotLevelView(discord.ui.View):
    def __init__(self, on_pick, min_level, max_level):
        super().__init__(timeout=60)
        self.add_item(SlotLevelSelect(on_pick, min_level, max_level))


class Spells(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="cast", description="Cast one of your character's known spells")
    @app_commands.describe(target_ac="Optional: the target's AC, for attack-roll spells")
    async def cast(self, interaction: discord.Interaction, target_ac: int = None):
        characters = await database.get_characters_for_user(interaction.user.id, interaction.guild_id)
        casters = [c for c in characters if CLASSES.get(c["class_name"], {}).get("caster")]
        if not casters:
            await interaction.response.send_message(
                "None of your characters can cast spells yet — try `/newcharacter` with a caster class!",
                ephemeral=True
            )
            return

        async def character_chosen(inter, character):
            spell_names = get_known_spells(character)
            if not spell_names:
                await inter.response.edit_message(
                    content=f"**{character['name']}** doesn't know any spells yet.", view=None
                )
                return

            async def spell_chosen(inter2, spell_name):
                await self._resolve_spell_pick(inter2, character, spell_name, target_ac)

            await inter.response.edit_message(
                content=f"Which spell is **{character['name']}** casting?",
                view=SpellPickView(spell_chosen, spell_names)
            )

        await interaction.response.send_message(
            "Which character is casting?", view=PickCharacterView(casters, character_chosen), ephemeral=True
        )

    async def _resolve_spell_pick(self, interaction, character, spell_name, target_ac):
        data = SPELLS.get(spell_name)
        class_name = character["class_name"]
        spell_ability = SPELLCASTING_ABILITY.get(class_name)
        mod = ability_modifier(character[ABILITY_TO_FIELD[spell_ability]]) if spell_ability else 0
        prof = proficiency_bonus(character["level"])
        save_dc = 8 + prof + mod
        attack_bonus = prof + mod

        if not data:
            await interaction.response.edit_message(
                content=(f"I don't have built-in mechanics for **{spell_name}** yet.\n"
                         f"{character['name']}'s spell save DC is **{save_dc}**, spell attack is "
                         f"**+{attack_bonus}** — use `/roll` to roll damage manually."),
                view=None
            )
            return

        level = data["level"]
        if level == 0:
            await self._cast_and_reveal(interaction, character, spell_name, data, mod, save_dc, attack_bonus,
                                         slot_level=0, target_ac=target_ac)
            return

        max_slot = max_available_slot_level(character)
        caster_type = CLASSES.get(class_name, {}).get("caster")

        if max_slot < level:
            await interaction.response.edit_message(
                content=(f"**{character['name']}** doesn't have a high enough spell slot yet for "
                         f"{spell_name} (needs a level {level} slot)."),
                view=None
            )
            return

        if caster_type == "pact":
            await self._cast_and_reveal(interaction, character, spell_name, data, mod, save_dc, attack_bonus,
                                         slot_level=max_slot, target_ac=target_ac)
            return

        async def slot_chosen(inter, slot_level):
            await self._cast_and_reveal(inter, character, spell_name, data, mod, save_dc, attack_bonus,
                                         slot_level=slot_level, target_ac=target_ac)

        await interaction.response.edit_message(
            content=f"Cast **{spell_name}** using which slot level?",
            view=SlotLevelView(slot_chosen, level, max_slot)
        )

    async def _cast_and_reveal(self, interaction, character, spell_name, data, mod, save_dc, attack_bonus,
                                slot_level, target_ac):
        cast_type = data["cast_type"]
        header = format_school_header(spell_name, data)
        slot_note = f" using a level {slot_level} slot" if slot_level else ""
        lines = [f"✨ **{character['name']}** casts {header}{slot_note}"]

        if cast_type in ("attack", "save"):
            base = data["damage_dice_base"]
            if data["level"] == 0:
                count, faces = base.lower().split("d")
                total_count = int(count) * cantrip_dice_multiplier(character["level"])
                dmg_expr = f"{total_count}d{faces}"
            else:
                dmg_expr = scale_dice_expr(base, data["scaling_dice"], slot_level - data["level"])
            dmg_total, dmg_breakdown = roll_expression(dmg_expr)

            if cast_type == "attack":
                to_hit_total, to_hit_breakdown = roll_expression(
                    f"1d20{'+' if attack_bonus >= 0 else ''}{attack_bonus}"
                )
                hit_text = ""
                if target_ac is not None:
                    hit_text = " ✅ **HIT**" if to_hit_total >= target_ac else " ❌ **MISS**"
                lines.append(f"To-hit: {to_hit_breakdown} = **{to_hit_total}**{hit_text}")
                lines.append(f"Damage: {dmg_breakdown} = **{dmg_total}** {data['damage_type']}")
            else:
                save_note = "half damage on a successful save" if data["half_on_save"] else "no damage on a successful save"
                lines.append(f"Target saves vs **{data['save_ability']} DC {save_dc}** ({save_note})")
                lines.append(f"Damage: {dmg_breakdown} = **{dmg_total}** {data['damage_type']}")

        elif cast_type == "auto":
            extra_darts = data.get("extra_dart_per_slot", 0) * max(0, slot_level - data["level"])
            darts = data["darts_base"] + extra_darts
            die_count, die_faces = data["die_per_dart"].lower().split("d")
            total_dice = int(die_count) * darts
            flat = data["flat_per_dart"] * darts
            dmg_total, dmg_breakdown = roll_expression(f"{total_dice}d{die_faces}+{flat}")
            lines.append(f"{darts} dart(s) auto-hit, no roll needed")
            lines.append(f"Damage: {dmg_breakdown} = **{dmg_total}** {data['damage_type']}")

        elif cast_type == "heal":
            heal_expr = scale_dice_expr(data["heal_dice_base"], data["scaling_dice"], slot_level - data["level"])
            if data.get("add_ability_mod"):
                heal_expr += f"{'+' if mod >= 0 else ''}{mod}"
            heal_total, heal_breakdown = roll_expression(heal_expr)
            lines.append(f"Healing: {heal_breakdown} = **{heal_total}** HP restored")

        elif cast_type == "utility":
            lines.append(data.get("description", "No damage to roll — this is a utility spell."))

        content = "\n".join(lines)
        await interaction.response.edit_message(content="✅ Cast — see below!", view=None)
        await interaction.followup.send(content=content)


async def setup(bot):
    await bot.add_cog(Spells(bot))