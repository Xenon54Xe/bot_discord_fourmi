import discord
from discord.ext import commands
import sys
from os import path

p = path.abspath(".")
sys.path.insert(1, p)

import BDD.database_handler as dbh
import functions as fc


def setup(bot):
    bot.add_cog(MemberCommands(bot))
    print("Loading OtherCommands...")


class MemberCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.database_handler = dbh.DatabaseHandler("database.db")
        self.functions = fc.Function()

    @commands.command()
    async def updateUser(self, ctx, arg=None):
        guild = ctx.guild
        guild_id = guild.id

        if arg in self.functions.list_all:
            users = guild.members
        else:
            users = ctx.message.mentions

        if len(users) > 0:
            for user in users:
                user_id = user.id
                username = user.display_name
                self.database_handler.create_user(user_id, guild_id, username)
            await ctx.send("Utilisateurs mis à jour.")
            return

        user = ctx.author
        user_id = user.id
        username = user.display_name
        self.database_handler.create_user(user_id, guild_id, username)
        await ctx.send("Utilisateur mis à jour.")

    @commands.command()
    async def setChoice(self, ctx, *, choice):
        guild = ctx.guild
        guild_id = guild.id

        if choice in self.functions.list_none:
            choice = None

        user_id = ctx.author.id
        self.database_handler.set_choice(user_id, guild_id, choice)
        await ctx.send("Vos choix ont étés mis à jour")

    @commands.command()
    async def setAvailability(self, ctx, *, args):
        guild = ctx.guild
        guild_id = guild.id

        if args in self.functions.list_none:
            args = None

        user_id = ctx.author.id
        self.database_handler.set_availability(user_id, guild_id, args)
        await ctx.send("Disponibilités mises à jour.")

    @commands.command()
    async def getRoleMovable(self, ctx):
        guild = ctx.guild
        guild_id = guild.id

        roles = self.database_handler.get_all_roles(guild_id)
        say = f"Les rôles attribuables sont :\n"
        for role in roles:
            role_id = role["roleId"]
            movable = role["movable"]
            if movable:
                role_guild = guild.get_role(role_id)
                say += f"**``{role_guild.name}``**\n"
        await ctx.send(say)

    @commands.command()
    async def addRole(self, ctx):
        guild = ctx.guild
        guild_id = guild.id

        member = ctx.author
        roles = ctx.message.role_mentions

        for role in roles:
            role_id = role.id
            movable = self.database_handler.get_role(role_id, guild_id)["movable"]
            if movable:
                await member.add_roles(role)
            else:
                await ctx.send(f"Le role **{role.name}** n'est pas attribuable")

        await ctx.send("Rôles mis à jour.")

    @commands.command()
    async def removeRole(self, ctx):
        guild = ctx.guild
        guild_id = guild.id

        member = ctx.author
        roles = ctx.message.role_mentions

        for role in roles:
            role_id = role.id
            movable = self.database_handler.get_role(role_id, guild_id)["movable"]
            if movable:
                await member.remove_roles(role)
            else:
                await ctx.send(f"Le role **{role.name}** n'est pas déplaçeable")

        await ctx.send("Rôles mis à jour.")

    @commands.command()
    async def getEvent(self, ctx):
        guild = ctx.guild
        guild_id = guild.id

        user = ctx.author
        channel = await user.create_dm()

        event_db = self.database_handler.get_guild(guild_id)["event"]
        event_dict = self.functions.str_to_dict(event_db, self.functions.first_splitter, self.functions.second_splitter)
        say = f"Les évenements du serveur **{guild.name}** sont :\n"
        for key in event_dict:
            event = event_dict[key]
            say += f"{event}\n"
        say = say[:-1]
        await channel.send(say)
