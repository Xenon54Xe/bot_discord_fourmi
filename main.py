import discord
from discord.ext import commands, tasks
import os
import random
import asyncio

import BDD.database_handler as db
import functions as fc

database_handler = db.DatabaseHandler("database.db")
functions = fc.Function()

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
    "Au secours ! On m'attaque !",
    "Please be good with me",
    "I love burn ant with a magnifying glass ! (in the game of course)",
    "I can't help you fight ant but i can help you manage your alliance",
    "I've never taste a ice cream ;(",
    "My ant queen is level 23",
    "During winter i love eat raclette",
    "My creators are the best !"
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
    if user_id == 753240790779691109 or user_id == 587604292240670720:
        return True


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
    cogs = os.listdir("cogs")  # bug d'appel des cogs
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


# ajoute une aide
@bot.command()
@commands.check(is_bot_owner)
async def addHelp(ctx):
    p = os.path.abspath("help_command")
    with open(p, "r", encoding="UTF-8") as file:
        text = file.readlines()[0]
        current_dict = functions.str_to_dict(text, auto_reformat=False)
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

    with open(p, "w", encoding="UTF-8") as file:
        file.write(string)
        file.close()

    await ctx.send(f"Aide pour la commande __'{name}'__ mise à jour.")


# commande qui met à jour les aides
@bot.command()
@commands.check(is_bot_owner)
async def reloadHC(ctx):
    clean_help_command()
    await ctx.send("Help_command rechargé.")


def clean_help_command():
    p = os.path.abspath("help_command")
    with open(p, "r", encoding="UTF-8") as file:
        text = file.readlines()[0]
        last_help_command = functions.str_to_dict(text, auto_reformat=False)
        file.close()

    ctg = [key for key in bot.cogs.keys()]
    ctg.append("DefaultCommands")
    cmd = [i.name for i in bot.commands]
    list_to_search = ctg + cmd

    cleaned_help_command = {}
    for key in last_help_command.keys():
        if key in list_to_search:
            value = last_help_command[key]
            cleaned_help_command[key] = value

    global help_commands
    help_commands = cleaned_help_command

    help_commands_str = functions.dict_to_str(cleaned_help_command)

    with open(p, "w", encoding="UTF-8") as file:
        file.write(help_commands_str)
        file.close()


# commande help
@bot.command()
async def help(ctx, arg=None):
    try:
        arg = int(arg)
    except:
        pass

    if arg is not None:
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
            ('setPercentage', 'définir vos pourcentages'),
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
            ('getAllChoice', 'donne tous les choix des joueurs'),
            ('getAllAvailability', 'donne toutes les disponibilités'),
            ('getAllSpeciality', 'donne toutes les spécialités'),
            ('getAllPercentage', 'donne tous les pourcentages'),
            ('getData', 'donne les données du serveur'),
            ('reset', 'réinitialise les choix et les disponibilités')
        ],

        "EventCommands": [
            ('setEvent', 'créer un évenement'),
            ('getEvent', 'donne les évenements'),
            ('delEvent', 'supprime un évenement'),
            ('setRoleEvent', 'définir quel rôle est mentionné'),
            ('setTimeBeforeCall', "définit quand est envoyé l'évenements"),
            ('getTime', 'donne votre décalage avec le temps utc'),
        ],

        "AdminCommands": [
            ('prerequisite', 'donne les prérequis du bot'),
            ('setChannelCMD', 'définir le salon des commandes'),
            ('setChannelEvent', 'définir le salon des évenements'),
            ('setChannelAd', 'définir le salon des annonces'),
            ('setRoleManager', 'définir le rôle data manager'),
            ('getRoleManager', 'donne le rôle data manager'),
            ('setRoleMovable', 'définir les rôles movable')
        ],
    }

    warning = functions.warning
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
            if nb_of_space < 0:
                nb_of_space = 0
            if cmd[0] in hide_commands:
                continue
            try:
                x = help_commands[cmd[0]]
                value += f"``'{cmd[0]}'{' ' * nb_of_space}`` |ㅤ**{cmd[1]}**\n"
            except:
                value += f"``'{cmd[0]}'{' ' * nb_of_space}`` |ㅤ**{cmd[1]}** {warning}\n"
        value = value[:-1]

        if len(cmds) > len(bot_cmds):
            name = "**Commandes**: Il y a trop de commandes"
        elif len(cmds) < len(bot_cmds):
            name = "**Commandes**: Il manque des commandes"
        else:
            name = "**Commandes**:"
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
                value += f"``{i + 1} : {pages[i]}`` {warning}"
        value += "__Pour cela faite -help <numéro de la page>__"
        embed.add_field(name=f"Vous pouvez choisir entre {len(pages)} pages d'aide.",
                        value=value)

        await ctx.send(embed=embed)


# met à jour le serveur
def update_guild(guild: discord.guild):
    guild_id = guild.id
    if database_handler.guild_exists_with(guild_id):
        database_handler.update_guild(guild_id, guild.name)
    else:
        database_handler.add_guild(guild_id, guild.name)


# met à jour les utilisateurs d'un serveur
def update_members(guild: discord.Guild):
    members = guild.members
    guild_id = guild.id

    for member in members:
        if member.bot is False:
            if database_handler.user_exists_with(member.id, guild_id):
                database_handler.update_user(member.id, guild_id, member.display_name)
            else:
                database_handler.add_user(member.id, guild_id, member.display_name)
        else:
            try:
                database_handler.remove_user(member.id, guild_id)
            except:
                pass

    members_db = database_handler.get_all_users(guild_id)
    for member_db in members_db:
        member_db_id = member_db["userId"]
        if member_db_id == -1:
            continue

        found = False
        for member in members:
            if member.id == member_db_id:
                found = True
                break
        if not found:
            database_handler.remove_user(member_db_id, guild_id)


# met à jour les rôles d'un serveur
def update_roles(guild: discord.Guild):
    roles = guild.roles
    guild_id = guild.id

    for role in roles:
        if role.name != "@everyone" and role.is_bot_managed() is False:
            if database_handler.role_exists_with(role.id, guild_id):
                database_handler.update_role(role.id, guild_id, role.name)
            else:
                database_handler.add_role(role.id, guild_id, role.name)
        else:
            try:
                database_handler.remove_role(role.id, guild_id)
            except:
                pass

    roles_db = database_handler.get_all_roles(guild_id)
    for role_db in roles_db:
        role_db_id = role_db["roleId"]
        found = False
        for role in roles:
            if role.id == role_db_id:
                found = True
                break
        if not found:
            database_handler.remove_role(role_db_id, guild_id)


# quand le bot est lancé
@bot.event
async def on_ready():
    change_status.start()
    guilds = bot.guilds
    for guild in guilds:
        update_guild(guild)
        update_members(guild)
        update_roles(guild)
    load_all_cogs()
    clean_help_command()
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


# les erreurs de toutes les commandes du bot se retrouvent ici
@bot.event
async def on_command_error(ctx, error):
    guild = ctx.guild
    guild_id = guild.id

    channel = ctx.channel

    if isinstance(error, commands.CheckFailure):
        channel_cmd = guild.get_channel(database_handler.get_guild(guild_id)["cmdChannelId"])

        if channel_cmd and channel != channel_cmd:
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
token = "___token___"
try:
    bot.run(token)
except Exception as exc:
    raise exc
