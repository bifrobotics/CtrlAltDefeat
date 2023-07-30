from datetime import datetime

import discord
from discord.ext import commands, pages

import utils


class Misc(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.utils = utils.Utils(bot)

    @discord.slash_command(name="ping", description="Get the response time of the bot")
    async def ping(self, ctx: discord.ApplicationContext):
        await ctx.respond(embed=self.utils.create_custom_embed(ctx, name="Pong!", description=f"Response time: `{round(self.bot.latency * 1000)}ms`", embed_type=utils.EmbedType.INFO))



    async def _user_autocomplete(self, ctx: discord.ApplicationContext, value: str):
        members = ctx.guild.members
        return [discord.OptionData(name=member.display_name, value=member.id) for member in members if
                value.lower() in member.display_name.lower() and not member.bot]

    async def _subdivision_autocomplete(self, ctx: discord.ApplicationContext, value: discord.Role):
        divisions = [ctx.guild.get_role(id) for id in utils.GuildDataManager.get_guild_config(ctx.guild_id).subdivision_to_role.values()]
        return [discord.OptionChoice(name=division, value=division) for division in divisions if
                value in division]

    # ... [rest of your code]

    async def send_paginated_embed(self, ctx, data, title):
        """Send paginated embeds using Pycord's Paginator."""
        # Convert the data into a list of embeds
        embeds = []
        embed = discord.Embed(title=title, color=0x00ff00)

        for item in data:
            if len(embed.fields) == 25:  # Max fields per embed is 25
                embeds.append(embed)
                embed = discord.Embed(title=title, color=0x00ff00)
            embed.add_field(name=item['name'], value=item['value'], inline=True)
        if len(embed.fields) > 0:
            embeds.append(embed)

        # Create the paginator
        paginator = pages.Paginator(pages=embeds, loop_pages=True)

        # Send the paginator
        await paginator.respond(ctx.interaction)

    @discord.slash_command(name="display_user_data", description="Displays user data in an embed.")
    @commands.has_permissions(administrator=True)  # Ensure only admins can run this command
    @discord.option(name="user", description="Select a user", autocomplete=True)
    @discord.option(name="division", description="Select a division", autocomplete=_subdivision_autocomplete)
    async def display_user_data(self, ctx: discord.ApplicationContext, user: discord.Member = None,
                                division: discord.Role = None):
        """Displays user data in an embed based on the provided options."""

        subdivision_to_role = utils.GuildDataManager.get_guild_config(ctx.guild_id).subdivision_to_role

        if user:  # Display data for a specific user
            member_data = utils.GuildDataManager.get_member_data(user)
            subdivision_role = subdivision_to_role.get(member_data.subdivision._display_name)
            embed = discord.Embed(title=f"Data for {user.name}", color=0x00ff00)
            embed.add_field(name="Division", value=member_data.division, inline=True)
            if member_data.subdivision:
                embed.add_field(name="Subdivision", value=f"<@&{subdivision_role}>" if member_data.subdivision is not utils.Subdivision.NONE else "None", inline=True)
            await ctx.respond(embed=embed)

        elif division:  # Display data for all users of a specific division
            embed = discord.Embed(title=f"Users in {division} Division", color=0x00ff00)
            for member in ctx.guild.members:
                member_data = utils.GuildDataManager.get_member_data(member)
                subdivision_role = subdivision_to_role.get(member_data.subdivision._display_name)
                if member_data.division == division:
                    embed.add_field(name=member.name, value=f"Subdivision: {f'<@&{subdivision_role}>' if member_data.subdivision is not utils.Subdivision.NONE else 'None'}", inline=True)
            await ctx.respond(embed=embed)
        else:  # Display data for all users
            def get_subdivision_order(member):

                member_data = utils.GuildDataManager.get_member_data(member)
                subdivision_str = member_data.subdivision._display_name
                # If the subdivision is a role mention, return a high value to sort it last
                if subdivision_str.startswith('<@&') and subdivision_str.endswith('>'):
                    return float('inf')
                # Otherwise, return the enum value
                return utils.Subdivision.from_display_name(subdivision_str)._value_

            data = []
            # Sort members by their subdivisions
            sorted_members = sorted(list(filter(lambda x: not x.bot, ctx.guild.members)), key=get_subdivision_order)

            for member in sorted_members:
                if member.bot:
                    continue
                member_data = utils.GuildDataManager.get_member_data(member)
                subdivision_role = subdivision_to_role.get(member_data.subdivision._display_name)
                data.append({
                    'name': member.name,
                    'value': f"Division: {member_data.division}\nSubdivision: {f'<@&{subdivision_role}>' if member_data.subdivision is not utils.Subdivision.NONE else 'None'}"
                })
            await self.send_paginated_embed(ctx, data, "All Users Data")


    @discord.slash_command(name="save_member_roles", description="Searches for every member's roles and saves their data.")
    @commands.has_permissions(administrator=True)  # Ensure only admins can run this command
    async def save_member_roles(self, ctx: discord.ApplicationContext):
        """Searches for every member's roles and saves their data."""
        for member in ctx.guild.members:
            if member.bot:
                continue
            print(f"Saving roles for {member.name}...")
            subdivision = utils.GuildDataManager.identify_member_subdivision(member)
            member_data = utils.MemberData(division=subdivision._division,
                                           subdivision=subdivision)
            utils.GuildDataManager.save_member_data(member.id, member_data)

        success_embed = self.utils.create_custom_embed(ctx, name="Success!", description="All member roles have been saved successfully!", embed_type=utils.EmbedType.SUCCESS)
        await ctx.respond(embed=success_embed)

    @discord.slash_command(name="interested", description="Show interest in attending the event")
    @discord.guild_only()
    async def interested(self, ctx: discord.ApplicationContext):
        # Fetch user information
        member: discord.Member = ctx.user

        # Update the guild config to add the member's ID to the list of interested members
        guild_config = utils.GuildDataManager.get_guild_config(ctx.guild.id)
        if ctx.user.id in guild_config.interested_members:
            embed = self.utils.create_custom_embed(ctx, "Already Interested", "You've already shown interest in attending the event!", utils.EmbedType.WARNING)
            await ctx.respond(embed=embed)
            return
        guild_config.interested_members.append(ctx.user.id)
        utils.GuildDataManager.save_guild_config(ctx.guild.id, guild_config)

        # Send a DM to owner (tycho)
        owner = ctx.guild.get_member(640575886617477139)
        alert_msg = await owner.send(embed=self.utils.create_custom_embed(None, name="Interest Notification",
                                                                          description=f"{member.name}#{member.discriminator} (`{member.id}`) has shown interest in attending the event!",
                                                                          embed_type=utils.EmbedType.NEUTRAL,
                                                                          fields={
                                                                              "Division": utils.GuildDataManager.get_member_data(
                                                                                  member).division,
                                                                              "Subdivision": str(
                                                                                  utils.GuildDataManager.get_member_data(
                                                                                      member).subdivision),
                                                                              "Time": datetime.now().strftime(
                                                                                  "%m/%d/%Y, %H:%M:%S"),
                                                                              "Nick:": member.nick
                                                                          }))
        # Add a reaction to the message
        await alert_msg.add_reaction("👍")

        # Send a response to the user
        await ctx.respond(embed=self.utils.create_custom_embed(ctx, name="Interest Registered!",
                                                               description="Your interest has been registered. You'll receive event details soon after verification.",
                                                               embed_type=utils.EmbedType.SUCCESS))

    # Add a listener to check for your manual verification (e.g., reacting with a thumbs up emoji to the DM)
    @commands.Cog.listener()
    async def on_reaction_add(self, reaction: discord.Reaction, user):
        if user.id == 640575886617477139 and reaction.emoji == "👍":
            # Extract member ID from the message content and fetch the member
            print(reaction.message.embeds[0].description.split('`')[1])
            member_id = int(reaction.message.embeds[0].description.split('`')[1])
            member = self.bot.get_guild(1108189336765218999).get_member(member_id)

            # Send event details to the member
            event_details = f"""
            Hello {member.name}!

            Thanks for showing interest in our workshop. Here are the event details:

            When: `Monday @1PM`
            Address: `4285 Santa Monica Terrace, Fremont, CA 94539`
            
            *What do I need to bring?*
            - Water bottle
            
            - Design: Pencil and paper. (preferably graph paper)
            - Mechanical: None 
            - Electrical: None
            - Programming: Bring your laptop and charger. We'll be using Java and IntelliJ IDEA, so make sure you have those installed.
            
            *Psst! Design and Mechanical, bring any household materials you think you might need to protect a 10 foot egg drop!*
            
            **But most importantly, don't forget to bring yourself!**
            
            *Note: The workshop is at my house, and I live in a gated community which means that you will have to get through security. Here are the steps to do so.*
            
            **Step 1:** Arrive at the gate.
            **Step 2:** Go left to the visitor lane, and pull up to the keypad.
            **Step 3:** The code to call is 032. Enter it, and it will call us.
            **Step 4:** We will answer, and let you in.

            We're excited to see you there!
            """
            await member.send(embed=self.utils.create_custom_embed(None, name="Event Details", description=event_details, embed_type=utils.EmbedType.INFO))


def setup(bot):
    bot.add_cog(Misc(bot))
