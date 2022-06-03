import discord
from discord.ext import commands
import sys
from os import path

p = path.abspath(".")
sys.path.insert(1, p)

import BDD.database_handler as dbh


def setup(bot):
    bot.add_cog(MemberCommands(bot))
    print("Loading OtherCommands...")


class MemberCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.database_handler = dbh.DatabaseHandler("database.db")

    @commands.command()
    async def updateUser(self, ctx):
        user_id = ctx.author.id
        guild_id = ctx.guild.id
        username = ctx.author.display_name
        self.database_handler.create_user(user_id, guild_id, username)
        await ctx.send("Utilisateur mis à jour")

    @commands.command()
    async def setChoice(self, ctx, *, choice):
        user_id = ctx.author.id
        guild_id = ctx.guild.id

        if choice in ("None", "0", "", "Null", " "):
            choice = None

        self.database_handler.set_choice(user_id, guild_id, choice)
        await ctx.send("Vos choix ont étés mis à jour")

    @commands.command()
    async def getChoice(self, ctx):
        user_id = ctx.author.id
        guild_id = ctx.guild.id
        choices = self.database_handler.get_choice(user_id, guild_id)

        if choices is None:
            say = "Vous n'avez pas fais de choix"
        else:
            say = f"Vos choix : {choices}"

        await ctx.send(say)

    @commands.command()
    async def setAvailability(self, ctx, *, args):
        user_id = ctx.author.id
        guild_id = ctx.guild.id

        if args in ("None", "0", "", "Null", " "):
            args = None

        self.database_handler.set_availability(user_id, guild_id, args)
        await ctx.send("Disponibilités mises à jour.")

    @commands.command()
    async def getAvailability(self, ctx):
        user_id = ctx.author.id
        guild_id = ctx.guild.id
        availability = self.database_handler.get_availability(user_id, guild_id)

        if availability is None:
            say = "Vous n'avez pas défini vos disponibilités"
        else:
            say = f"Vos disponibilités : {availability}"

        await ctx.send(say)

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
        guild_id = ctx.guild.id
        member = ctx.author
        roles = ctx.message.role_mentions

        for role in roles:
            role_id = role.id
            movable = self.database_handler.get_movable(role_id, guild_id)
            if movable:
                await member.add_roles(role)
            else:
                await ctx.send(f"Le role **{role.name}** n'est pas attribuable")

        await ctx.send("Rôles mis à jour.")

    @commands.command()
    async def removeRole(self, ctx):
        guild_id = ctx.guild.id
        member = ctx.author
        roles = ctx.message.role_mentions

        for role in roles:
            role_id = role.id
            movable = self.database_handler.get_movable(role_id, guild_id)
            if movable:
                await member.remove_roles(role)
            else:
                await ctx.send(f"Le role **{role.name}** n'est pas déplaçeable")

        await ctx.send("Rôles mis à jour.")

    @commands.command()
    async def getEvent(self, ctx):
        user = ctx.author
        channel = await user.create_dm()
        guild_id = ctx.guild.id
        event = self.database_handler.get_guild(guild_id)["event"]
        print(event)
        await channel.send(f"L'évent de la guild est:\n"
                           f"**{event}**")
