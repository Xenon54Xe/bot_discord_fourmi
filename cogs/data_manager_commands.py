import discord
from discord.ext import commands
import sys
from os import path

p = path.abspath(".")
sys.path.insert(1, p)

import BDD.database_handler as dbh


def setup(bot):
    bot.add_cog(DataManagerCommands(bot))
    print("Loading DataManagerCommands...")


class DataManagerCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.database_handler = dbh.DatabaseHandler("database.db")

    def cog_check(self, ctx):
        member = ctx.author
        is_admin = member.guild_permissions.administrator
        if is_admin:
            return True

        guild_id = ctx.guild.id
        roles = member.roles
        for role in roles:
            role_id = role.id
            manager = self.database_handler.get_data_manager(role_id, guild_id)
            if manager:
                return True
        return False

    @commands.command()
    async def setEvent(self, ctx, *, event):
        guild_id = ctx.guild.id
        self.database_handler.set_event(guild_id, event)
        await ctx.send("L'évent de la guild à été mis à jour.")

    @commands.command()
    async def getAllChoices(self, ctx):
        guild_id = ctx.author.guild.id
        user = ctx.author
        channel = await user.create_dm()
        users = self.database_handler.get_all_users(guild_id)

        say = ""
        for user in users:
            username = user["username"]
            choice = user["choice"]
            if choice is None:
                choice = ""
            say += f"{username} : {choice}\n"
        await channel.send(say)

    @commands.command()
    async def getAllAvailability(self, ctx):
        guild_id = ctx.guild.id
        user = ctx.author
        channel = await user.create_dm()
        users = self.database_handler.get_all_users(guild_id)

        say = ""
        for user in users:
            username = user["username"]
            choice = user["availability"]
            if choice is None:
                choice = ""
            say += f"{username} : {choice}\n"
        await channel.send(say)

    @commands.command()
    async def getAllUsers(self, ctx):
        guild_id = ctx.guild.id
        users = self.database_handler.get_all_users(guild_id)
        say = ""
        for user in users:
            say += f"{user['username']}\n"
        await ctx.send(say)
