import discord
from discord.ext import commands
from discord.ui import Button, View

from utils import GuildDataManager, Utils, EmbedType, Subdivision


class GuildConfigCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.utils = Utils(bot)

    @discord.slash_command(name="configure", description="Configure GuildData role mappings.")
    @discord.default_permissions(administrator=True)
    @discord.guild_only()
    async def configure(self, ctx: discord.ApplicationContext):
        if not ctx.user.guild_permissions.administrator:
            embed = self.utils.create_custom_embed(ctx, embed_type=EmbedType.WARNING, description="You need to be a server admin to use this command!")
            await ctx.respond(embed=embed, ephemeral=True)
            return
        embed = self.utils.create_custom_embed(ctx, embed_type=EmbedType.INFO, description="Choose a division to map a role:")
        await ctx.respond(embed=embed, view=DivisionView())

class DivisionButton(discord.ui.Button):
    def __init__(self, division: Subdivision):
        super().__init__(
            label=str(division),
            custom_id=division.value,
            style=discord.ButtonStyle.blurple
        )

    async def callback(self, interaction: discord.Interaction):
        from bot_singleton import bot
        embed = Utils.create_custom_embed(interaction, embed_type=EmbedType.INFO, title=":gear: Role Configuration", description=f"Please mention the role you want to map to {self.label}.")
        await interaction.response.send_message(embed=embed, ephemeral=True)

        # Wait for the admin to mention a role
        msg = await bot.wait_for('message', check=lambda m: len(m.role_mentions) > 0 and m.author == interaction.user)
        role = msg.role_mentions[0]
        await msg.delete()

        # Save the mapping to GuildConfig
        config = GuildDataManager.get_guild_config(interaction.guild.id)
        config.subdivision_to_role[self.label] = role.id
        GuildDataManager.save_guild_config(interaction.guild.id, config)

        embed = Utils.create_custom_embed(interaction, embed_type=EmbedType.SUCCESS, title=":white_check_mark: Success!", description=f"Mapped `{self.label}` to <@&{role.id}>!")
        await interaction.followup.send(embed=embed)


class DivisionView(View):
    def __init__(self):
        super().__init__()
        for division in Subdivision:
            self.add_item(DivisionButton(division))

    async def on_timeout(self):
        self.disable_all_items()
        await self.message.edit(content="*View timeout! Run `/configure` again to see this view!", view=self)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.guild_permissions.administrator




def setup(bot):
    bot.add_cog(GuildConfigCog(bot))
