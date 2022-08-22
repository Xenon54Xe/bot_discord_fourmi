import discord
from discord.ext import commands
import os

import sys
p = os.path.abspath(".")
sys.path.insert(0, p)

from BDD.database_handler import DatabaseHandler
from functions import Function


def setup(bot):
    bot.add_cog(Events(bot))
    print("Loading Events...")


class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.database_handler = DatabaseHandler("database.db")
        self.functions = Function()

    # ajoute le serveur rejoint dans la BDD
    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.guild):
        guild_id = guild.id
        guild_name = guild.name

        if self.database_handler.guild_exists_with(guild_id):
            self.database_handler.update_guild(guild_id, guild_name)
        else:
            self.database_handler.add_guild(guild_id, guild_name)

        channel = guild.text_channels[0]
        embed = self.functions.get_prerequis_embed()
        await channel.send(embed=embed)

    # met à jour le serveur dans la BDD
    @commands.Cog.listener()
    async def on_guild_update(self, before, after):
        guild = after.guild
        guild_id = guild.id
        guild_name = guild.name

        try:
            self.database_handler.update_guild(guild_id, guild_name)
        except:
            raise Exception(f"Le serveur '{after.name}' à été modifié et ne figurait pas dans la BDD...")

    # supprime le serveur quitté de la BDD
    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.guild):
        guild_id = guild.id

        try:
            self.database_handler.remove_guild(guild_id)
        except:
            raise Exception(f"Le serveur '{guild.name}' à été quitté et ne figurait pas dans la BDD...")

    # ajoute le membre qui a rejoint dans la BDD
    @commands.Cog.listener()
    async def on_member_join(self, member):
        if member.bot:
            return
        guild = member.guild
        guild_id = guild.id

        user_id = member.id
        username = member.display_name

        if self.database_handler.user_exists_with(user_id, guild_id):
            self.database_handler.update_user(user_id, guild_id, username)
        else:
            self.database_handler.add_user(user_id, guild_id, username)

    # met à jour le membre dans la BDD
    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if after.bot:
            return
        guild = after.guild
        guild_id = guild.id

        user_id = after.id
        username = after.display_name

        try:
            self.database_handler.update_user(user_id, guild_id, username)
        except:
            raise Exception(f"Le profil du membre '{username}' du serveur '{guild.name}' à été modifié et ne figurait "
                            f"pas dans la BDD...")

    # supprime le membre qui a quitté de la BDD
    @commands.Cog.listener()
    async def on_member_remove(self, member):
        if member.bot:
            return
        guild = member.guild
        guild_id = guild.id

        user_id = member.id

        try:
            self.database_handler.remove_user(user_id, guild_id)
        except:
            raise Exception(f"Le membre '{member.name}' à quitté le serveur '{guild.name}' et ne figurait pas "
                            f"dans la BDD...")

    # ajoute le rôle qui a été créé dans la BDD
    @commands.Cog.listener()
    async def on_guild_role_create(self, role):
        if role.is_bot_managed():
            return
        guild = role.guild
        guild_id = guild.id

        role_id = role.id
        role_name = role.name

        if self.database_handler.role_exists_with(role_id, guild_id):
            self.database_handler.update_role(role_id, guild_id, role_name)
        else:
            self.database_handler.add_role(role_id, guild_id, role_name)

    # met à jour le rôle dans la BDD
    @commands.Cog.listener()
    async def on_guild_role_update(self, before, after):
        if after.is_bot_managed():
            return
        guild = after.guild
        guild_id = guild.id

        role_id = after.id
        role_name = after.name

        try:
            self.database_handler.update_role(role_id, guild_id, role_name)
        except:
            raise Exception(f"Le rôle '{role_name}' du serveur '{guild.name}' à été modifié et ne figurait "
                            f"pas dans la BDD...\n"
                            f"Ou alors ce rôle est un rôle de bot.")

    # supprime le rôle qui a été supprimé de la BDD
    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        if role.is_bot_managed():
            return
        guild = role.guild
        guild_id = guild.id

        role_id = role.id

        try:
            self.database_handler.remove_role(role_id, guild_id)
        except:
            raise Exception(f"Le rôle '{role.name}' à été supprimé du serveur '{guild.name}' et ne figurait pas "
                            f"dans la BDD...")
