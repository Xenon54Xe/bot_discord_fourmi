import discord
from discord.ext import commands

from bot_discord_fourmi.BDD.database_handler import DatabaseHandler
from bot_discord_fourmi import functions as fc


def setup(bot):
    bot.add_cog(MemberCommands(bot))
    print("Loading MembersCommands...")


class MemberCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.database_handler = DatabaseHandler("database.db")
        self.functions = fc.Function()

    @commands.command()
    async def suggest(self, ctx, *, suggestion: str):
        guild = ctx.guild
        guild_id = guild.id

        suggestion_db = self.database_handler.get_guild(guild_id)["suggestion"]
        suggestion_list = self.functions.str_to_list(suggestion_db)

        suggestion_list.append(suggestion)
        suggestion_str = self.functions.list_to_str(suggestion_list)
        self.database_handler.set_suggestion(guild_id, suggestion_str)

        await ctx.send("Suggestion envoyée")

    @commands.command()
    async def setChoice(self, ctx, *, choice: str):
        guild = ctx.guild
        guild_id = guild.id

        members = ctx.message.mentions

        for member in members:
            text = f"<@{member.id}>"
            choice = choice.replace(text, "")

        while len(self.functions.find(choice, "  ")) > 0:
            choice = choice.replace("  ", " ")

        while choice.startswith(" "):
            choice = choice[1:]

        while choice.endswith(" "):
            choice = choice[:-1]

        if choice in self.functions.list_none:
            choice = None

        if len(members) > 0:
            if not self.functions.is_data_manager(ctx):
                await ctx.send("Vous n'avez pas les permissions pour modifier les choix de quelqu'un d'autre.")
                return
            for member in members:
                user_id = member.id
                self.database_handler.set_choice(user_id, guild_id, choice)
            await ctx.send("Choix des membres mis à jour.")
            return

        self.database_handler.set_choice(ctx.author.id, guild_id, choice)

        await ctx.send("Choix mis à jour.")

    @commands.command()
    async def setAvailability(self, ctx, *, arg: str):
        guild = ctx.guild
        guild_id = guild.id

        members = ctx.message.mentions
        print(members)

        for member in members:
            text = f"<@{member.id}>"
            arg = arg.replace(text, "")

        while len(self.functions.find(arg, "  ")) > 0:
            arg = arg.replace("  ", " ")

        while arg.startswith(" "):
            arg = arg[1:]

        while arg.endswith(" "):
            arg = arg[:-1]

        if arg in self.functions.list_none:
            arg = None

        if len(members) > 0:
            if not self.functions.is_data_manager(ctx):
                await ctx.send("Vous n'avez pas les permissions pour modifier les disponibilités de quelqu'un d'autre.")
                return
            for member in members:
                user_id = member.id
                self.database_handler.set_availability(user_id, guild_id, arg)
            await ctx.send("Disponibilités des membres mis à jour.")
            return

        self.database_handler.set_availability(ctx.author.id, guild_id, arg)

        await ctx.send("Disponibilités mis à jour.")

    @commands.command()
    async def setSpeciality(self, ctx, *, arg: str):
        guild = ctx.guild
        guild_id = guild.id

        members = ctx.message.mentions

        for member in members:
            text = f"<@{member.id}>"
            arg = arg.replace(text, "")

        while len(self.functions.find(arg, "  ")) > 0:
            arg = arg.replace("  ", " ")

        while arg.startswith(" "):
            arg = arg[1:]

        while arg.endswith(" "):
            arg = arg[:-1]

        if not arg in self.functions.list_none + ["cac", "vel", "tir"]:
            await ctx.send("Vous devez choisir entre __cac__, __vel__, __tir__ et __null__.")
            return
        if arg in self.functions.list_none:
            arg = None

        if len(members) > 0:
            if not self.functions.is_data_manager(ctx):
                await ctx.send("Vous n'avez pas les permissions pour modifier les spécialités de quelqu'un d'autre.")
                return
            for member in members:
                user_id = member.id
                self.database_handler.set_speciality(user_id, guild_id, arg)
            await ctx.send("Spécialités des membres mis à jour.")
            return

        self.database_handler.set_speciality(ctx.author.id, guild_id, arg)

        await ctx.send("Spécialités mis à jour.")

    @commands.command()
    async def setAd(self, ctx, title, desc, name, *, value):
        guild = ctx.guild
        guild_id = guild.id

        member = ctx.author
        member_id = member.id

        ad_value_max = 1
        member_roles = member.roles

        for role in member_roles:
            role_id = role.id

            try:
                role_ad_value = self.database_handler.get_role(role_id, guild_id)["adValue"]
            except:continue

            if role_ad_value > ad_value_max:
                ad_value_max = role_ad_value

        user_ad = self.database_handler.get_user(member_id, guild_id)["ad"]
        user_ad_list = self.functions.str_to_list(user_ad)

        if len(user_ad_list) < ad_value_max:
            embed = discord.Embed(title=title, description=desc, colour=834)
            embed.set_author(name=member.name, icon_url=member.avatar_url)
            embed.add_field(name=name, value=value)
        else:
            await ctx.send(f"Vous avez {len(user_ad_list)} annonces et vos rôle ne vous permettent pas d'en créer "
                           f"d'autres, si vous voulez en créer une nouvelle commencez par supprimer une ancienne avec "
                           f"la commande -delAd <id>.")
            return

        ad_channel = guild.get_channel(self.database_handler.get_guild(guild_id)["adChannelId"])
        if ad_channel is None:
            ad_channel = guild.text_channels[0]

        msg = await ad_channel.send(embed=embed)

        user_ad_list.append(msg.id)
        user_ad_str = self.functions.list_to_str(user_ad_list)

        self.database_handler.set_ad(member_id, guild_id, user_ad_str)

        await ctx.send("Annonce envoyée.")

    @commands.command()
    async def getAd(self, ctx):
        guild = ctx.guild
        guild_id = guild.id

        member = ctx.author
        member_id = member.id

        user_ad = self.database_handler.get_user(member_id, guild_id)["ad"]
        user_ad_list = self.functions.str_to_list(user_ad)

        if len(user_ad_list) == 0:
            await ctx.send("Vous n'avez pas d'annonces.")
            return

        channel_ad = guild.get_channel(self.database_handler.get_guild(guild_id)["adChannelId"])
        if channel_ad is None:
            channel_ad = guild.text_channels[0]

        ad_to_remove = []
        for ad_id in user_ad_list:
            try:
                msg = await channel_ad.fetch_message(ad_id)
            except discord.NotFound:
                ad_to_remove.append(ad_id)
                continue
            await ctx.send(content=f"**Message ID : {msg.id}**", embed=msg.embeds[0])

        for ad_id in ad_to_remove:
            user_ad_list.remove(ad_id)

        if len(user_ad_list) == 0:
            await ctx.send("Vous n'avez pas d'annonces correctes.")

        user_ad_str = self.functions.list_to_str(user_ad_list)
        self.database_handler.set_ad(member_id, guild_id, user_ad_str)

    @commands.command()
    async def delAd(self, ctx, arg):
        guild = ctx.guild
        guild_id = guild.id

        member = ctx.author
        member_id = member.id

        channel_ad = guild.get_channel(self.database_handler.get_guild(guild_id)["adChannelId"])
        if channel_ad is None:
            channel_ad = guild.text_channels[0]

        user_ad = self.database_handler.get_user(member_id, guild_id)["ad"]
        user_ad_list = self.functions.str_to_list(user_ad)

        arg = self.functions.reformat_type(arg)

        if arg in self.functions.list_all:
            for ad_id in user_ad_list:
                msg = await channel_ad.fetch_message(ad_id)
                await msg.delete()
            user_ad_list.clear()
            await ctx.send("Annonces supprimées.")

        elif isinstance(arg, int):
            try:
                msg = await channel_ad.fetch_message(arg)
            except:
                await ctx.send(f"L'annonce avec l'id __'{arg}'__ n'a pas été trouvé.")
                return

            user_ad_list.remove(msg.id)

            await msg.delete()
            await ctx.send("Annonce supprimée.")
        else:
            await ctx.send(f"L'id que vous avez envoyé : __'{arg}'__ n'est pas un nombre entier.")

        user_ad_str = self.functions.list_to_str(user_ad_list)
        self.database_handler.set_ad(member_id, guild_id, user_ad_str)

    @commands.command()
    async def getRoleMovable(self, ctx):
        guild = ctx.guild
        guild_id = guild.id

        roles = self.database_handler.get_all_roles(guild_id)

        say = f"Les rôles attribuables sont :\n"
        count = 0
        for role in roles:
            role_id = role["roleId"]
            movable = role["isMovable"]
            if movable:
                role_guild = guild.get_role(role_id)
                say += f"**``{role_guild.name}``**\n"
                count += 1
        if count == 0:
            await ctx.send("Il n'y a pas de rôle attribuables.")
            return
        await ctx.send(say)

    @commands.command()
    async def addRole(self, ctx, arg: str = None):
        guild = ctx.guild
        guild_id = guild.id

        member = ctx.author

        if arg in self.functions.list_all:
            roles = []
            roles_db = self.database_handler.get_all_roles(guild_id)
            for role_db in roles_db:
                if role_db["isMovable"]:
                    role = guild.get_role(role_db["roleId"])
                    roles.append(role)
            if len(roles) == 0:
                await ctx.send("Vous n'avez pas la permission de vous donner les rôles de ce serveur.")
        else:
            roles = ctx.message.role_mentions
            if len(roles) == 0:
                await ctx.send("Il manque la mention des rôles que vous voulez avoir.")
                return

        for role in roles:
            role_id = role.id
            movable = self.database_handler.get_role(role_id, guild_id)["isMovable"]
            if movable:
                await member.add_roles(role)
            else:
                await ctx.send(f"Vous n'avez pas le droit de vous donner le rôle **{role.name}**.")

        await ctx.send("Rôles mis à jour.")

    @commands.command()
    async def removeRole(self, ctx, arg: str = None):
        guild = ctx.guild
        guild_id = guild.id

        member = ctx.author

        if arg in self.functions.list_all:
            roles = []
            roles_db = self.database_handler.get_all_roles(guild_id)
            for role_db in roles_db:
                if role_db["isMovable"]:
                    role = guild.get_role(role_db["roleId"])
                    roles.append(role)
            if len(roles) == 0:
                await ctx.send("Vous n'avez pas la permission de vous enlever les rôles de ce serveur.")
        else:
            roles = ctx.message.role_mentions
            if len(roles) == 0:
                await ctx.send("Il manque la mention des rôles que vous voulez enlever.")
                return

        for role in roles:
            role_id = role.id
            movable = self.database_handler.get_role(role_id, guild_id)["isMovable"]
            if movable:
                await member.remove_roles(role)
            else:
                await ctx.send(f"Vous n'avez pas le droit de vous enlever le rôle **{role.name}**.")

        await ctx.send("Rôles mis à jour.")
