import discord
from discord.ext import commands
import sys
from os import path

p = path.abspath(".")
sys.path.insert(1, p)

import BDD.database_handler as dbh


def setup(bot):
    bot.add_cog(Events(bot))
    print("Loading BasicCommands...")


class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.database_handler = dbh.DatabaseHandler("database.db")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        user_id = member.id
        guild_id = member.guild.id
        username = member.name
        self.database_handler.create_user(user_id, guild_id, username)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        user_id = member.id
        guild_id = member.guild.id
        self.database_handler.delete_user(user_id, guild_id)

    @commands.Cog.listener()
    async def on_guild_role_create(self, role):
        role_id = role.id
        guild_id = role.guild.id
        role_name = role.name
        self.database_handler.create_role(role_id, guild_id, role_name)

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        role_id = role.id
        guild_id = role.guild.id
        self.database_handler.delete_role(role_id, guild_id)
