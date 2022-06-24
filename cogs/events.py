import discord
from discord.ext import commands

from bot_discord_fourmi.BDD.database_handler import DatabaseHandler


def setup(bot):
    bot.add_cog(Events(bot))
    print("Loading Events...")


class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.database_handler = DatabaseHandler("database.db")

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.guild):
        guild_id = guild.id
        guild_name = guild.name
        self.database_handler.create_guild(guild_id, guild_name)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.guild):
        guild_id = guild.id
        guild_name = guild.name
        self.database_handler.delete_guild(guild_id)

    @commands.Cog.listener()
    async def on_guild_update(self, before, after):
        guild_id = after.id
        guild_name = after.name
        print(guild_name)

        self.database_handler.create_guild(guild_id, guild_name)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        user_id = member.id
        guild_id = member.guild.id
        username = member.display_name
        self.database_handler.create_user(user_id, guild_id, username)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        user_id = member.id
        guild_id = member.guild.id
        self.database_handler.delete_user(user_id, guild_id)

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        guild = after.guild
        guild_id = guild.id

        member_id = after.id
        member_name = after.display_name

        self.database_handler.create_user(member_id, guild_id, member_name)

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

    @commands.Cog.listener()
    async def on_guild_role_update(self, before, after):
        guild = after.guild
        guild_id = guild.id

        role_id = after.id
        role_name = after.name

        self.database_handler.create_user(role_id, guild_id, role_name)
