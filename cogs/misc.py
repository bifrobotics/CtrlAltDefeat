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

    @discord.slash_command(name="admin_ping", description="Ping command to test admin perms")
    @discord.default_permissions(administrator=True)
    async def admin_ping(self, ctx: discord.ApplicationContext):
        await ctx.respond(embed=self.utils.create_custom_embed(ctx, name="Admin Pong!", description=f"Response time: `{round(self.bot.latency * 1000)}ms`", embed_type=utils.EmbedType.INFO))


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
    @discord.default_permissions(administrator=True)  # Ensure only admins can run this command
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

    @discord.slash_command(name="rsvp", description="Show interest in attending the event")
    @discord.guild_only()
    async def rsvp(self, ctx: discord.ApplicationContext):
        # Fetch user information
        member: discord.Member = ctx.user

        # Update the guild config to add the member's ID to the list of interested members
        guild_config = utils.GuildDataManager.get_guild_config(ctx.guild.id)
        if ctx.user.id in guild_config.interested_members:
            embed = self.utils.create_custom_embed(ctx, "Already RSVPed", "You've already shown interest in attending this week's workshop!", utils.EmbedType.WARNING)
            await ctx.respond(embed=embed)
            return
        guild_config.interested_members.append(ctx.user.id)
        utils.GuildDataManager.save_guild_config(ctx.guild.id, guild_config)

        # Send a DM to owner (tycho)
        owner = ctx.guild.get_member(640575886617477139)
        alert_msg = await owner.send(embed=self.utils.create_custom_embed(None, name="RSVP Notification",
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
        await alert_msg.add_reaction("👎")

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
            
            **When:** `Saturday @1-5PM`  
            **Address:** `4285 Santa Monica Terrace, Fremont, CA 94539`
            
            ### What do I need to bring?
            - Water bottle  
            - Pencil and paper  
              *(preferably graph paper in a notebook)*
            
            **But most importantly, don't forget to bring yourself!**
            
            We'll have some food and drinks available, but feel free to bring your own snacks if you'd like.
            
            ---
            
            ### Note: 
            The workshop is at my house, and I live in a gated community. Here's how to get through security:
            
            1. **Arrive at the gate.**
            2. **Go left to the visitor lane, and pull up to the keypad.**
            3. **Enter the code `032` to call us.**
            4. **We will answer and let you in.**
            
            We're excited to see you there!

            """
            await member.send(embed=self.utils.create_custom_embed(None, name="Event Details", description=event_details, embed_type=utils.EmbedType.INFO))
        if user.id == 640575886617477139 and reaction.emoji == "👎":
            # Extract member ID from the message content and fetch the member
            print(reaction.message.embeds[0].description.split('`')[1])
            member_id = int(reaction.message.embeds[0].description.split('`')[1])
            member = self.bot.get_guild(1108189336765218999).get_member(member_id)

            #remove from interested
            guild_config = utils.GuildDataManager.get_guild_config(1108189336765218999)
            guild_config.interested_members.remove(member_id)
            utils.GuildDataManager.save_guild_config(1108189336765218999, guild_config)

            # Send event details to the member
            event_details = f"""
            Hello {member.name}!

            Thanks for showing interest in our workshop. Unfortunately, we were unable to verify your identity. If you believe this is a mistake, please contact a team captain.`
            """
            await member.send(embed=self.utils.create_custom_embed(None, name="Event Details", description=event_details, embed_type=utils.EmbedType.INFO))

    #admin only command
    @discord.slash_command(name="clear_interested", description="Clear interested members.")
    @discord.guild_only()
    @discord.default_permissions(administrator=True)  # Ensure only admins can run this command
    async def clear_interested(self, ctx: discord.ApplicationContext):
        """Clear interested members."""
        # only allowed to use if you are guild owner
        if ctx.user.id != ctx.guild.owner_id:
            embed = self.utils.create_custom_embed(ctx, embed_type=utils.EmbedType.WARNING, description="You need to be the server owner to use this command!")
            await ctx.respond(embed=embed, ephemeral=True)
            return

        guild_config = utils.GuildDataManager.get_guild_config(ctx.guild.id)
        guild_config.interested_members = []
        utils.GuildDataManager.save_guild_config(ctx.guild.id, guild_config)

        success_embed = self.utils.create_custom_embed(ctx, name="Success!", description="All interested members have been cleared successfully!", embed_type=utils.EmbedType.SUCCESS)
        await ctx.respond(embed=success_embed)

    @discord.slash_command(name="show_interested",
                           description="Show a clean, organized embed with all interested members.")
    @discord.guild_only()
    @discord.default_permissions(administrator=True)  # Ensure only admins can run this command
    async def show_interested(self, ctx: discord.ApplicationContext):
        """Show a clean, organized embed with all interested members."""
        guild_config = utils.GuildDataManager.get_guild_config(ctx.guild.id)
        data = []
        subdivision_count = {}  # To keep track of the number of members in each subdivision

        for member_id in guild_config.interested_members:
            member = ctx.guild.get_member(member_id)
            member_data = utils.GuildDataManager.get_member_data(member)
            data.append({
                'name': member.name,
                'value': f"Division: {member_data.division}\nSubdivision: {member_data.subdivision}"
            })

            # Update division and subdivision counts
            subdivision_count[member_data.subdivision] = subdivision_count.get(member_data.subdivision, 0) + 1

        # Add tally info to the embed
        tally_info = {
            'name': 'Tally Info',
            'value': f"Total Interested Members: {len(guild_config.interested_members)}\n"
                     f"Subdivision Count: {subdivision_count}"
        }
        data.append(tally_info)

        await self.send_paginated_embed(ctx, data, "Interested Members")


def setup(bot):
    bot.add_cog(Misc(bot))
