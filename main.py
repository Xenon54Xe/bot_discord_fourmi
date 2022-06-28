import discord
from discord.ext import commands, tasks
import os
import random
import asyncio

from BDD.database_handler import DatabaseHandler
from bot_discord_fourmi.functions import Function

database_handler = DatabaseHandler("database.db")
functions = Function()

"""
Création du bot
"""
intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix="-", description="Alpha- du bot :)", intents=intents)
bot.remove_command('help')

# dictionnaire qui contient toutes les aides
help_commands = {}

# affiché dans la description du bot
fun_fact = [
    "J'ai ai été créé en 2022",
    "Je suis spécialisé dans les fourmis",
    "Je gère ma propre fourmilière :)",
    "J'aime pas passer la serpillère",
    "Les fourmis de feu sont dangereuses",
    "Travailler en groupe c'est efficace",
    "Au secours ! On m'attaque !"
]


"""
Vérifications
"""


# vérifie que la commande effectuée soit dans le bon salon
def cmd_in_good_channel(ctx) -> bool:
    channel = ctx.channel
    if isinstance(channel, discord.DMChannel):
        return True

    guild = ctx.guild
    guild_id = guild.id

    cmd_channel_id = database_handler.get_guild(guild_id)["cmdChannelId"]
    cmd_channel = guild.get_channel(cmd_channel_id)

    if cmd_channel is None:
        return True
    else:
        msg = ctx.message
        channel_id = msg.channel.id

        if channel_id == cmd_channel_id:
            return True
        return False


# ajout de la vérification pour toutes les commandes du bot
bot.add_check(cmd_in_good_channel)


# vérifie si la commande est faite par le propriétaire du bot
def is_bot_owner(ctx):
    user_id = ctx.author.id
    return user_id == 753240790779691109


@bot.command()
@commands.check(is_bot_owner)
async def getSuggestion(ctx):
    for guild in bot.guilds:
        guild_id = guild.id

        suggestion_db = database_handler.get_guild(guild_id)["suggestion"]

        suggestion_list = []
        if suggestion_db != "" and suggestion_db:
            suggestion_list = functions.str_to_list(suggestion_db, functions.list_splitter)

        say = f"__**{guild.name}**__\n"
        if len(suggestion_list) > 0:
            for i in range(len(suggestion_list)):
                say += f"``{i+1} : {suggestion_list[i]}``\n"
        else:
            say += "Aucunes suggestions."

        await ctx.send(say)

    def check(msg):
        return msg.channel == ctx.channel and msg.author == ctx.author

    msg = await ctx.send("Voulez-vous modifier ces suggestions ? oui/non")
    while msg.content not in ("oui", "non"):
        try:
            msg = await bot.wait_for('message', check=check, timeout=60)
        except asyncio.TimeoutError:
            await ctx.send("Fin.")
            return

    if msg.content == "non":
        await ctx.send("Fin.")
        return

    guild_name = [i.name for i in bot.guilds]
    msg = await ctx.send("Donnez le nom du serveur dont vous voulez modifier les suggestions.")
    while msg.content not in guild_name:
        try:
            msg = await bot.wait_for('message', check=check, timeout=60)
        except asyncio.TimeoutError:
            await ctx.send("Fin.")
            return

    selected_guild = None
    for guild in bot.guilds:
        if msg.content == guild.name:
            selected_guild = guild
            break

    guild_id = selected_guild.id
    suggestions_db = database_handler.get_guild(guild_id)["suggestion"]
    suggestion_list = functions.str_to_list(suggestions_db)
    if len(suggestion_list) == 0:
        await ctx.send(f"Il n'y a aucune suggestion dans le serveur **{selected_guild.name}**.")
        return

    can_continue = True
    while can_continue:
        say = ""
        for i in range(len(suggestion_list)):
            say += f"**{i} : {suggestion_list[i]}**\n"
        await ctx.send(f"{say}"
                       f"Que voulez-vous supprimer ? Donnez des nombres entiers")

        msg = await bot.wait_for('message', check=check, timeout=60)
        nums_to_pop = functions.take_numbers(msg.content, to_int=True)

        suggests_to_remove = []
        for num in nums_to_pop:
            try:
                suggests_to_remove.append(suggestion_list[num])
            except:
                await ctx.send(f"La suggestion numéro __'{num}'__ n'existe pas.")

        for suggest_to_remove in suggests_to_remove:
            suggestion_list.remove(suggest_to_remove)

        await ctx.send("Suggestions supprimées.")

        msg = await ctx.send("Voulez-vous continuer ? oui/non")
        while msg.content not in ("oui", "non"):
            try:
                msg = await bot.wait_for('message', check=check, timeout=60)
            except asyncio.TimeoutError:
                can_continue = False
                continue

        if msg.content == "non":
            can_continue = False

    suggestion_str = functions.list_to_str(suggestion_list)
    database_handler.set_suggestion(guild_id, suggestion_str)

    await ctx.send("Suggestion managing terminé.")


@bot.command()
@commands.check(is_bot_owner)
async def load(ctx, name=None):
    if name in functions.list_all:
        load_all_cogs()
    else:
        try:
            bot.load_extension(f"cogs.{name}")
        except:
            print(f"Erreur: Problème dans le chargement de: '{name}'")
            return
    await ctx.send(f"Extension chargée")


@bot.command()
@commands.check(is_bot_owner)
async def unload(ctx, name=None):
    if name in functions.list_all:
        unload_all_cogs()
    else:
        try:
            bot.unload_extension(f"cogs.{name}")
        except():
            print(f"Erreur: Problème dans le déchargement de: '{name}'")
            return
    await ctx.send("Extension déchargée")


@bot.command()
@commands.check(is_bot_owner)
async def reload(ctx, name=None):
    if name in functions.list_all:
        load_all_cogs()
    else:
        try:
            bot.reload_extension(f"cogs.{name}")
        except:
            try:
                bot.load_extension(f"cogs.{name}")
            except:
                await ctx.send("Je n'ai pas compris quel extension je dois charger.")
                return
    await ctx.send("Extension rechargée")


# charge toutes les extensions
def load_all_cogs():
    cogs = os.listdir("cogs")
    for cog_name in cogs:
        if cog_name.endswith(".py") and cog_name != "__init__.py":
            try:
                bot.load_extension(f"cogs.{cog_name[:-3]}")
            except:
                bot.reload_extension(f"cogs.{cog_name[:-3]}")
    print("Cogs loaded")


# décharge toutes les extensions
def unload_all_cogs():
    cogs = os.listdir("cogs")
    for cog_name in cogs:
        if cog_name.endswith(".py") and cog_name != "__init__.py":
            try:
                bot.unload_extension(f"cogs.{cog_name[:-3]}")
            except:
                print(f"Erreur: Problème dans le déchargement de '{cog_name}'")
    print("Cogs loaded")


@bot.command()
@commands.check(is_bot_owner)
async def addHelp(ctx):
    p = os.path.abspath("help_command")
    with open(p, "r", encoding="UTF-8") as file:
        text = file.readlines()[0]
        current_dict = functions.str_to_dict(text)
        file.close()

    content: str = ctx.message.content
    name = functions.take_parts(content, " ", take_first=True)[0]
    value = content.replace(f'-addHelp {name} ', "")

    if name == "" or value == "":
        await ctx.send("Vous avez oublié le nom de la commande ou l'aide.")
        return

    find = False
    cmds = bot.commands
    for cmd in cmds:
        if cmd.name == name:
            find = True
            break

    cogs = list(bot.cogs)
    cogs.append("DefaultCommands")
    if not find:
        for cog in cogs:
            if cog == name:
                find = True
                break

    if not find:
        await ctx.send(f"La commande '{name}' n'a pas été trouvée.")
        return

    current_dict[name] = value
    string = functions.dict_to_str(current_dict)

    print(current_dict)

    with open(p, "w", encoding="UTF-8") as file:
        file.write(string)
        file.close()

    await ctx.send(f"Aide pour la commande __'{name}'__ mise à jour.")


@bot.command()
@commands.check(is_bot_owner)
async def reloadHC(ctx):
    reload_help_command()
    await ctx.send("Help_command rechargé.")



def reload_help_command():
    p = os.path.abspath("help_command")
    global help_commands
    with open(p, "r", encoding="UTF-8") as file:
        text = file.readlines()[0]
        help_commands = functions.str_to_dict(text)
        file.close()


@bot.command()
async def help(ctx, arg=None):
    if arg is not None:
        arg = functions.reformat_type(arg)
        if isinstance(arg, str):
            try:
                value = help_commands[arg]
                await ctx.send(value)
            except:
                await ctx.send(f"Il n'y a pas d'aides pour la commande **'{arg}'**")
            return

    cogs = bot.cogs
    cmds = bot.commands
    default_commands = "DefaultCommands"
    hide_commands = ["load", "unload", "reload", "reloadHC", "getSuggestion", "addHelp"]

    bot_dict = {}
    for cog in cogs:
        bot_dict[cog] = []
    bot_dict[default_commands] = []

    for cmd in cmds:
        try:
            bot_dict[cmd.cog_name].append(cmd.name)
        except:
            bot_dict[default_commands].append(cmd.name)

    order_dict = {
        "DefaultCommands": [
            ('load', ''),
            ('unload', ''),
            ('reload', ''),
            ('reloadHC', ''),
            ('getSuggestion', ''),
            ('help', 'Aide'),
            ('addHelp', '')
        ],

        "MemberCommands": [
            ('suggest', 'suggestion pour le bot'),
            ('setChoice', 'définir vos choix'),
            ('setAvailability', 'définir vos disponibilités'),
            ('setSpeciality', 'définir vos spécialités'),
            ('setAd', 'créer une annonce'),
            ('getAd', 'donne vos annonces'),
            ('delAd', 'supprimer une annonce'),
            ('getRoleMovable', 'donne les rôles attribuables'),
            ('addRole', 'vous donne un rôle'),
            ('removeRole', 'vous enlève un rôle')
        ],

        "DataManagerCommands": [
            ('addUser', 'ajoute un membre virtuel'),
            ('getUsername', 'donne le nom de tous les membres'),
            ('removeUser', 'supprime un membre virtuel'),
            ('setOtherData', "définir les données d'un autre membre"),
            ('setAdCount', "définir le nombre d'annonces qu'un rôle peut envoyer"),
            ('setAdChannel', 'définir le salon des annonces'),
            ('getAllChoice', 'donne tous les choix des joueurs'),
            ('getAllAvailability', 'donne toutes les disponibilités'),
            ('getAllSpeciality', 'donne toutes les spécialités'),
            ('reset', 'réinitialise les choix et les disponibilités')
        ],

        "EventCommands": [
            ('setEvent', 'créer un évenement'),
            ('getEvent', 'donne les évenements'),
            ('delEvent', 'supprime un évenement'),
            ('setRoleEvent', 'définir quel rôle est mentionné'),
            ('setChannelEvent', 'définir le salon des évenements'),
            ('setTimeBeforeCall', "définit quand est envoyé l'évenements"),
            ('getTime', 'donne votre décalage avec le temps utc'),
        ],

        "AdminCommands": [
            ('setRoleManager', 'définir le rôle data manager'),
            ('getRoleManager', 'donne le rôle data manager'),
            ('setCMDChannel', 'définir le salon des commandes'),
            ('setRoleMovable', 'définir les rôles movable')
        ],
    }

    if isinstance(arg, int):
        keys = list(order_dict.keys())
        try:
            choosen_key = keys[arg - 1]
        except:
            await ctx.send(f"La page '{arg}' n'existe pas. Il n'y en a que {len(keys)}")
            return

        try:
            x = help_commands[choosen_key]
            title = choosen_key
        except:
            title = f"{choosen_key} /!\\ "
        embed = discord.Embed(title=f"__**{title}**__", description="Une aide bienvenue !", colour=193095)
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
        embed.set_footer(text="Faites -help <nom_de_la_commande> pour plus de précisions")

        cmds = order_dict[choosen_key]
        try:
            bot_cmds = bot_dict[choosen_key]
        except:
            await ctx.send(f"La clé '{choosen_key}' n'est pas la même dans le order_dict et le bot_dict")
            return

        value = ""
        for cmd in cmds:
            count = len(cmd[0])
            nb_of_space = 20 - count
            if cmd[0] in hide_commands:
                continue
            try:
                x = help_commands[cmd[0]]
                value += f"``'{cmd[0]}'{' ' * nb_of_space}`` | **{cmd[1]}**\n"
            except:
                value += f"``'{cmd[0]}'{' ' * nb_of_space}`` | **{cmd[1]}** __ /!\\ __\n"
        value = value[:-1]
        if len(cmds) != len(bot_cmds):
            name = f"**Commandes**: __ /!\\ __"
        else:
            name = "**Commandes:**"
        embed.add_field(name=name, value=value)

        await ctx.send(embed=embed)

    else:
        embed = discord.Embed(title="__**HELP**__", description="Vous avez demandé de l'aide ?", colour=193095)
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)

        pages = list(order_dict.keys())
        value = ""
        for i in range(len(pages)):
            try:
                x = help_commands[pages[i]]
                value += f"``{i + 1} : {pages[i]}``\n"
            except:
                value += f"``{i + 1} : {pages[i]}`` __/!\\ __\n"
        value += "__Pour cela faite -help <numéro de la page>__"
        embed.add_field(name=f"Vous pouvez choisir entre {len(pages)} pages d'aide.",
                        value=value)

        await ctx.send(embed=embed)


# quand le bot est lancé
@bot.event
async def on_ready():
    change_status.start()
    guilds = bot.guilds
    for guild in guilds:
        functions.update_guild(guild)
        functions.update_members(guild)
        functions.update_roles(guild)
    load_all_cogs()
    reload_help_command()
    print("Ready")


# boucle qui change le statut du bot toutes les 5 min
@tasks.loop(minutes=5)
async def change_status():
    choice = random.choice(fun_fact)
    game = discord.Game(f"-help | {choice}")
    await bot.change_presence(status=discord.Status.dnd, activity=game)


# les erreures des commandes reload, load, unload, reloadHC se retrouvent ici
@load.error
@unload.error
@reload.error
@reloadHC.error
async def loading_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send("Vous ne pouvez pas utiliser la commande de l'être sûprème !")


# les erreures de toutes les commandes du bot se retrouvent ici
@bot.event
async def on_command_error(ctx, error):
    guild = ctx.guild
    guild_id = guild.id

    if isinstance(error, commands.CheckFailure):
        channel_cmd = guild.get_channel(database_handler.get_guild(guild_id)["cmdChannelId"])

        if channel_cmd:
            user_msg = ctx.message
            await user_msg.delete()
            bot_msg = await ctx.send(f"Vous n'avez pas fais la commande dans le bon salon : {channel_cmd.mention}")
            await bot_msg.delete(delay=20)
        else:
            await ctx.send("Vous n'avez pas les permissions pour utiliser cette commande.")

    elif isinstance(error, commands.CommandNotFound):
        await ctx.send("Je ne connais pas cette commande.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Vous avez oublié l'argument.")
    else:
        raise error

# démarrage du bot
token = "OTgyNzIyODMzNTE4MDYzNjM2.GgNPoh.QBUzkETAsfqLhkoqVIHT-Kc2YCID8huAiD4uiA"
try:
    bot.run(token)
except Exception as exc:
    print("Pas de co ?")
    raise exc
