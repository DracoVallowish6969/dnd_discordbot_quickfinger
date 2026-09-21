"""
The character creation wizard, management commands, and wizard router.
"""
import random
import discord
from discord import app_commands
from discord.ext import commands

import database
from data.reference import (
    RACES, CLASSES, SKILLS, WEAPONS, ARMOR, STARTING_GEAR, DEFAULT_HOMEBREW_GEAR,
    ability_modifier
)
from utils.sheet import (
    compute_hp, build_sheet_embed, recalculate_character_stats,
    get_homebrew_features_for, get_homebrew_race_traits_for
)
from views.character_ui import (
    PickCharacterView, MultiPickCharacterView, ConfirmView, NameModal, RaceView,
    ClassView, LevelPickView, ScoreMethodView, DiceResultView, AssignArrayView,
    CustomScorePart1Modal, CustomScorePart2Modal, ModalTriggerView, SkillPickView,
    WeaponPickView, ArmorPickView, ShieldView, SpellsModal, HomebrewInfoModal,
    HitDieView, SavesView, HomebrewFeaturesModal, RaceNameModal, RaceTraitsModal,
    EditCategoryView
)

ABILITIES = ["STR", "DEX", "CON", "INT", "WIS", "CHA"]
MIN_CUSTOM_SCORE = 1
MAX_CUSTOM_SCORE = 30


def roll_ability_array():
    results = []
    for _ in range(6):
        dice = sorted(random.randint(1, 6) for _ in range(4))
        results.append(sum(dice[1:]))
    return sorted(results, reverse=True)


def parse_score(raw: str):
    try:
        value = int(str(raw).strip())
    except ValueError:
        return None
    if value < MIN_CUSTOM_SCORE or value > MAX_CUSTOM_SCORE:
        return None
    return value


class Character(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="newcharacter", description="Create a new D&D character step by step")
    async def newcharacter(self, interaction: discord.Interaction):
        state = {"user_id": interaction.user.id, "guild_id": interaction.guild_id}

        async def name_submitted(inter, name):
            state["name"] = name
            custom_races = await database.get_custom_races(inter.guild_id)
            await inter.response.send_message(
                f"Nice, **{name}**! Now pick a race:", view=RaceView(race_chosen, custom_races), ephemeral=True
            )

        async def race_chosen(inter, race):
            if race == "__new_custom_race__":
                await inter.response.send_modal(RaceNameModal(
                    lambda i, n: self._start_custom_race_flow(i, n, resume_cb=race_chosen)
                ))
                return

            if race in RACES:
                state["race"] = race
                state["is_homebrew_race"] = False
            else:
                custom_race = await database.get_custom_race_by_name(inter.guild_id, race)
                state["race"] = custom_race["name"]
                state["is_homebrew_race"] = True

            custom_classes = await database.get_custom_classes(inter.guild_id)
            await inter.response.edit_message(
                content=f"Race: **{race}**. Now pick a class:",
                view=ClassView(class_chosen, custom_classes)
            )

        async def class_chosen(inter, class_name):
            if class_name == "__new_homebrew__":
                await inter.response.send_modal(HomebrewInfoModal(
                    lambda i, n: self._start_homebrew_flow(i, n, resume_after=state, resume_cb=class_chosen)
                ))
                return

            standard = CLASSES.get(class_name)
            if standard:
                state["class_name"] = class_name
                state["is_homebrew_class"] = False
                state["save_proficiencies"] = standard["saves"]
                state["skill_list"] = standard["skill_list"]
                state["skill_choices"] = standard["skill_choices"]
                state["gear_options"] = STARTING_GEAR.get(class_name, DEFAULT_HOMEBREW_GEAR)
                state["caster_type"] = standard["caster"]
                hit_die = standard["hit_die"]
            else:
                custom = await database.get_custom_class_by_name(inter.guild_id, class_name)
                state["class_name"] = custom["name"]
                state["is_homebrew_class"] = True
                state["save_proficiencies"] = custom["saves"]
                state["skill_list"] = custom["skill_list"]
                state["skill_choices"] = custom["skill_choices"]
                state["gear_options"] = DEFAULT_HOMEBREW_GEAR
                state["caster_type"] = None
                hit_die = custom["hit_die"]

            state["hit_die"] = hit_die
            state["scores"] = {}
            await inter.response.edit_message(
                content=f"Class: **{class_name}**. What level is this character?",
                view=LevelPickView(level_chosen)
            )

        async def level_chosen(inter, level):
            state["level"] = level
            await inter.response.edit_message(
                content=(f"Level **{level}**. How do you want to set ability scores?\n"
                         f"Roll dice for a random set, or type in your own numbers if you already "
                         f"have a character sheet made."),
                view=ScoreMethodView(method_chosen)
            )

        async def method_chosen(inter, method):
            if method == "custom":
                await inter.response.send_modal(CustomScorePart1Modal(custom_part1_submitted))
                return

            state["remaining_array"] = roll_ability_array()
            await inter.response.edit_message(
                content=(f"🎲 Rolled: `{state['remaining_array']}`\n"
                         f"Happy with these, or want to try again?"),
                view=DiceResultView(dice_confirmed, dice_reroll)
            )

        async def dice_reroll(inter, _method):
            state["remaining_array"] = roll_ability_array()
            await inter.response.edit_message(
                content=(f"🎲 Rerolled: `{state['remaining_array']}`\n"
                         f"Happy with these, or want to try again?"),
                view=DiceResultView(dice_confirmed, dice_reroll)
            )

        async def dice_confirmed(inter, _method):
            await inter.response.edit_message(
                content=(f"Scores to assign: `{state['remaining_array']}`\n"
                         f"Tap an ability, and its next score is `{state['remaining_array'][0]}`. "
                         f"Put your biggest number on what matters most for this class!"),
                view=AssignArrayView(score_assigned, ABILITIES)
            )

        async def score_assigned(inter, ability):
            value = state["remaining_array"].pop(0)
            state["scores"][ability] = value
            remaining_abilities = [a for a in ABILITIES if a not in state["scores"]]
            if remaining_abilities:
                await inter.response.edit_message(
                    content=(f"{ability} = **{value}**. Next score is `{state['remaining_array'][0]}` "
                             f"— pick another ability:"),
                    view=AssignArrayView(score_assigned, remaining_abilities)
                )
            else:
                await self._prompt_skills(inter, state, skills_chosen, use_edit=True)

        async def custom_part1_submitted(inter, values):
            parsed = {k: parse_score(v) for k, v in values.items()}
            if any(v is None for v in parsed.values()):
                async def reopen(reopen_inter):
                    await reopen_inter.response.send_modal(CustomScorePart1Modal(custom_part1_submitted))
                await inter.response.send_message(
                    f"⚠️ Ability scores need to be whole numbers between {MIN_CUSTOM_SCORE} and "
                    f"{MAX_CUSTOM_SCORE}. Let's try that again:",
                    view=ModalTriggerView(reopen, label="Try again"), ephemeral=True
                )
                return
            state["scores"].update(parsed)

            async def open_part2(part2_inter):
                await part2_inter.response.send_modal(CustomScorePart2Modal(custom_part2_submitted))

            await inter.response.send_message(
                f"STR **{parsed['STR']}**, DEX **{parsed['DEX']}**, CON **{parsed['CON']}** set. "
                f"Tap below to enter INT, WIS, and CHA:",
                view=ModalTriggerView(open_part2, label="Continue ➜ INT / WIS / CHA"), ephemeral=True
            )

        async def custom_part2_submitted(inter, values):
            parsed = {k: parse_score(v) for k, v in values.items()}
            if any(v is None for v in parsed.values()):
                async def reopen(reopen_inter):
                    await reopen_inter.response.send_modal(CustomScorePart2Modal(custom_part2_submitted))
                await inter.response.send_message(
                    f"⚠️ Ability scores need to be whole numbers between {MIN_CUSTOM_SCORE} and "
                    f"{MAX_CUSTOM_SCORE}. Let's try that again:",
                    view=ModalTriggerView(reopen, label="Try again"), ephemeral=True
                )
                return
            state["scores"].update(parsed)
            await self._prompt_skills(inter, state, skills_chosen, use_edit=False)

        async def skills_chosen(inter, skills):
            state["skill_proficiencies"] = list(skills)
            weapon_options = state["gear_options"]["weapons"]
            await inter.response.edit_message(
                content="Skills set! Now pick your starting weapon:",
                view=WeaponPickView(weapon_chosen, weapon_options)
            )

        async def weapon_chosen(inter, weapon):
            state["weapon"] = weapon
            armor_options = state["gear_options"]["armor"]
            await inter.response.edit_message(
                content=f"Weapon: **{weapon}**. Now pick your starting armor:",
                view=ArmorPickView(armor_chosen, armor_options)
            )

        async def armor_chosen(inter, armor):
            state["armor"] = armor
            two_handed = {"Greatsword", "Greataxe", "Longbow", "Shortbow", "Light Crossbow"}
            if state["weapon"] in two_handed:
                state["has_shield"] = False
                await self._maybe_ask_spells(inter, state, use_edit=True)
            else:
                await inter.response.edit_message(
                    content=f"Armor: **{armor}**. Want to carry a shield too?",
                    view=ShieldView(shield_chosen)
                )

        async def shield_chosen(inter, wants_shield):
            state["has_shield"] = wants_shield
            await self._maybe_ask_spells(inter, state, use_edit=True)

        async def spells_submitted(inter, spells):
            state["known_spells"] = spells
            await self._finalize_character(inter, state)

        state["_spells_submitted_callback"] = spells_submitted
        await interaction.response.send_modal(NameModal(name_submitted))

    async def _prompt_skills(self, interaction, state, skills_chosen_callback, use_edit: bool):
        n = state["skill_choices"]
        content = f"Scores set! Now pick **{n}** skill{'s' if n != 1 else ''} your character is trained in:"
        view = SkillPickView(skills_chosen_callback, state["skill_list"], n)
        if use_edit:
            await interaction.response.edit_message(content=content, view=view)
        else:
            await interaction.response.send_message(content=content, view=view, ephemeral=True)

    async def _start_homebrew_flow(self, interaction, class_name, resume_after, resume_cb):
        state = {"guild_id": interaction.guild_id, "created_by": interaction.user.id, "name": class_name}

        async def hit_die_chosen(inter, hit_die):
            state["hit_die"] = hit_die
            await inter.response.edit_message(
                content=f"**{class_name}** uses a d{hit_die} hit die. Now pick 2 saving throw proficiencies:",
                view=SavesView(saves_chosen)
            )

        async def saves_chosen(inter, saves):
            state["saves"] = list(saves)
            state["skill_choices"] = 2
            state["skill_list"] = list(SKILLS.keys())
            state["is_caster"] = False
            await inter.response.send_modal(HomebrewFeaturesModal(features_submitted))

        async def features_submitted(inter, feature_lines):
            state["features"] = feature_lines
            await database.save_custom_class(state)
            feature_summary = f" with {len(feature_lines)} feature(s)" if feature_lines else " (no features written)"
            await inter.response.send_message(
                content=(f"✅ Homebrew class **{class_name}** created! (d{state['hit_die']} hit die, "
                         f"saves: {', '.join(state['saves'])}){feature_summary}.\n\nNow pick your class again "
                         f"from the list to continue building your character:"),
                view=ClassView(resume_cb, await database.get_custom_classes(interaction.guild_id)),
                ephemeral=True
            )

        await interaction.response.send_message(
            f"Building homebrew class **{class_name}**. Pick a hit die:",
            view=HitDieView(hit_die_chosen), ephemeral=True
        )

    async def _start_custom_race_flow(self, interaction, race_name, resume_cb):
        state = {"guild_id": interaction.guild_id, "created_by": interaction.user.id, "name": race_name}

        async def asi_chosen(inter, abilities):
            state["asi"] = list(abilities)
            await inter.response.send_modal(RaceTraitsModal(traits_submitted))

        async def traits_submitted(inter, trait_lines):
            state["traits"] = trait_lines
            await database.save_custom_race(state)
            trait_summary = f" with {len(trait_lines)} trait(s)" if trait_lines else " (no traits written)"
            await inter.response.send_message(
                content=(f"✅ Custom race **{race_name}** created! (+1 {', '.join(state['asi'])}){trait_summary}.\n\n"
                         f"Now pick your race again from the list to continue building your character:"),
                view=RaceView(resume_cb, await database.get_custom_races(interaction.guild_id)),
                ephemeral=True
            )

        await interaction.response.send_message(
            f"Building custom race **{race_name}**. Pick 2 abilities to get +1 each:",
            view=SavesView(asi_chosen, placeholder="Pick exactly 2 abilities to get +1 each..."),
            ephemeral=True
        )

    async def _maybe_ask_spells(self, interaction, state, use_edit: bool):
        if state.get("caster_type"):
            callback = state["_spells_submitted_callback"]
            await interaction.response.send_modal(SpellsModal(callback))
        else:
            await self._finalize_character(interaction, state, use_edit=use_edit)

    async def _finalize_character(self, interaction, state, use_edit: bool = True):
        scores = state["scores"]
        if state.get("is_homebrew_race"):
            custom_race = await database.get_custom_race_by_name(state["guild_id"], state["race"])
            asi_list = custom_race.get("asi", []) if custom_race else []
            race_bonus = {a: 1 for a in asi_list}
        else:
            race_bonus = RACES[state["race"]]["asi"]
        final_scores = {a: scores[a] + race_bonus.get(a, 0) for a in ABILITIES}
        level = state.get("level", 1)

        max_hp = compute_hp(state["hit_die"], final_scores["CON"], level=level)
        dex_mod = ability_modifier(final_scores["DEX"])

        armor_data = ARMOR[state["armor"]]
        dex_cap = armor_data["dex_cap"]
        effective_dex_bonus = dex_mod if dex_cap is None else min(dex_mod, dex_cap)
        ac = armor_data["base_ac"] + effective_dex_bonus
        if state.get("has_shield"):
            ac += ARMOR["Shield"]["ac_bonus"]

        character_data = {
            "user_id": state["user_id"],
            "guild_id": state["guild_id"],
            "name": state["name"],
            "race": state["race"],
            "class_name": state["class_name"],
            "is_homebrew_class": state["is_homebrew_class"],
            "level": level,
            "str": final_scores["STR"], "dex": final_scores["DEX"], "con": final_scores["CON"],
            "intl": final_scores["INT"], "wis": final_scores["WIS"], "cha": final_scores["CHA"],
            "max_hp": max_hp, "current_hp": max_hp, "ac": ac,
            "skill_proficiencies": state.get("skill_proficiencies", []),
            "save_proficiencies": state["save_proficiencies"],
            "weapon": state.get("weapon", "Unarmed Strike"),
            "armor": state.get("armor", "None"),
            "has_shield": state.get("has_shield", False),
            "known_spells": state.get("known_spells", []),
            "is_homebrew_race": state.get("is_homebrew_race", False),
        }
        char_id = await database.save_character(character_data)
        character_data["id"] = char_id

        embed = build_sheet_embed(
            character_data,
            await get_homebrew_features_for(character_data),
            await get_homebrew_race_traits_for(character_data)
        )
        if use_edit:
            await interaction.response.edit_message(
                content=f"🎉 **{state['name']}** is ready to adventure!", view=None
            )
        else:
            await interaction.response.send_message(
                content=f"🎉 **{state['name']}** is ready to adventure!", ephemeral=True
            )
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="sheet", description="View one of your characters' sheets")
    async def sheet(self, interaction: discord.Interaction, name: str = None):
        if name:
            character = await database.get_character_by_name(interaction.user.id, interaction.guild_id, name)
            if not character:
                await interaction.response.send_message(f"Couldn't find a character named '{name}'.", ephemeral=True)
                return
            await interaction.response.send_message(
                embed=build_sheet_embed(
                    character,
                    await get_homebrew_features_for(character),
                    await get_homebrew_race_traits_for(character)
                )
            )
        else:
            characters = await database.get_characters_for_user(interaction.user.id, interaction.guild_id)
            if not characters:
                await interaction.response.send_message(
                    "You don't have any characters yet — try `/newcharacter`!", ephemeral=True
                )
                return
            if len(characters) == 1:
                character = characters[0]
                await interaction.response.send_message(
                    embed=build_sheet_embed(
                        character,
                        await get_homebrew_features_for(character),
                        await get_homebrew_race_traits_for(character)
                    )
                )
            else:
                names = ", ".join(c["name"] for c in characters)
                await interaction.response.send_message(
                    f"You have multiple characters: {names}. Use `/sheet name:<name>` to pick one.",
                    ephemeral=True
                )

    @app_commands.command(name="editcharacter", description="Edit an existing character's details")
    async def editcharacter(self, interaction: discord.Interaction):
        characters = await database.get_characters_for_user(interaction.user.id, interaction.guild_id)
        if not characters:
            await interaction.response.send_message(
                "You don't have any characters to edit yet — try `/newcharacter`!", ephemeral=True
            )
            return

        async def character_chosen(inter, character):
            async def category_chosen(inter_cat, category):
                if category == "name":
                    async def name_edited(inter_name, new_name):
                        character["name"] = new_name
                        await recalculate_and_save(inter_name, character)
                    await inter_cat.response.send_modal(NameModal(name_edited))

                elif category == "level":
                    async def level_edited(inter_lvl, new_level):
                        character["level"] = new_level
                        await recalculate_and_save(inter_lvl, character)
                    await inter_cat.response.edit_message(
                        content=f"Pick a new level for **{character['name']}**:",
                        view=LevelPickView(level_edited)
                    )

                elif category == "weapon":
                    weapon_options = list(WEAPONS.keys())
                    async def weapon_edited(inter_wep, new_weapon):
                        character["weapon"] = new_weapon
                        two_handed = {"Greatsword", "Greataxe", "Longbow", "Shortbow", "Light Crossbow"}
                        if new_weapon in two_handed:
                            character["has_shield"] = False
                        await recalculate_and_save(inter_wep, character)
                    await inter_cat.response.edit_message(
                        content=f"Pick a new weapon for **{character['name']}**:",
                        view=WeaponPickView(weapon_edited, weapon_options)
                    )

                elif category == "armor":
                    armor_options = [a for a in ARMOR.keys() if a != "Shield"]
                    async def armor_edited(inter_arm, new_armor):
                        character["armor"] = new_armor
                        two_handed = {"Greatsword", "Greataxe", "Longbow", "Shortbow", "Light Crossbow"}

                        if character.get("weapon") in two_handed:
                            character["has_shield"] = False
                            await recalculate_and_save(inter_arm, character)
                        else:
                            async def shield_edited(inter_shd, wants_shield):
                                character["has_shield"] = wants_shield
                                await recalculate_and_save(inter_shd, character)
                            await inter_arm.response.edit_message(
                                content=f"Armor set to **{new_armor}**. Want to carry a shield (+2 AC)?",
                                view=ShieldView(shield_edited)
                            )
                    await inter_cat.response.edit_message(
                        content=f"Pick new armor for **{character['name']}**:",
                        view=ArmorPickView(armor_edited, armor_options)
                    )

                elif category == "spells":
                    async def spells_edited(inter_spl, new_spells):
                        character["known_spells"] = new_spells
                        await recalculate_and_save(inter_spl, character)
                    await inter_cat.response.send_modal(SpellsModal(spells_edited))

            await inter.response.edit_message(
                content=f"Editing **{character['name']}**. What would you like to edit?",
                view=EditCategoryView(category_chosen)
            )

        async def recalculate_and_save(inter_save, char_obj):
            char_obj = await recalculate_character_stats(char_obj)
            await database.update_character(char_obj)
            embed = build_sheet_embed(
                char_obj,
                await get_homebrew_features_for(char_obj),
                await get_homebrew_race_traits_for(char_obj)
            )
            await inter_save.response.edit_message(
                content=f"✅ Updated **{char_obj['name']}**!", view=None
            )
            await inter_save.followup.send(embed=embed)

        await interaction.response.send_message(
            "Which character would you like to edit?",
            view=PickCharacterView(characters, character_chosen),
            ephemeral=True
        )

    @app_commands.command(name="damage", description="Apply damage to one of your characters")
    @app_commands.describe(amount="How much damage to apply")
    async def damage(self, interaction: discord.Interaction, amount: int):
        if amount < 0:
            await interaction.response.send_message(
                "Damage amount can't be negative — use `/heal` to restore HP instead.", ephemeral=True
            )
            return
        characters = await database.get_characters_for_user(interaction.user.id, interaction.guild_id)
        if not characters:
            await interaction.response.send_message(
                "You don't have any characters yet — try `/newcharacter`!", ephemeral=True
            )
            return

        async def character_chosen(inter, character):
            old_hp = character["current_hp"]
            new_hp = max(0, old_hp - amount)
            await database.update_hp(character["id"], new_hp)
            status = " 💀 **Down!**" if new_hp == 0 else ""
            content = (f"💥 **{character['name']}** takes **{amount}** damage: "
                       f"{old_hp} → **{new_hp}**/{character['max_hp']} HP{status}")
            await inter.response.edit_message(content="✅ Applied — see below!", view=None)
            await inter.followup.send(content=content)

        await interaction.response.send_message(
            "Which character is taking damage?", view=PickCharacterView(characters, character_chosen),
            ephemeral=True
        )

    @app_commands.command(name="heal", description="Heal one of your characters")
    @app_commands.describe(amount="How much HP to restore")
    async def heal(self, interaction: discord.Interaction, amount: int):
        if amount < 0:
            await interaction.response.send_message(
                "Healing amount can't be negative — use `/damage` to apply damage instead.", ephemeral=True
            )
            return
        characters = await database.get_characters_for_user(interaction.user.id, interaction.guild_id)
        if not characters:
            await interaction.response.send_message(
                "You don't have any characters yet — try `/newcharacter`!", ephemeral=True
            )
            return

        async def character_chosen(inter, character):
            old_hp = character["current_hp"]
            new_hp = min(character["max_hp"], old_hp + amount)
            await database.update_hp(character["id"], new_hp)
            content = (f"💚 **{character['name']}** heals **{amount}** HP: "
                       f"{old_hp} → **{new_hp}**/{character['max_hp']} HP")
            await inter.response.edit_message(content="✅ Applied — see below!", view=None)
            await inter.followup.send(content=content)

        await interaction.response.send_message(
            "Which character is healing?", view=PickCharacterView(characters, character_chosen),
            ephemeral=True
        )

    @app_commands.command(name="mycharacters", description="View a list of all your characters")
    async def mycharacters(self, interaction: discord.Interaction):
        characters = await database.get_characters_for_user(interaction.user.id, interaction.guild_id)
        if not characters:
            await interaction.response.send_message(
                "You don't have any characters yet — try `/newcharacter`!", ephemeral=True
            )
            return

        lines = []
        for c in characters:
            race_tag = "🔧" if c.get("is_homebrew_race") else ""
            class_tag = "🔧" if c.get("is_homebrew_class") else ""
            lines.append(
                f"**{c['name']}** — Level {c['level']} {race_tag}{c['race']} {class_tag}{c['class_name']}\n"
                f"HP: {c['current_hp']}/{c['max_hp']}  |  AC: {c['ac']}"
            )

        embed = discord.Embed(
            title=f"{interaction.user.display_name}'s Characters",
            description="\n\n".join(lines),
            color=discord.Color.dark_gold()
        )
        embed.set_footer(text="Use /sheet name:<name> to see full details for one of them.")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="deletecharacter", description="Permanently delete one of your characters")
    async def deletecharacter(self, interaction: discord.Interaction):
        characters = await database.get_characters_for_user(interaction.user.id, interaction.guild_id)
        if not characters:
            await interaction.response.send_message(
                "You don't have any characters yet — try `/newcharacter`!", ephemeral=True
            )
            return

        async def character_chosen(inter, character):
            async def confirmed(inter2, yes):
                if yes:
                    deleted = await database.delete_character(character["id"], interaction.user.id)
                    content = (f"🗑️ **{character['name']}** has been permanently deleted." if deleted
                               else "Something went wrong — that character couldn't be deleted.")
                else:
                    content = f"Cancelled — **{character['name']}** was not deleted."
                await inter2.response.edit_message(content=content, view=None)

            await inter.response.edit_message(
                content=(f"⚠️ Are you sure you want to permanently delete **{character['name']}**? "
                         f"This cannot be undone."),
                view=ConfirmView(confirmed, confirm_label="🗑️ Yes, delete permanently")
            )

        await interaction.response.send_message(
            "Which character do you want to delete?", view=PickCharacterView(characters, character_chosen),
            ephemeral=True
        )

    @app_commands.command(name="deletecharacters", description="Permanently delete multiple characters at once")
    async def deletecharacters(self, interaction: discord.Interaction):
        characters = await database.get_characters_for_user(interaction.user.id, interaction.guild_id)
        if not characters:
            await interaction.response.send_message(
                "You don't have any characters yet — try `/newcharacter`!", ephemeral=True
            )
            return

        async def characters_chosen(inter, selected):
            names = ", ".join(c["name"] for c in selected)

            async def confirmed(inter2, yes):
                if yes:
                    deleted_names = []
                    for c in selected:
                        if await database.delete_character(c["id"], interaction.user.id):
                            deleted_names.append(c["name"])
                    content = (f"🗑️ Deleted: {', '.join(deleted_names)}" if deleted_names
                               else "Nothing was deleted — something went wrong.")
                else:
                    content = "Cancelled — no characters were deleted."
                await inter2.response.edit_message(content=content, view=None)

            await inter.response.edit_message(
                content=(f"⚠️ Are you sure you want to permanently delete **{len(selected)}** "
                         f"character(s): {names}? This cannot be undone."),
                view=ConfirmView(confirmed, confirm_label="🗑️ Yes, delete them all")
            )

        await interaction.response.send_message(
            "Select one or more characters to delete:",
            view=MultiPickCharacterView(characters, characters_chosen), ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(Character(bot))