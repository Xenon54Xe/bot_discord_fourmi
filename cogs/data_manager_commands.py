import datetime
import time
import asyncio
import os

import discord
from discord.ext import commands, tasks

import sys
p = os.path.abspath(".")
sys.path.insert(0, p)

from functions import Function
from BDD.database_handler import DatabaseHandler


def setup(bot):
    bot.add_cog(DataManagerCommands(bot))
    bot.add_cog(EventCommands(bot))
    print("Loading DataManagerCommands and EventCommands...")


class DataManagerCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.database_handler = DatabaseHandler("database.db")
        self.functions = Function()

    def cog_check(self, ctx):
        return self.is_data_manager(ctx)

    # vérifie qu'un membre ayant fait la commande puisse l'utiliser
    def is_data_manager(self, ctx):
        member = ctx.author
        is_admin = member.guild_permissions.administrator
        if is_admin:
            return True

        guild_id = ctx.guild.id
        roles = member.roles
        for role in roles:
            if role.name == "@everyone":
                continue
            role_id = role.id
            manager = self.database_handler.get_role(role_id, guild_id)["isDataManager"]
            if manager:
                return True
        return False

    # essaye de trouver un utilisateur depuis son prénom
    def find_users_with_name(self, guild_id: int, name: str) -> list:
        users = self.database_handler.get_all_users(guild_id)
        found_users = [i for i in users if i["username"] == name]

        return found_users

    # ajoute un utilisateur virtuel
    @commands.command()
    async def addUser(self, ctx, *, name):
        guild = ctx.guild
        guild_id = guild.id

        find = self.find_users_with_name(guild_id, name)
        if len(find) > 0:
            await ctx.send(f"Il existe déjà un utilisateur avec le nom __'{name}'__.")
            return
        self.database_handler.add_user(-1, guild_id, name)

        await ctx.send("Membre ajouté.")

    # donne les pseudos de tous les membres du serveur (membres virtuels compris)
    @commands.command()
    async def getUsername(self, ctx):
        guild = ctx.guild
        guild_id = guild.id

        member = ctx.author

        channel = await member.create_dm()

        users = self.database_handler.get_all_users(guild_id)

        warning = self.functions.warning
        first_msg = await channel.send(f"__Pseudos__")

        true_users = []
        virtual_users = []
        for user in users:
            if user["userId"] == -1:
                virtual_users.append(user)
            else:
                true_users.append(user)

        async def print_users(list_users: list):
            for nb_users in range(len(list_users)):
                say = ""
                for ten_user in range(10):
                    try:
                        user = list_users[nb_users * 10 + ten_user]
                    except:
                        break
                    say += f"``{user['username']}`` "
                if say != "":
                    await channel.send(say)
                else:
                    break

        await channel.send("**Membres du serveur:**")
        await print_users(true_users)

        await channel.send(f"{warning} **Membres virtuels:**")
        await print_users(virtual_users)

        await first_msg.reply("Le début est là-haut")

    # supprime un utilisateur virtuel
    @commands.command()
    async def removeUser(self, ctx, name):
        guild = ctx.guild
        guild_id = guild.id

        users = self.find_users_with_name(guild_id, name)
        if len(users) == 0:
            await ctx.send(f"Le membre ayant le nom __'{name}'__ n'existe pas.")
            return
        elif len(users) > 1:
            await ctx.send(f"Il y a {len(users)} membres ayant le nom __'{name}'__. Seuls les membres "
                           f"qui ont étés ajoutés manuellement seront supprimés.")
        users_to_remove = [i for i in users if i["userId"] == -1]

        for user in users_to_remove:
            bdd_id = user["id"]
            self.database_handler.remove_user(bdd_id=bdd_id)

        await ctx.send("Utilisateur(s) supprimé(s).")

    # définit les données d'un/d' autre(s) membre(s)
    @commands.command()
    async def setOtherData(self, ctx, data_name, type_of_user, username, *, arg: str):
        guild = ctx.guild
        guild_id = guild.id

        """
        Vérifications principales
        """
        if data_name not in self.functions.user_data_name:
            await ctx.send(f"Vous devez renseigner le type de donnée que vous voulez modifier :\n"
                           f"``{self.functions.user_data_name}``")
            return
        elif data_name in ["choice", "availability"]:
            if len(arg) > self.functions.max_text_length:
                await ctx.send(f"Vous ne devez pas dépasser **{self.functions.max_text_length}** caractères.")
                return

        if type_of_user not in self.functions.user_type:
            await ctx.send(f"Vous devez renseigner le type d'utilisateur :\n"
                           f"``{self.functions.user_type}``")
            return

        """
        Définition des membres dont il faut modifier les données
        """
        if type_of_user == "normal":
            users_message = ctx.message.mentions
            users = []
            for user in users_message:
                users.append(self.database_handler.get_user(user.id, guild_id))
                arg = arg.replace(f"<@{user.id}>", "")

            while arg.startswith(" "):
                arg = arg[1:]
        else:
            users = self.find_users_with_name(guild_id, username)
            if len(users) == 0:
                await ctx.send(f"L'utilisateur avec le nom __'{username}'__ n'a pas été trouvé.")
                return
            elif len(users) > 1:
                await ctx.send(f"Il y a plusieurs utilisateurs avec le pseudo __'{username}'__ et il vont "
                               f"tous être modifié.")

        """
        Vérifications secondaires
        """
        if data_name == "speciality" and arg not in self.functions.user_speciality + self.functions.list_none:
            await ctx.send(f"Vous devez choisir entre les trois spécialités suivantes :\n"
                           f"``{self.functions.user_speciality}`` ou __null__.")
        elif data_name == "percentage":
            percent_list = self.functions.take_data_for_percentage(arg)
            if percent_list[0] is False:
                await ctx.send(f"Vous vous êtes trompé dans le dernier argument. {percent_list[1]}")
                return
            else:
                percent_list = percent_list[1]

        if arg in self.functions.list_none:
            arg = None

        """
        Modification des données
        """
        for user in users:
            bdd_id = user["id"]
            if data_name == "choice":
                self.database_handler.set_choice(new_choices=arg, bdd_id=bdd_id)
            elif data_name == "availability":
                self.database_handler.set_availability(availability=arg, bdd_id=bdd_id)
            elif data_name == "speciality":
                self.database_handler.set_speciality(speciality=arg, bdd_id=bdd_id)
            elif data_name == "percentage":
                # récupération des données de la BDD
                percentage_db = self.database_handler.get_user(bdd_id=bdd_id)["percentage"]
                percentage_unpack = self.functions.unpack_str_to_dict_list(percentage_db)
                if percentage_unpack == {}:
                    percentage_unpack = {
                        "army": [0, 0, 0],
                        "cac": [0, 0, 0],
                        "vel": [0, 0, 0],
                        "tir": [0, 0, 0]
                    }

                # ajout des valeur
                for case in percent_list:
                    key = case[0]
                    nums = case[1]
                    percentage_unpack[key] = nums

                # mise à jour de la BDD
                arg = self.functions.pack_dict_list_to_str(percentage_unpack)
                self.database_handler.set_percentages(bdd_id=bdd_id, percentage=arg)

        await ctx.send("Données mis à jour.")

    # définit le nombre d'annonces qu'un rôle peut faire
    @commands.command()
    async def setAdCount(self, ctx, value):
        guild = ctx.guild
        guild_id = guild.id

        roles = ctx.message.role_mentions

        try:
            value = int(value)
        except:
            await ctx.send(f"La valeur '{value}' que vous avez renseigné n'est pas un nombre entier.")
            return

        if len(roles) == 0:
            await ctx.send("Vous avez oublié la mention du ou des rôles.")
            return

        for role in roles:
            role_id = role.id
            self.database_handler.set_role_ad_value(role_id, guild_id, value)

        await ctx.send("Nombre d'annonces des rôles mis à jour.")

    # donne les choix de tous les membres
    @commands.command()
    async def getAllChoice(self, ctx):
        guild = ctx.guild
        guild_id = guild.id

        user = ctx.author
        channel = await user.create_dm()
        users = self.database_handler.get_all_users(guild_id)

        warning = self.functions.warning
        first_msg = await channel.send(f"__Données__\n"
                                       f"{warning} = Utilisateur virtuel\n")
        for nb_users in range(len(users)):
            say = ""
            for ten_user in range(10):
                try:
                    user = users[nb_users * 10 + ten_user]
                except:
                    break
                username = user["username"]
                count = len(username)
                space = 20 - count
                if count < 0:
                    count = 0
                choice = user["choice"]
                if choice is None:
                    choice = ""
                say += f"``{username}{' ' * space}`` : {choice}\n"
                if user["userId"] == -1:
                    say = say[:-1]
                    say += f"{warning}\n"
            if say != "":
                await channel.send(say)
            else:
                break

        await first_msg.reply("Le début est là-haut.")

    # donne les disponibilités de tous les membres
    @commands.command()
    async def getAllAvailability(self, ctx):
        guild = ctx.guild
        guild_id = guild.id

        user = ctx.author
        channel = await user.create_dm()
        users = self.database_handler.get_all_users(guild_id)

        warning = self.functions.warning
        first_msg = await channel.send(f"__Données__\n"
                                       f"{warning} = Utilisateur virtuel\n")
        for nb_users in range(len(users)):
            say = ""
            for ten_users in range(10):
                try:
                    user = users[nb_users * 10 + ten_users]
                except:
                    break
                username = user["username"]
                count = len(username)
                space = 20 - count
                if count < 0:
                    count = 0
                choice = user["availability"]
                if choice is None:
                    choice = ""
                say += f"``{username}{' ' * space}`` : {choice}\n"
                if user["userId"] == -1:
                    say = say[:-1]
                    say += f"{warning}\n"
            if say != "":
                await channel.send(say)
            else:
                break

        await first_msg.reply("Le début est là-haut.")

    # donne les spécialités de tous les membres
    @commands.command()
    async def getAllSpeciality(self, ctx):
        guild = ctx.guild
        guild_id = guild.id

        member = ctx.author
        channel = await member.create_dm()

        members_db = self.database_handler.get_all_users(guild_id)

        dictionary = {
            "cac": [],
            "vel": [],
            "tir": [],
            None: []
        }
        for member_db in members_db:
            spe = member_db["speciality"]
            dictionary[spe].append(member_db)

        warning = self.functions.warning
        first_msg = await channel.send(f"__Données__\n"
                                       f"{warning} = Utilisateur virtuel\n")
        for key in dictionary.keys():
            name = key
            if name == "cac":
                name = "corps à corps"
            elif name == "vel":
                name = "véloces"
            elif name == "tir":
                name = "tireuses"
            else:
                name = "pas précisée"

            await channel.send(f"**```Nombre de spécialité {name} : {len(dictionary[key])}```**")
            members = dictionary[key]
            for nb_users in range(len(members)):
                say = ""
                for ten_user in range(10):
                    try:
                        user = members[nb_users * 10 + ten_user]
                    except:
                        break
                    say += f"***-*** ``{user['username']}``\n"
                    if user["userId"] == -1:
                        say = say[:-1]
                        say += f"{warning}\n"
                if say != "":
                    await channel.send(say)
                else:
                    break

        await first_msg.reply(f'Le début est là-haut.')

    # donne les pourcentages de tous les membres
    @commands.command()
    async def getAllPercentage(self, ctx):
        guild = ctx.guild
        guild_id = guild.id

        user = ctx.author
        channel = await user.create_dm()
        users = self.database_handler.get_all_users(guild_id)

        warning = self.functions.warning
        first_msg = await channel.send(f"__Données__\n"
                                       f"{warning} = Utilisateur virtuel\n")
        for user in users:
            if user["userId"] == -1:
                username = f"**{user['username']}** {warning}"
            else:
                username = f"**{user['username']}**"
            percentage_db = user["percentage"]
            percentage_unpack = self.functions.unpack_str_to_dict_list(percentage_db)

            keys = percentage_unpack.keys()
            if len(keys) == 0:
                continue

            speciality = user["speciality"]
            if speciality is None or speciality == "":
                speciality = "pas précisée"
            elif speciality == "cac":
                speciality = "corps à corps"
            elif speciality == "vel":
                speciality = "véloces"
            else:
                speciality = "tireuses"

            embed = discord.Embed(title=username, description="Spécialité ")

            for key in keys:
                value = percentage_unpack[key]
                attack = value[0]
                defense = value[1]
                life = value[2]

                if key == "army":
                    name = "Armée"
                elif key == "cac":
                    name = "Corps à corps"
                elif key == "vel":
                    name = "Véloces"
                else:
                    name = "Tireuses"

                embed.add_field(name=name, value=f"``Attaque``: **{attack}**\n``Défense``: **{defense}**\n``Vie    ``: **{life}**")

            await channel.send(embed=embed)

        await channel.send("__Si il manque des membres c'est qu'ils n'ont pas rempli leurs pourcentages__.")
        await first_msg.reply(f'Le début est là-haut.')

    @commands.command()
    async def getData(self, ctx):
        guild = ctx.guild
        guild_id = guild.id

        user = ctx.author
        channel = await user.create_dm()

        first_msg = await channel.send("__Données__")

        """
        Rôles
        """
        roles = self.database_handler.get_all_roles(guild_id)
        await channel.send("**```Rôles :```**")

        role_data_manager = [i for i in roles if i["isDataManager"]]
        if len(role_data_manager) == 1:
            await channel.send(f"Le rôle **data manager** est **{role_data_manager[0]['roleName']}**.")
        else:
            await channel.send("Il n'y a pas de rôles **data manager**.")

        roles_movable = [i for i in roles if i["isMovable"]]
        if len(roles_movable) > 0:
            text = "Les rôles **movable** sont :"
            for role in roles_movable:
                name = role['roleName']
                text += f" **{name}**,"
            text = text[:-1]
            await channel.send(f"{text}.")
        else:
            await channel.send("Il n'y a pas de rôles **movable**.")

        roles_event = [i for i in roles if i["isEvent"]]
        if len(roles_event) > 0:
            text = "Les rôles **event** sont :"
            for role in roles_event:
                name = role['roleName']
                text += f" **{name}**,"
            text = text[:-1]
            await channel.send(f"{text}.")
        else:
            await channel.send("Il n'y a pas de rôles **event**.")

        text = "Le **nombre d'annonces** que les rôles peuvent faire sont :"
        for role in roles:
            name = role["roleName"]
            ad_value = role["adValue"]
            text += f" **@{name}={ad_value}**,"
        text = text[:-1]
        await channel.send(text)

        """
        Serveur
        """
        guild_db = self.database_handler.get_guild(guild_id)

        cmd_channel_id = guild_db["cmdChannelId"]
        cmd_channel = guild.get_channel(cmd_channel_id)
        if cmd_channel is not None:
            cmd_text = f"Le salon des commandes est {cmd_channel.mention}, son id est **{cmd_channel.id}**."
        else:
            cmd_text = "Il n'y a pas de salon réservé aux commandes."

        event_channel_id = guild_db["eventChannelId"]
        event_channel = guild.get_channel(event_channel_id)
        if event_channel is None:
            event_channel = guild.text_channels[0]
        event_text = f"Le salon où sont affichés les évenements est {event_channel.mention}, son id est " \
                     f"**{event_channel.id}**."

        ad_channel_id = guild_db["adChannelId"]
        ad_channel = guild.get_channel(ad_channel_id)
        if ad_channel is None:
            ad_channel = guild.text_channels[0]
        ad_text = f"Le salon où sont envoyées les annonces est {ad_channel.mention}, son id est **{ad_channel.id}**."

        embed = discord.Embed(title="Salons", description="Voici les informations sur les salons spéciaux du serveur.")
        embed.add_field(name="Salon des commandes", value=cmd_text)
        embed.add_field(name="Salon des évenements", value=event_text)
        embed.add_field(name="Salon des annonces", value=ad_text)

        await channel.send(embed=embed)

        await first_msg.reply("Le début est là-haut.")

    # réinitialise les données de tous les membres
    @commands.command()
    async def reset(self, ctx, arg):
        guild = ctx.guild
        guild_id = guild.id

        if arg not in ["availability", "choice"]:
            await ctx.send("Il faut choisir entre **availability** et **choice**")
            return

        for user in guild.members:
            user_id = user.id

            if arg == "availability":
                if self.database_handler.user_exists_with(user_id, guild_id):
                    self.database_handler.set_availability(user_id, guild_id)
            elif arg == "choice":
                if self.database_handler.user_exists_with(user_id, guild_id):
                    self.database_handler.set_choice(user_id, guild_id)

        await ctx.send("Réinitialisation effectuée.")


class EventCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.database_handler = DatabaseHandler("database.db")
        self.functions = Function()

        self.interval = 3600
        self.time_before_call_date = 900
        self.recall_event.change_interval(seconds=self.interval)
        self.has_changed_interval = False
        self.already_running = False
        self.recall_event.start()

    # créé ou modifie un évenement du serveur
    @commands.command()
    async def setEvent(self, ctx, event_id: str, key: str, *, value: str):
        print("###START setEvent###")
        guild = ctx.guild
        guild_id = guild.id

        try:
            event_id = int(event_id)
        except:
            event_id = None

        event_db = self.database_handler.get_guild(guild_id)["event"]
        event_unpack = self.functions.unpack_str_to_list_dict(event_db)

        choosed_event = None
        for event in event_unpack:
            if event["id"] == event_id:
                choosed_event = event
                break

        choosed_id = -1
        if choosed_event is None:
            for event in event_unpack:
                if event["id"] > choosed_id:
                    choosed_id = event["id"]
            event_id = choosed_id + 1
            choosed_event = {
                "date": None,
                "event": None,
                "organisation": None,
                "permanent": False,
                "interval": (0, 1),
                "already_recall": False,
                'id': event_id
            }

        def check(msg):
            return msg.channel == ctx.channel and msg.author == ctx.author

        if key not in self.functions.event_keys:
            await ctx.send(f"Vous devez choisir une clé dans la liste ci-dessous :\n"
                           f"``{self.functions.event_keys}``")
            return
        elif key == "date":
            try:
                value = self.functions.take_date(value)
            except:
                await ctx.send("La date que vous avez renseigné n'est pas sous le format : "
                               "**'DD/MM/YY HH:MM:SS'** -> **'jour/mois/années heures:minutes:secondes'**")
        elif key == "event":
            pass
        elif key == "organisation":
            pass
        elif key == "permanent":
            if value in self.functions.list_true:
                value = True
            elif value in self.functions.list_false:
                value = False
            else:
                await ctx.send("Argument à modifier : **permanent**, cet argument est soit __vrai__ soit __faux__, "
                               "mais je n'ai pas compris ce que vous voulez mettre.")
        elif key == "interval":
            try:
                value = self.functions.take_numbers(value, to_int=True)
                if len(value) != 2:
                    await ctx.send(f"Il faut deux nombres : __'{value}'__")
                    return
                if value[0] == 0 and value[1] == 0:
                    await ctx.send("L'intervalle minimum est de une heure.")
                    value = [0, 1]
            except:
                await ctx.send("Vous devez indiquer le nombre de jours et le nombre d'heures.")
                return

            if choosed_event["permanent"] is False:
                await ctx.send("Argument à modifier : **interval**, pour le modifier il faut que l'argument "
                               "**permanent** soit sur __vrai__, voulez-vous le mettre sur vrai ?")
                try:
                    msg = await self.bot.wait_for('message', check=check, timeout=60)
                    content = msg.content
                except asyncio.TimeoutError:
                    content = "non"

                if content in self.functions.list_true:
                    choosed_event["permanent"] = True
                elif content in self.functions.list_false:
                    await ctx.send("Opération annulée.")
                    return
                else:
                    await ctx.send("Je n'ai pas compris.")
                    return

        choosed_event[key] = value

        event_found = False
        for i in range(len(event_unpack)):
            if event_unpack[i]["id"] == choosed_event["id"]:
                event_unpack[i] = choosed_event
                event_found = True
                break

        if not event_found:
            event_unpack.append(choosed_event)

        event_pack = self.functions.pack_list_dict_to_str(event_unpack)

        self.database_handler.set_event(guild_id, event_pack)

        self.recall_event.change_interval(seconds=self.interval)
        self.has_changed_interval = False

        if self.recall_event.is_running:
            self.recall_event.restart()
        else:
            self.recall_event.start()

        await ctx.send("Evenement mis à jour.")

    # donne tous les évenements du serveur
    @commands.command()
    async def getEvent(self, ctx):
        guild = ctx.guild
        guild_id = guild.id

        event_db = self.database_handler.get_guild(guild_id)["event"]

        if event_db != "" and event_db is not None:
            event_list = self.functions.unpack_str_to_list_dict(event_db)
        else:
            await ctx.send("Il n'y a pas d'évenements sur ce serveur.")
            return

        for event_lib in event_list:
            embed = self.embed_event(event_lib, title="GetEvent", description="", show_utc=True, show_id=True)
            await ctx.send(embed=embed)

    # supprime un évenement du serveur
    @commands.command()
    async def delEvent(self, ctx, *, event_id):
        guild = ctx.guild
        guild_id = guild.id

        try:
            event_id = int(event_id)
        except:
            await ctx.send(f"Il faut l'identifiant d'un évenement, __'{event_id}'__ n'est pas un identifiant.")

        event_db = self.database_handler.get_guild(guild_id)["event"]
        event_unpack = self.functions.unpack_str_to_list_dict(event_db)

        if len(event_unpack) == 0:
            await ctx.send("Il n'y a pas d'évenements de prévus.")
            return

        event_to_destroy = None
        for event in event_unpack:
            if event["id"] == event_id:
                event_to_destroy = event
                break

        if event_to_destroy is not None:
            event_unpack.remove(event_to_destroy)
        else:
            await ctx.send(f"L'évenement avec l'id __'{event_id}'__ n'a pas été trouvé.")
            return

        event_str = self.functions.pack_list_dict_to_str(event_unpack)
        self.database_handler.set_event(guild_id, event_str)

        await ctx.send("Evenement supprimé.")

    # définit le(s) rôle(s) qui sont mentionnés quand un évenement est affiché
    @commands.command()
    async def setRoleEvent(self, ctx, arg):
        guild = ctx.guild
        guild_id = guild.id

        roles = ctx.message.role_mentions

        print(arg)
        if arg in self.functions.list_true:
            arg = True
        elif arg in self.functions.list_false:
            arg = False
        else:
            await ctx.send("Je n'ai pas bien compris ce que vous voulez faire. Essayez avec **oui** ou **non**")
            return

        if len(roles) == 0:
            await ctx.send("Vous avez oublié la mention du ou des rôles.")
            return

        for role in roles:
            role_id = role.id
            self.database_handler.set_role_is_event(role_id, guild_id, arg)

        await ctx.send("Rôle évent mis à jour.")

    # définit le temps qui sépare le premier et le deuxième affichage dans le serveur
    @commands.command()
    async def setTimeBeforeCall(self, ctx, seconds):
        guild = ctx.guild
        guild_id = guild.id


        try:
            value = int(seconds)
        except:
            await ctx.send(f"Il faut un nombre, **{seconds}** n'est pas un nombre.")
            return

        if value < 900:
            await ctx.send("La valeur minimale est de **900** secondes, ce qui fait 15 minutes")
            value = 900

        self.database_handler.set_time_before_call(guild_id, value)
        self.recall_event.restart()
        await ctx.send("Temps d'envoit avant la date de l'évenement mis à jour.")

    # boucle qui permet d'afficher les évenements à la bonne date
    @tasks.loop(seconds=10)
    async def recall_event(self):
        # Pour éviter que la fonction soit appelée pleins de fois à cause d'un temps très petit
        if self.already_running:
            return
        self.already_running = True

        """
        Si l'intervalle de la tâche vient d'être changé alors ne pas lire la suite
        """
        if self.has_changed_interval:
            self.has_changed_interval = False
            self.already_running = False
            print("###UPDATE recall_event###")
            return

        print("###START recall_event###")

        # récupère tous les serveurs où le bot est
        guilds: [discord.Guild] = self.bot.guilds

        # définir les valeurs
        global_shortest_time = 3600
        global_nb_events = 0

        for guild in guilds:
            guild_id = guild.id

            # récupérer le salon des évenements
            channel_event = guild.get_channel(self.database_handler.get_guild(guild_id)["eventChannelId"])
            if channel_event is None:
                channel_event = guild.text_channels[0]

            # récupérer le temps avant le dernier affichage du serveur pour les évenements
            time_before_last_call = self.database_handler.get_guild(guild_id)["timeBeforeLastCall"]

            """
            Rôle event
            """
            roles_event = []
            for role_db in self.database_handler.get_all_roles(guild_id):
                if role_db["isEvent"]:
                    role = guild.get_role(role_db["roleId"])
                    if role is None:
                        print(f"L'id '{role_db['roleId']}' ne permet pas de trouver un rôle.")
                    roles_event.append(role)
            if len(roles_event) == 0:
                roles_event.append(guild.default_role)

            # récupérer les évenements du serveur
            event_db = self.database_handler.get_guild(guild_id)["event"]
            if event_db is None or event_db == "":
                print(f"Pas d'event dans le serveur {guild.name}")
                continue

            # mettre les évenements sous forme de liste de dictionnaire
            event_unpack = self.functions.unpack_str_to_list_dict(event_db)
            # récupérer le temps actuel sous forme de float
            current_time_float = time.time()

            # définir la liste où irons les évenements à détruire
            event_to_remove = []
            for i in range(len(event_unpack)):
                # définir l'évenement sur lequel faire des testes...
                event = event_unpack[i]

                # vérifie si il n'y a pas de date
                if event["date"] is None:
                    global_nb_events -= 1
                    continue

                """
                Vérifie si déjà appelé.
                """
                if event["already_recall"]:
                    # temps restant = date prévue moins date actuelle (float)
                    remaining_time_before_next_call = event["date"] - current_time_float
                else:
                    # temps restant = date prévue moins date actuelle moins time_before_last_call
                    remaining_time_before_next_call = event["date"] - current_time_float - time_before_last_call

                """
                Si a atteint la date d'envoit de l'évenement
                """
                if remaining_time_before_next_call <= 0:
                    # si cet évenement à déjà été appelé
                    if event["already_recall"]:
                        # afficher l'évenement
                        embed = self.embed_event(event, description="Un évenement à commencé !")
                        mentions = ""
                        for role_event in roles_event:
                            if role_event.name == "@everyone":
                                mentions += "@everyone"
                            else:
                                mentions += f"{role_event.mention}"
                        await channel_event.send(content=mentions, embed=embed)

                        # si cet évenement est permanent, ajouter le temps pour la prochaine date d'affichage
                        if event["permanent"]:
                            interval = event["interval"]
                            time_to_add = interval[0] * 24 * 3600 + interval[1] * 3600
                            event["date"] += time_to_add
                            # stocker le fait qu'il puisse être rappelé
                            event["already_recall"] = False
                            # mettre à jour l'évenement dans la liste
                            event_unpack[i] = event
                        else:
                            # sinon le mettre dans la liste des évenements à supprimer
                            event_to_remove.append(event)

                    # si pas déjà appelé
                    else:
                        # afficher l'évenement
                        embed = self.embed_event(event)
                        mentions = ""
                        for role_event in roles_event:
                            if role_event.name == "@everyone":
                                mentions += "@everyone"
                            else:
                                mentions += f"{role_event.mention}"
                        await channel_event.send(content=mentions, embed=embed)

                        # stocker qu'il à été appelé
                        event["already_recall"] = True
                        # mettre à jour l'évenement dans la liste
                        event_unpack[i] = event

            # supprimer les évenements finis
            for event in event_to_remove:
                try:
                    event_unpack.remove(event)
                except Exception as exc:
                    raise exc

            # ajouter le nombre d'évenements de ce serveur
            global_nb_events += len(event_unpack)

            # mettre à jour la BDD
            event_pack = self.functions.pack_list_dict_to_str(event_unpack)
            self.database_handler.set_event(guild_id, event_pack)

            # stocker le temps restant le plus court avant le prochain affichage
            shortest_time = self.get_shortest_time(event_unpack, guild_id)
            # si ce temps est le plus court de tous les évenements
            if shortest_time < global_shortest_time:
                global_shortest_time = shortest_time

        """
        Si il n'y a plus d'évenement dans aucuns serveurs arrêter la tache
        """
        if global_nb_events == 0:
            print("###STOP recall_event###")
            self.already_running = False
            self.recall_event.stop()
            return

        if global_shortest_time < 0:
            global_shortest_time = 0

        # changer l'intervalle de la tâche
        self.recall_event.change_interval(seconds=global_shortest_time)
        # stocker le fait que la tâche à changé d'intervalle
        self.has_changed_interval = True
        # redémarrer la tâche
        self.already_running = False
        self.recall_event.restart()

        print("###END recall_event###")

    # retourne le temps d'attente avant le prochain affichage le plus court
    def get_shortest_time(self, list_dict: [dict], guild_id: int, maximum: int = 3600) -> float:
        current_time_float = time.time()
        time_before_last_call = self.database_handler.get_guild(guild_id)["timeBeforeLastCall"]

        shortest_time = maximum
        for event in list_dict:
            if event["date"] is None:
                continue

            if event["already_recall"]:
                time_before_next_call = event["date"] - current_time_float
            else:
                time_before_next_call = event["date"] - current_time_float - time_before_last_call
            if time_before_next_call < shortest_time:
                shortest_time = time_before_next_call
        return shortest_time

    # permet de connaître le temps qui sépare le membre du temps UTC
    @commands.command()
    async def getTime(self, ctx):
        current_time = time.time()
        dutc = self.functions.take_date_from_struct(time.gmtime(current_time))
        embed = discord.Embed(title="Time Zone",
                              description="Trouver le temps qui vous sépare du méridien de greenwich",
                              colour=8765432,
                              timestamp=datetime.datetime(dutc[0], dutc[1], dutc[2], dutc[3], dutc[4], dutc[5]))
        embed.add_field(name="Explication", value="Il vous suffit de soustraire le temps UTC à votre temps local pour "
                                                  "trouver le nombre d'heure qui vous sépare du méridien de Greenwich.\n"
                                                  "__(Local - UTC = DT)__", inline=False)
        embed.add_field(name="UTC", value=f"Le temps UTC est de {dutc[3]}:{dutc[4]}", inline=False)
        embed.set_footer(text="Temps Local")
        await ctx.send(embed=embed)

        await ctx.send("Quel est votre temps local ? Donnez moi l'heure et la minute. (HH:MM)")

        def check(msg):
            return msg.channel == ctx.channel and msg.author == ctx.author

        msg = await self.bot.wait_for('message', check=check, timeout=60)

        num = self.functions.take_numbers(msg.content, to_int=True)
        if len(num) != 2:
            await ctx.send("Je n'ai pas bien compris.")
            return

        hour = num[0]
        min = num[1]
        utc_hour = dutc[3]
        utc_min = dutc[4]

        if hour < utc_hour:
            hour += 24
        if min < utc_min:
            min += 60

        dt_hour = hour - utc_hour
        dt_min = min - utc_min

        await ctx.send(f"Vous avez donc {dt_hour} heures et {dt_min} min d'avance par rapport au temps utc.\n"
                       f"Ce qui est utile à savoir puisque pour créer un évenement il faut rentrer la date en heure "
                       f"utc et pas en heure locale.")

    # retourne un embed depuis un dictionnaire Event
    def embed_event(self, event: dict, title: str = "Commandant !", description: str = "Un évenement va bientôt commencer !",
                    show_utc: bool = False, show_id: bool = False) -> discord.Embed:

        date = event["date"]
        dlu = None

        if date is None:
            embed = discord.Embed(title=title, description=description, colour=592029)
        else:
            dlu = self.functions.take_date_from_struct(time.gmtime(date))
            timestamp = datetime.datetime(dlu[0], dlu[1], dlu[2], dlu[3], dlu[4], dlu[5])
            embed = discord.Embed(title=title, description=description, timestamp=timestamp)

        embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar_url)

        if event["event"] is not None:
            embed.add_field(name="Evenement", value=event["event"], inline=False)
        if event["organisation"] is not None:
            embed.add_field(name="Organisation", value=event["organisation"], inline=False)
        if event["permanent"]:
            interval = event["interval"]
            value = f"Cet évenement revient tous les __{interval[0]}__ jours et __{interval[1]}__ heures."

            embed.add_field(name="Permanent", value=value, inline=False)

        if show_utc and date is not None:
            embed.add_field(name="UTC", value=f"``{dlu[2]}/{dlu[1]}/{dlu[0]} {dlu[3]}:{dlu[4]}:{dlu[5]}``")

        text_footer = ""
        if show_id:
            text_footer += f"ID: {event['id']}\n"
        if date is not None:
            text_footer += "Date "

        if text_footer != "":
            embed.set_footer(text=text_footer)
        return embed
