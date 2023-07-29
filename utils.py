import datetime
import enum
import json
import os
from dataclasses import dataclass, asdict

import discord


class EmbedData:
    def __init__(self, color, title=None, description=None, thumbnail_url=None,
                 image_url=None, fields=None, footer_text=None, footer_icon=None,
                 author_name=None, author_icon=None):
        self.color = color
        self.title = title
        self.description = description
        self.thumbnail_url = thumbnail_url
        self.image_url = image_url
        self.fields = fields
        self.footer_text = footer_text
        self.footer_icon = footer_icon
        self.author_name = author_name
        self.author_icon = author_icon



class EmbedType(enum.Enum):
    SUCCESS = EmbedData(
        color=discord.Color.green(),
        title=":white_check_mark: Success! :white_check_mark:",
        description="The operation was successful.",
        footer_text="Powered by Ctrl+Alt+Defeat",
        footer_icon="https://cdn.discordapp.com/attachments/1126591811016740894/1134181700885287002/DALLE_2023-07-25_18.45.42_-_Background__Digital_circuitry_in_cool_blues_and_metallic_grays._Center__Detailed_robotic_claw_hovering_over_three_symbolized_buttons._First__Joystick_.png"
    )
    ERROR = EmbedData(
        color=discord.Color.red(),
        title=":x: Error! :x:",
        description="An error occurred during the operation.",
        footer_text="Powered by CtrlAltDefeat",
        footer_icon="https://cdn.discordapp.com/attachments/1126591811016740894/1134181700885287002/DALLE_2023-07-25_18.45.42_-_Background__Digital_circuitry_in_cool_blues_and_metallic_grays._Center__Detailed_robotic_claw_hovering_over_three_symbolized_buttons._First__Joystick_.png"
    )
    WARNING = EmbedData(
        color=discord.Color.orange(),
        title=":warning: Warning! :warning:",
        description="There's something you should be aware of.",
        footer_text="Powered by CtrlAltDefeat",
        footer_icon="https://cdn.discordapp.com/attachments/1126591811016740894/1134181700885287002/DALLE_2023-07-25_18.45.42_-_Background__Digital_circuitry_in_cool_blues_and_metallic_grays._Center__Detailed_robotic_claw_hovering_over_three_symbolized_buttons._First__Joystick_.png"
    )

    NEUTRAL = EmbedData(
        color=discord.Color.blurple(),
        title=":information_source: Notice :information_source:",
        description="Here's some information for you.",
        footer_text="Powered by CtrlAltDefeat",
        footer_icon="https://cdn.discordapp.com/attachments/1126591811016740894/1134181700885287002/DALLE_2023-07-25_18.45.42_-_Background__Digital_circuitry_in_cool_blues_and_metallic_grays._Center__Detailed_robotic_claw_hovering_over_three_symbolized_buttons._First__Joystick_.png"
    )

    INFO = EmbedData(
        color=discord.Color.blue(),
        title=":blue_book: Info",
        description="Here's the detailed information you requested.",
        footer_text="Powered by CtrlAltDefeat",
        footer_icon="https://cdn.discordapp.com/attachments/1126591811016740894/1134181700885287002/DALLE_2023-07-25_18.45.42_-_Background__Digital_circuitry_in_cool_blues_and_metallic_grays._Center__Detailed_robotic_claw_hovering_over_three_symbolized_buttons._First__Joystick_.png"
    )


class Utils:
    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    def create_custom_embed(ctx: discord.ApplicationContext, name=None, description=None, embed_type: EmbedType=None,
                            fields: dict = {}, **kwargs):
        # Convert embed_type to EmbedData instance if it's an Enum value
        if isinstance(embed_type, enum.Enum):
            embed_type = embed_type.value

        embed = discord.Embed()

        if isinstance(embed_type, EmbedData):
            embed.color = embed_type.color
            if embed_type.title:
                embed.title = embed_type.title
            if embed_type.description:
                embed.description = embed_type.description
            if embed_type.thumbnail_url:
                embed.set_thumbnail(url=embed_type.thumbnail_url)
            if embed_type.image_url:
                embed.set_image(url=embed_type.image_url)
            if embed_type.fields:
                for field in embed_type.fields:
                    embed.add_field(name=field.name, value=field.value, inline=field.inline)
            if embed_type.footer_text:
                embed.set_footer(text=embed_type.footer_text, icon_url=embed_type.footer_icon)
            if embed_type.author_name:
                embed.set_author(name=embed_type.author_name, icon_url=embed_type.author_icon)

        if name:
            embed.title = name

        if description:
            embed.description = description

        for name, value in fields.items():
            embed.add_field(name=name, value=value, inline=False)

        # Handle any additional keyword arguments (kwargs) to add more customization
        for key, value in kwargs.items():
            setattr(embed, key, value)

        # Optionally, you can add a footer with your bot information.
        embed.set_footer(text=f"Powered by CtrlAltDefeat", icon_url="https://cdn.discordapp.com/attachments/1126591811016740894/1134181700885287002/DALLE_2023-07-25_18.45.42_-_Background__Digital_circuitry_in_cool_blues_and_metallic_grays._Center__Detailed_robotic_claw_hovering_over_three_symbolized_buttons._First__Joystick_.png")
        embed.timestamp = datetime.datetime.now()

        return embed

class Subdivision(enum.Enum):
    DESIGN = "DSN", "Design Division", "Robotics"
    MECHANICAL = "MCH", "Mechanical Division", "Robotics"
    ELECTRICAL = "ELC", "Electrical Division", "Robotics"
    PROGRAMMING = "PRO", "Programming Division", "Robotics"
    BUSINESS = "BSN", "Business Division", "Logistics"
    MEDIA = "MDA", "Media Division", "Logistics"
    STRATEGY = "STR", "Strategy Division", "Logistics"
    OUTREACH = "OUTR", "Outreach Division", "Logistics"
    NONE = 'SPEC', "Nullified Division", "Sadness :("

    def __new__(cls, value, display_name, division):
        obj = object.__new__(cls)
        obj._value_ = value
        obj._display_name = display_name
        obj._division = division
        return obj

    def __str__(self):
        return self._display_name

    @classmethod
    def from_display_name(cls, display_name):
        for division in cls:
            if division._display_name == display_name:
                return division
        raise ValueError("Invalid display name for Division")


@dataclass
class MemberData:
    division: str
    subdivision: Subdivision


@dataclass
class GuildConfig:
    subdivision_to_role: dict[str, int]


class GuildDataManager:
    MEMBER_DATA_DIR = "member_data"
    GUILD_CONFIG_DIR = "guild_config"

    @classmethod
    def _get_member_file_path(cls, member_id: int) -> str:
        return os.path.join(cls.MEMBER_DATA_DIR, f"{member_id}.json")

    @classmethod
    def save_member_data(cls, member_id: int, member_data: MemberData) -> None:
        file_path = cls._get_member_file_path(member_id)
        os.makedirs(cls.MEMBER_DATA_DIR, exist_ok=True)
        # prepare for serialization
        data = asdict(member_data)
        data['subdivision'] = member_data.subdivision.name
        with open(file_path, "w") as f:
            json.dump(data, f)

    @classmethod
    def _load_member_data(cls, member_id: int) -> MemberData:
        file_path = cls._get_member_file_path(member_id)
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                data = json.load(f)
                data['subdivision'] = Subdivision.__getitem__(data['subdivision'])
                return MemberData(**data)
        else:
            None

    @classmethod
    def get_member_data(cls, member: discord.Member) -> MemberData:
        if member.bot:
            raise ValueError("Bad Argument: Members with data cannot be bots")
        member_data = cls._load_member_data(member.id)
        if member_data is None:
            subdivision = GuildDataManager.identify_member_subdivision(member)
            member_data = MemberData(division=subdivision._division, subdivision=subdivision)
            cls.save_member_data(member.id, member_data)
        return member_data

    @classmethod
    def identify_member_subdivision(cls, member: discord.Member) -> Subdivision:
        # Identify a member's subdivision based on their roles
        for role in member.roles:
            subdivision_to_role = cls.get_guild_config(member.guild.id).subdivision_to_role
            for subdivision, role_id in subdivision_to_role.items():
                if role.id == role_id:
                    return Subdivision.from_display_name(subdivision)
        return Subdivision.NONE

    @classmethod
    def delete_member_data(cls, member_id: int) -> None:
        file_path = cls._get_member_file_path(member_id)
        if os.path.exists(file_path):
            os.remove(file_path)

    @classmethod
    def _get_guild_file_path(cls, guild_id: int) -> str:
        return os.path.join(cls.GUILD_CONFIG_DIR, f"{guild_id}.json")

    @classmethod
    def save_guild_config(cls, guild_id: int, config_data: GuildConfig) -> None:
        file_path = cls._get_guild_file_path(guild_id)
        os.makedirs(cls.GUILD_CONFIG_DIR, exist_ok=True)
        with open(file_path, "w") as f:
            json.dump(asdict(config_data), f)

    @classmethod
    def load_guild_config(cls, guild_id: int) -> GuildConfig:
        file_path = cls._get_guild_file_path(guild_id)
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                data = json.load(f)
                return GuildConfig(**data)
        else:
            return None

    @classmethod
    def get_guild_config(cls, guild_id: int) -> GuildConfig:
        config = cls.load_guild_config(guild_id)
        if config is None:
            config = GuildConfig(subdivision_to_role={})
            cls.save_guild_config(guild_id, config)
        return config

    @classmethod
    def delete_guild_config(cls, guild_id: int) -> None:
        file_path = cls._get_guild_file_path(guild_id)
        if os.path.exists(file_path):
            os.remove(file_path)


