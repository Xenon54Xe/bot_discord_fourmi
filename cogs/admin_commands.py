import discord
from discord.ext import commands
import sys
from os import path

p = path.abspath(".")
sys.path.insert(1, p)

import BDD.database_handler as dbh
import functions as fc


def setup(bot):
    bot.add_cog(AdminCommands(bot))
    print("Loading AdminCommands...")


class AdminCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.database_handler = dbh.DatabaseHandler("database.db")
        self.functions = fc.Function()

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setRoleManager(self, ctx, manager):  # finir
        guild = ctx.guild
        guild_id = guild.id

        if manager not in self.functions.list_false + self.functions.list_true:
            await ctx.send("Je ne comprends pas ce que je dois faire, essayez avec oui/non.")
            return

        roles_dataManager = self.database_handler.get_all_roles(guild_id)
        roles_dataManager = [guild.get_role(i["roleId"]) for i in roles_dataManager if i["dataManager"]]
        if len(roles_dataManager) > 1:
            print(f"{guild_id} : Il y a plusieurs rôles dataManager.")

        if manager in self.functions.list_false:
            for role_dm in roles_dataManager:
                role_dm_id = role_dm.id
                self.database_handler.set_data_manager(role_dm_id, guild_id, False)
            await ctx.send("Il n'y a plus de rôles dataManager")
            return

        roles_tgt = ctx.message.role_mentions
        if len(roles_tgt) == 0:
            await ctx.send("Il manque la mention du rôle !")
            return
        if len(roles_tgt) > 1:
            await ctx.send("Il ne peut y avoir qu'un seul rôle dataManager par serveur !")
            return

        if manager in self.functions.list_true:
            role_tgt = roles_tgt[0]
            role_tgt_id = role_tgt.id

            def check(msg):
                return msg.channel == ctx.channel and msg.author == ctx.author

            do_data_manager = True
            if len(roles_dataManager) > 0:
                await ctx.send("Il y a déjà un rôle dataManager, voulez-vous le remplacer ? (oui/non)")

                msg = await self.bot.wait_for('message', check=check, timeout=60)
                text = msg.content
                if text in self.functions.list_true:
                    for role_dm in roles_dataManager:
                        role_dm_id = role_dm.id
                        self.database_handler.set_data_manager(role_dm_id, guild_id, False)
                else:
                    do_data_manager = False

            movable = self.database_handler.get_role(role_tgt_id, guild_id)["movable"]
            if movable:
                await ctx.send(f"Le rôle {role_tgt.name} est __movable__ "
                               f"et ne peut pas être __dataManager__ en plus.")
                self.database_handler.set_data_manager(role_tgt_id, guild_id, False)
            elif do_data_manager:
                self.database_handler.set_data_manager(role_tgt_id, guild_id, True)
            else:
                await ctx.send("Le rôle dataManager n'a pas été modifié.")
                return

            await ctx.send(f"Le rôle **{role_tgt.name}** est maintenant dataManager.")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def getRoleManager(self, ctx):
        # Définition des variables importantes
        guild = ctx.guild
        guild_id = guild.id

        roles = self.database_handler.get_all_roles(guild_id)
        data_role = [guild.get_role(i["roleId"]) for i in roles if i["dataManager"]]

        if len(data_role) == 0:
            await ctx.send("Il n'y a pas de rôle dataManager")
        else:
            await ctx.send(f"Le rôle dataManager est **{data_role[0].name}**")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setRoleMovable(self, ctx, movable, *, arg):
        # Définition des variables importantes
        guild = ctx.guild
        guild_id = guild.id

        default_role = guild.default_role
        default_perms = default_role.permissions
        unauthorized_perm = [i[0] for i in default_perms if i[1] is False]

        # Récupération des rôles qu'il faut rendre movable ou pas
        if arg in self.functions.list_all:
            roles = guild.roles
        else:
            roles = ctx.message.role_mentions
            if len(roles) == 0:
                await ctx.send("Il manque la mention des rôles !")
                return

        # Rendre movable :
        if movable in self.functions.list_true:
            for role in roles:
                role_id = role.id

                # Vérifie que le rôle ne soit pas @everyone
                if role == default_role:
                    await ctx.send("Le rôle **everyone** ne peut pas être movable")
                    self.database_handler.set_movable(role_id, guild_id, False)
                    continue

                # Vérifie que le rôle ne soit pas dataManager
                data_manager = self.database_handler.get_role(role_id, guild_id)["dataManager"]
                if data_manager:
                    await ctx.send(f"Le rôle **{role.name}** est __data manager__ "
                                   f"et ne peux pas être __movable__ en plus.")
                    self.database_handler.set_movable(role_id, guild_id, False)
                    continue

                # Vérifie que le rôle n'ait pas de permissions trop avancées
                role_perms = role.permissions
                role_perms = [i[0] for i in role_perms if i[1] is True]
                role_unauthorized_perms = [i for i in role_perms if i in unauthorized_perm]

                if len(role_unauthorized_perms) > 0:
                    to_say = ""
                    for i in role_unauthorized_perms:
                        to_say += f"{i}, "
                    to_say = to_say[:-2]

                    await ctx.send(f"Le rôle **{role.name}** à des permissions trop avancées pour être movable :\n"
                                   f"*{to_say}*")
                    self.database_handler.set_movable(role_id, guild_id, False)
                    continue

                # Rend le rôle movable si tout est bon
                self.database_handler.set_movable(role_id, guild_id, True)

        # Rendre pas movable :
        elif movable in self.functions.list_false:
            for role in roles:
                role_id = role.id
                self.database_handler.set_movable(role_id, guild_id, False)

        await ctx.send("Rôles mis à jours.")
