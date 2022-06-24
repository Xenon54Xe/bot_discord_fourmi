import datetime
import time
import asyncio

import discord
from discord.ext import commands, tasks

from bot_discord_fourmi import functions as fc
from bot_discord_fourmi.BDD.database_handler import DatabaseHandler


def setup(bot):
    bot.add_cog(DataManagerCommands(bot))
    print("Loading DataManagerCommands...")


class DataManagerCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.database_handler = DatabaseHandler("database.db")
        self.event_dict = {}
        self.functions = fc.Function()
        self.interval = 3600
        self.time_before_call_date = 900
        self.recall_event.change_interval(seconds=self.interval)
        self.has_changed_interval = False
        self.already_running = False
        self.recall_event.start()

    def cog_check(self, ctx):
        return self.functions.is_data_manager(ctx)

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
        print(len(event_unpack), "len")
        print(event_unpack)
        print(event_pack)
        self.database_handler.set_event(guild_id, event_pack)

        self.recall_event.change_interval(seconds=self.interval)
        self.has_changed_interval = False

        if self.recall_event.is_running:
            self.recall_event.restart()
        else:
            self.recall_event.start()

        await ctx.send("Evenement mis à jour.")

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

    def get_shortest_time(self, list_dict: list[dict], guild_id: int, maximum: int = 3600) -> float:
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

    @commands.command()
    async def setTimeBeforeCall(self, ctx, seconds):
        guild = ctx.guild
        guild_id = guild.id

        value = self.functions.reformat_type(seconds)
        if not isinstance(value, int):
            await ctx.send(f"Il faut un nombre, **{seconds}** n'est pas un nombre.")
            return

        if value < 900:
            await ctx.send("La valeur minimale est de **900** secondes, ce qui fait 15 minutes")
            value = 900

        self.database_handler.set_time_before_call(guild_id, value)
        self.recall_event.restart()
        await ctx.send("Temps d'envoit avant la date de l'évenement mis à jour.")

    @commands.command()
    async def setChannelEvent(self, ctx):
        guild = ctx.guild
        guild_id = guild.id

        channel_mentions = ctx.message.channel_mentions
        if len(channel_mentions) == 0:
            await ctx.send("Vous avez oublié la mention du salon textuel.")
            return
        elif len(channel_mentions) > 1:
            await ctx.send("Il ne faut qu'une seule mention de salon textuel.")

        channel_id = channel_mentions[0].id
        self.database_handler.set_event_channel(guild_id, channel_id)

        await ctx.send("Salon évenement mis à jour.")

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

    @commands.command()
    async def setAdCount(self, ctx, value):
        guild = ctx.guild
        guild_id = guild.id

        roles = ctx.message.role_mentions

        value = self.functions.reformat_type(value)

        if not isinstance(value, int):
            await ctx.send(f"La valeur '{value}' que vous avez renseigné n'est pas un nombre entier.")

        if len(roles) == 0:
            await ctx.send("Vous avez oublié la mention du ou des rôles.")
            return

        for role in roles:
            role_id = role.id
            self.database_handler.set_role_ad_value(role_id, guild_id, value)

        await ctx.send("Nombre d'annonces des rôles mis à jour.")

    @commands.command()
    async def setAdChannel(self, ctx):
        guild = ctx.guild
        guild_id = guild.id

        channel_mentions = ctx.message.channel_mentions
        if len(channel_mentions) == 0:
            await ctx.send("Vous avez oublié la mention du salon textuel.")
            return
        elif len(channel_mentions) > 1:
            await ctx.send("Il ne faut qu'une seule mention de salon textuel.")

        channel_id = channel_mentions[0].id
        self.database_handler.set_ad_channel(guild_id, channel_id)

        await ctx.send("Salon annonces mis à jour.")

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

    @commands.command()
    async def getAllChoice(self, ctx):
        guild = ctx.guild
        guild_id = guild.id

        user = ctx.author
        channel = await user.create_dm()
        users = self.database_handler.get_all_users(guild_id)

        say = f"__Choix du serveur **{guild.name}**__\n"
        for user in users:
            username = user["username"]
            count = len(username)
            space = 20 - count
            choice = user["choice"]
            if choice is None:
                choice = ""
            say += f"``{username}{' ' * space}`` : {choice}\n"
        await channel.send(say)

    @commands.command()
    async def getAllAvailability(self, ctx):
        guild = ctx.guild
        guild_id = guild.id

        user = ctx.author
        channel = await user.create_dm()
        users = self.database_handler.get_all_users(guild_id)

        say = f"__Disponibilités du serveur **{guild.name}**__\n"
        for user in users:
            username = user["username"]
            count = len(username)
            space = 20 - count
            choice = user["availability"]
            if choice is None:
                choice = ""
            say += f"``{username}{' ' * space}`` : {choice}\n"
        await channel.send(say)

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
            member_id = member_db["userId"]
            spe = member_db["speciality"]

            member_guild = guild.get_member(member_id)
            dictionary[spe].append(member_guild)

        await channel.send(f"__Spécialités du serveur **{guild.name}**__\n")
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

            say = f"Nombre de spécialité **{name}** : __{len(dictionary[key])}__\n"
            for member_dict in dictionary[key]:
                say += f"``{member_dict.name}``\n"
            await channel.send(say)

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

    def embed_event(self, event: dict, title: str ="Evenement", description: str ="Un évenement va bientôt commencer !",
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
