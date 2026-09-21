"""
Discord UI Components: Modals, Select Menus, and Action Buttons.
"""
import re
import discord
from data.reference import RACES, CLASSES, SKILLS, WEAPONS

ABILITIES = ["STR", "DEX", "CON", "INT", "WIS", "CHA"]


class CharacterSelect(discord.ui.Select):
    def __init__(self, characters, on_pick):
        options = [discord.SelectOption(label=c["name"], value=str(c["id"])) for c in characters]
        super().__init__(placeholder="Choose your character...", options=options)
        self.characters = {str(c["id"]): c for c in characters}
        self.on_pick = on_pick

    async def callback(self, interaction: discord.Interaction):
        await self.on_pick(interaction, self.characters[self.values[0]])


class PickCharacterView(discord.ui.View):
    def __init__(self, characters, on_pick):
        super().__init__(timeout=60)
        self.add_item(CharacterSelect(characters, on_pick))


class MultiCharacterSelect(discord.ui.Select):
    def __init__(self, characters, on_pick):
        options = [discord.SelectOption(label=c["name"], value=str(c["id"])) for c in characters[:25]]
        super().__init__(placeholder="Choose one or more characters...", options=options,
                          min_values=1, max_values=len(options))
        self.characters = {str(c["id"]): c for c in characters}
        self.on_pick = on_pick

    async def callback(self, interaction: discord.Interaction):
        selected = [self.characters[v] for v in self.values]
        await self.on_pick(interaction, selected)


class MultiPickCharacterView(discord.ui.View):
    def __init__(self, characters, on_pick):
        super().__init__(timeout=60)
        self.add_item(MultiCharacterSelect(characters, on_pick))


class ConfirmButton(discord.ui.Button):
    def __init__(self, label, confirmed, on_pick, style):
        super().__init__(label=label, style=style)
        self.confirmed = confirmed
        self.on_pick = on_pick

    async def callback(self, interaction: discord.Interaction):
        await self.on_pick(interaction, self.confirmed)


class ConfirmView(discord.ui.View):
    def __init__(self, on_pick, confirm_label="Yes, I'm sure", cancel_label="Cancel"):
        super().__init__(timeout=60)
        self.add_item(ConfirmButton(confirm_label, True, on_pick, discord.ButtonStyle.danger))
        self.add_item(ConfirmButton(cancel_label, False, on_pick, discord.ButtonStyle.secondary))


class NameModal(discord.ui.Modal, title="Name your character"):
    name = discord.ui.TextInput(label="Character name", placeholder="e.g. Dumbeldoor", max_length=50)

    def __init__(self, on_submit_callback):
        super().__init__()
        self.on_submit_callback = on_submit_callback

    async def on_submit(self, interaction: discord.Interaction):
        await self.on_submit_callback(interaction, str(self.name))


class RaceSelect(discord.ui.Select):
    def __init__(self, on_pick, custom_races):
        options = [discord.SelectOption(label=r) for r in RACES.keys()]
        for cr in custom_races:
            options.append(discord.SelectOption(label=f"🔧 {cr['name']} (custom)", value=cr["name"]))
        options.append(discord.SelectOption(label="✨ Create a custom race...", value="__new_custom_race__"))
        super().__init__(placeholder="Choose a race...", options=options[:25])
        self.on_pick = on_pick

    async def callback(self, interaction: discord.Interaction):
        await self.on_pick(interaction, self.values[0])


class RaceView(discord.ui.View):
    def __init__(self, on_pick, custom_races):
        super().__init__(timeout=180)
        self.add_item(RaceSelect(on_pick, custom_races))


class ClassSelect(discord.ui.Select):
    def __init__(self, on_pick, custom_classes):
        options = [discord.SelectOption(label=c) for c in CLASSES.keys()]
        for cc in custom_classes:
            options.append(discord.SelectOption(label=f"🔧 {cc['name']} (homebrew)", value=cc["name"]))
        options.append(discord.SelectOption(label="✨ Create a new homebrew class...", value="__new_homebrew__"))
        super().__init__(placeholder="Choose a class...", options=options[:25])
        self.on_pick = on_pick

    async def callback(self, interaction: discord.Interaction):
        await self.on_pick(interaction, self.values[0])


class ClassView(discord.ui.View):
    def __init__(self, on_pick, custom_classes):
        super().__init__(timeout=180)
        self.add_item(ClassSelect(on_pick, custom_classes))


class LevelSelect(discord.ui.Select):
    def __init__(self, on_pick):
        options = [discord.SelectOption(label=f"Level {n}", value=str(n)) for n in range(1, 21)]
        super().__init__(placeholder="Choose a starting level...", options=options)
        self.on_pick = on_pick

    async def callback(self, interaction: discord.Interaction):
        await self.on_pick(interaction, int(self.values[0]))


class LevelPickView(discord.ui.View):
    def __init__(self, on_pick):
        super().__init__(timeout=180)
        self.add_item(LevelSelect(on_pick))


class AssignScoreButton(discord.ui.Button):
    def __init__(self, ability, on_pick):
        super().__init__(label=ability, style=discord.ButtonStyle.primary)
        self.ability = ability
        self.on_pick = on_pick

    async def callback(self, interaction: discord.Interaction):
        await self.on_pick(interaction, self.ability)


class AssignArrayView(discord.ui.View):
    def __init__(self, on_pick, remaining_abilities):
        super().__init__(timeout=180)
        for ability in remaining_abilities:
            self.add_item(AssignScoreButton(ability, on_pick))


class ScoreMethodButton(discord.ui.Button):
    def __init__(self, label, method, on_pick, style=discord.ButtonStyle.primary):
        super().__init__(label=label, style=style)
        self.method = method
        self.on_pick = on_pick

    async def callback(self, interaction: discord.Interaction):
        await self.on_pick(interaction, self.method)


class ScoreMethodView(discord.ui.View):
    def __init__(self, on_pick):
        super().__init__(timeout=180)
        self.add_item(ScoreMethodButton("🎲 Roll dice for me", "roll", on_pick))
        self.add_item(ScoreMethodButton("✍️ I'll type my own numbers", "custom", on_pick,
                                          style=discord.ButtonStyle.secondary))


class DiceResultView(discord.ui.View):
    def __init__(self, on_use, on_reroll):
        super().__init__(timeout=180)
        self.add_item(ScoreMethodButton("✅ Use these", "use", on_use))
        self.add_item(ScoreMethodButton("🎲 Reroll", "reroll", on_reroll, style=discord.ButtonStyle.secondary))


class CustomScorePart1Modal(discord.ui.Modal, title="Enter your ability scores (1/2)"):
    str_score = discord.ui.TextInput(label="STR", placeholder="e.g. 15", max_length=3)
    dex_score = discord.ui.TextInput(label="DEX", placeholder="e.g. 14", max_length=3)
    con_score = discord.ui.TextInput(label="CON", placeholder="e.g. 13", max_length=3)

    def __init__(self, on_submit_callback):
        super().__init__()
        self.on_submit_callback = on_submit_callback

    async def on_submit(self, interaction: discord.Interaction):
        await self.on_submit_callback(
            interaction, {"STR": str(self.str_score), "DEX": str(self.dex_score), "CON": str(self.con_score)}
        )


class CustomScorePart2Modal(discord.ui.Modal, title="Enter your ability scores (2/2)"):
    int_score = discord.ui.TextInput(label="INT", placeholder="e.g. 12", max_length=3)
    wis_score = discord.ui.TextInput(label="WIS", placeholder="e.g. 10", max_length=3)
    cha_score = discord.ui.TextInput(label="CHA", placeholder="e.g. 8", max_length=3)

    def __init__(self, on_submit_callback):
        super().__init__()
        self.on_submit_callback = on_submit_callback

    async def on_submit(self, interaction: discord.Interaction):
        await self.on_submit_callback(
            interaction, {"INT": str(self.int_score), "WIS": str(self.wis_score), "CHA": str(self.cha_score)}
        )


class ModalTriggerButton(discord.ui.Button):
    def __init__(self, label, open_modal_callback):
        super().__init__(label=label, style=discord.ButtonStyle.primary)
        self.open_modal_callback = open_modal_callback

    async def callback(self, interaction: discord.Interaction):
        await self.open_modal_callback(interaction)


class ModalTriggerView(discord.ui.View):
    def __init__(self, open_modal_callback, label="Continue"):
        super().__init__(timeout=180)
        self.add_item(ModalTriggerButton(label, open_modal_callback))


class SkillMultiSelect(discord.ui.Select):
    def __init__(self, on_pick, skill_list, num_choices):
        options = [discord.SelectOption(label=f"{s} ({SKILLS[s]})", value=s) for s in skill_list[:25]]
        super().__init__(
            placeholder=f"Pick exactly {num_choices} skill{'s' if num_choices != 1 else ''}...",
            options=options, min_values=num_choices, max_values=num_choices
        )
        self.on_pick = on_pick

    async def callback(self, interaction: discord.Interaction):
        await self.on_pick(interaction, self.values)


class SkillPickView(discord.ui.View):
    def __init__(self, on_pick, skill_list, num_choices):
        super().__init__(timeout=180)
        self.add_item(SkillMultiSelect(on_pick, skill_list, num_choices))


class WeaponSelect(discord.ui.Select):
    def __init__(self, on_pick, weapon_options):
        options = [
            discord.SelectOption(label=f"{w} ({WEAPONS[w]['dice']} {WEAPONS[w]['damage_type']})", value=w)
            for w in weapon_options
        ]
        super().__init__(placeholder="Choose your starting weapon...", options=options)
        self.on_pick = on_pick

    async def callback(self, interaction: discord.Interaction):
        await self.on_pick(interaction, self.values[0])


class WeaponPickView(discord.ui.View):
    def __init__(self, on_pick, weapon_options):
        super().__init__(timeout=180)
        self.add_item(WeaponSelect(on_pick, weapon_options))


class ArmorSelect(discord.ui.Select):
    def __init__(self, on_pick, armor_options):
        options = [discord.SelectOption(label=a, value=a) for a in armor_options]
        super().__init__(placeholder="Choose your starting armor...", options=options)
        self.on_pick = on_pick

    async def callback(self, interaction: discord.Interaction):
        await self.on_pick(interaction, self.values[0])


class ArmorPickView(discord.ui.View):
    def __init__(self, on_pick, armor_options):
        super().__init__(timeout=180)
        self.add_item(ArmorSelect(on_pick, armor_options))


class ShieldButton(discord.ui.Button):
    def __init__(self, label, wants_shield, on_pick):
        super().__init__(label=label, style=discord.ButtonStyle.secondary)
        self.wants_shield = wants_shield
        self.on_pick = on_pick

    async def callback(self, interaction: discord.Interaction):
        await self.on_pick(interaction, self.wants_shield)


class ShieldView(discord.ui.View):
    def __init__(self, on_pick):
        super().__init__(timeout=180)
        self.add_item(ShieldButton("Yes, take a shield (+2 AC)", True, on_pick))
        self.add_item(ShieldButton("No shield", False, on_pick))


class SpellsModal(discord.ui.Modal, title="What spells do you know?"):
    spells_text = discord.ui.TextInput(
        label="Spells (comma or one per line)",
        style=discord.TextStyle.paragraph,
        placeholder="Fire Bolt, Mage Armor, Magic Missile",
        max_length=500,
        required=False,
    )

    def __init__(self, on_submit_callback):
        super().__init__()
        self.on_submit_callback = on_submit_callback

    async def on_submit(self, interaction: discord.Interaction):
        raw = str(self.spells_text)
        spells = [s.strip() for s in re.split(r"[,\n]", raw) if s.strip()]
        await self.on_submit_callback(interaction, spells)


class HomebrewInfoModal(discord.ui.Modal, title="Create a homebrew class"):
    name = discord.ui.TextInput(label="Class name", placeholder="e.g. Beastlord", max_length=40)

    def __init__(self, on_submit_callback):
        super().__init__()
        self.on_submit_callback = on_submit_callback

    async def on_submit(self, interaction: discord.Interaction):
        await self.on_submit_callback(interaction, str(self.name))


class HitDieSelect(discord.ui.Select):
    def __init__(self, on_pick):
        options = [discord.SelectOption(label=f"d{d}", value=str(d)) for d in [6, 8, 10, 12]]
        super().__init__(placeholder="Choose a hit die (how much HP per level)...", options=options)
        self.on_pick = on_pick

    async def callback(self, interaction: discord.Interaction):
        await self.on_pick(interaction, int(self.values[0]))


class HitDieView(discord.ui.View):
    def __init__(self, on_pick):
        super().__init__(timeout=180)
        self.add_item(HitDieSelect(on_pick))


class SavesSelect(discord.ui.Select):
    def __init__(self, on_pick, placeholder="Pick exactly 2 saving throw proficiencies..."):
        options = [discord.SelectOption(label=a) for a in ABILITIES]
        super().__init__(placeholder=placeholder, options=options, min_values=2, max_values=2)
        self.on_pick = on_pick

    async def callback(self, interaction: discord.Interaction):
        await self.on_pick(interaction, self.values)


class SavesView(discord.ui.View):
    def __init__(self, on_pick, placeholder="Pick exactly 2 saving throw proficiencies..."):
        super().__init__(timeout=180)
        self.add_item(SavesSelect(on_pick, placeholder))


class HomebrewFeaturesModal(discord.ui.Modal, title="Describe your class's features"):
    features_text = discord.ui.TextInput(
        label="Features (one per line)",
        style=discord.TextStyle.paragraph,
        placeholder="Wild Shape: transform into a beast once per rest\nKeen Senses: advantage on Perception checks",
        max_length=800,
        required=False,
    )

    def __init__(self, on_submit_callback):
        super().__init__()
        self.on_submit_callback = on_submit_callback

    async def on_submit(self, interaction: discord.Interaction):
        lines = [line.strip() for line in str(self.features_text).split("\n") if line.strip()]
        await self.on_submit_callback(interaction, lines)


class RaceNameModal(discord.ui.Modal, title="Name your custom race"):
    name = discord.ui.TextInput(label="Race name", placeholder="e.g. Variant Human", max_length=40)

    def __init__(self, on_submit_callback):
        super().__init__()
        self.on_submit_callback = on_submit_callback

    async def on_submit(self, interaction: discord.Interaction):
        await self.on_submit_callback(interaction, str(self.name))


class RaceTraitsModal(discord.ui.Modal, title="Describe your race's traits"):
    traits_text = discord.ui.TextInput(
        label="Traits (one per line)",
        style=discord.TextStyle.paragraph,
        placeholder="Feat: Alert (+5 initiative, can't be surprised while conscious)\nDarkvision 60 ft",
        max_length=800,
        required=False,
    )

    def __init__(self, on_submit_callback):
        super().__init__()
        self.on_submit_callback = on_submit_callback

    async def on_submit(self, interaction: discord.Interaction):
        lines = [line.strip() for line in str(self.traits_text).split("\n") if line.strip()]
        await self.on_submit_callback(interaction, lines)


class EditCategorySelect(discord.ui.Select):
    def __init__(self, on_pick):
        options = [
            discord.SelectOption(label="Name", emoji="✏️", value="name"),
            discord.SelectOption(label="Level", emoji="📊", value="level"),
            discord.SelectOption(label="Weapon", emoji="⚔️", value="weapon"),
            discord.SelectOption(label="Armor & Shield", emoji="🛡️", value="armor"),
            discord.SelectOption(label="Known Spells", emoji="✨", value="spells"),
        ]
        super().__init__(placeholder="Choose what you want to edit...", options=options)
        self.on_pick = on_pick

    async def callback(self, interaction: discord.Interaction):
        await self.on_pick(interaction, self.values[0])


class EditCategoryView(discord.ui.View):
    def __init__(self, on_pick):
        super().__init__(timeout=180)
        self.add_item(EditCategorySelect(on_pick))