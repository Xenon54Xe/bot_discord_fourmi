import discord
from discord.ext import commands
import sys
from os import path

p = path.abspath(".")
sys.path.insert(1, p)

import BDD.database_handler as dbh


def setup(bot):
    bot.add_cog(AdminCommands(bot))
    print("Loading AdminCommands...")


class AdminCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.database_handler = dbh.DatabaseHandler("database.db")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setRoleManager(self, ctx, manager, *, arg):
        guild = ctx.guild
        if arg in ("All", "Tout", "A"):
            roles = guild.roles
        else:
            roles = ctx.message.role_mentions
            if len(roles) == 0:
                await ctx.send("Il manque la mention des rôles !")
                return

        if manager in ('yes', 'y', 'true', 't', '1', 'enable', 'on'):
            manager = True
        elif manager in ('no', 'n', 'false', 'f', '0', 'disable', 'off'):
            manager = False

        guild_id = guild.id
        for role in roles:
            role_id = role.id
            movable = self.database_handler.get_data_manager(role_id, guild_id)
            if movable and manager:
                await ctx.send(f"Le rôle **{role.name}** est __movable__ et ne peux pas être __data manager__ en plus.")
                continue
            self.database_handler.set_data_manager(role_id, guild_id, manager)

        await ctx.send("Les rôles ont étés mis à jour.")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def getRoleManager(self, ctx):
        guild = ctx.guild
        guild_id = guild.id
        roles = self.database_handler.get_all_roles(guild_id)
        say = "Les rôles manager sont :\n"
        for role in roles:
            role_id = role["roleId"]
            dataManager = role["dataManager"]
            if dataManager:
                role_guild = guild.get_role(role_id)
                say += f"**``{role_guild.name}``**\n"
        await ctx.send(say)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setRoleMovable(self, ctx, movable, *, arg):
        guild = ctx.guild
        guild_id = guild.id

        if arg in ("All", "Tout", "A"):
            roles = guild.roles
        else:
            roles = ctx.message.role_mentions
            if len(roles) == 0:
                await ctx.send("Il manque la mention des rôles !")
                return

        if movable in ('yes', 'y', 'true', 't', '1', 'enable', 'on'):
            movable = True
        elif movable in ('no', 'n', 'false', 'f', '0', 'disable', 'off'):
            movable = False

        for role in roles:
            role_id = role.id
            data_manager = self.database_handler.get_data_manager(role_id, guild_id)
            if data_manager and movable:
                await ctx.send(f"Le rôle **{role.name}** est __data manager__ et ne peux pas être __movable__ en plus.")
                continue
            self.database_handler.set_movable(role_id, guild_id, movable)

        await ctx.send("Les rôles ont étés mis à jour.")
