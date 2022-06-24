from discord.ext import commands
import asyncio

from bot_discord_fourmi.BDD.database_handler import DatabaseHandler
from bot_discord_fourmi import functions as fc


def setup(bot):
    bot.add_cog(AdminCommands(bot))
    print("Loading AdminCommands...")


class AdminCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.database_handler = DatabaseHandler("database.db")
        self.functions = fc.Function()

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setRoleManager(self, ctx, is_manager):
        guild = ctx.guild
        guild_id = guild.id

        if is_manager not in self.functions.list_false + self.functions.list_true:
            await ctx.send("Je ne comprends pas ce que je dois faire, essayez avec oui/non.")
            return
        elif is_manager in self.functions.list_true:
            is_manager = True
        else:
            is_manager = False

        roles = ctx.message.role_mentions
        if len(roles) != 1:
            await ctx.send("Il faut une mention de rôle.")
            return

        role = roles[0]
        role_id = role.id

        def check(msg):
            return msg.channel == ctx.channel and msg.author == ctx.author

        is_movable = self.database_handler.get_role(role_id, guild_id)["isMovable"]
        if is_movable and is_manager:
            await ctx.send(f"Le rôle **{role.name}** est __movable__, c'est à dire que les membres peuvent se le "
                           f"donner. Voulez-vous rendre ce rôle __data manager__ et mettre l'argument "
                           f"__movable__ sur faux ?")
            try:
                msg = await self.bot.wait_for('message', check=check, timeout=60)
                content = msg.content
            except asyncio.TimeoutError:
                content = "non"

            if content in self.functions.list_false:
                await ctx.send("Opération terminée.")
                return
            elif content in self.functions.list_true:
                self.database_handler.set_role_is_movable(role_id, guild_id, False)
            else:
                await ctx.send("Je n'ai pas compris.")
                return

        roles_db = self.database_handler.get_all_roles(guild_id)
        roles_manager = [i for i in roles_db if i["isDataManager"]]
        if len(roles_manager) > 0 and is_manager:
            await ctx.send("Il ne peut y avoir qu'un seul rôle __data manager__ donc l'ancien ne sera plus data "
                           "manager.")
            self.database_handler.set_role_is_data_manager(roles_manager[0]["roleId"], guild_id, False)

        self.database_handler.set_role_is_data_manager(role_id, guild_id, is_manager)

        await ctx.send("Rôle data manager mis à jour.")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def getRoleManager(self, ctx):
        guild = ctx.guild
        guild_id = guild.id

        roles = self.database_handler.get_all_roles(guild_id)
        data_role = [guild.get_role(i["roleId"]) for i in roles if i["isDataManager"]]

        if len(data_role) == 0:
            await ctx.send("Il n'y a pas de rôle dataManager")
        else:
            await ctx.send(f"Le rôle dataManager est **{data_role[0].name}**")

    @commands.command()
    async def setCMDChannel(self, ctx, arg):
        guild = ctx.guild
        guild_id = guild.id

        channels = ctx.message.channel_mentions
        if len(channels) > 1:
            await ctx.send("Il ne peut y avoir qu'un salon pour les commandes du bot.")

        if len(channels) == 0:
            self.database_handler.set_cmd_channel(guild_id, None)
            await ctx.send("Il n'y a plus de salon des commandes.")
        else:
            self.database_handler.set_cmd_channel(guild_id, channels[0].id)
            await ctx.send("Salon des commandes mis à jour.")

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
            guild_roles = guild.roles
            roles = []
            for role in guild_roles:
                if role.is_bot_managed() is False and role != default_role:
                    roles.append(role)
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
                    continue

                # Vérifie que le rôle ne soit pas dataManager
                data_manager = self.database_handler.get_role(role_id, guild_id)["isDataManager"]
                if data_manager:
                    await ctx.send(f"Le rôle **{role.name}** est __data manager__ "
                                   f"et ne peux pas être __movable__ en plus.")
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
                    self.database_handler.set_role_is_movable(role_id, guild_id, False)
                    continue

                # Rend le rôle movable si tout est bon
                self.database_handler.set_role_is_movable(role_id, guild_id, True)

        # Rendre pas movable :
        elif movable in self.functions.list_false:
            for role in roles:
                role_id = role.id
                self.database_handler.set_role_is_movable(role_id, guild_id, False)

        await ctx.send("Rôles mis à jours.")
