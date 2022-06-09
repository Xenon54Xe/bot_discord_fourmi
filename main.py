import discord
from discord.ext import commands, tasks
import os
from BDD.database_handler import DatabaseHandler
import random

database_handler = DatabaseHandler("database.db")

intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix="-", description="Alpha- du bot :)", intents=intents)
bot.remove_command('help')

help_commands = {}

fun_fact = [
    "J'ai ai été créé en 2022",
    "Je suis spécialisé dans les fourmis",
    "Je gère ma propre fourmilière :)",
    "J'aime pas passer la serpillère",
    "Les fourmis de feu sont dangereuses",
    "Travailler en groupe c'est efficace",
    "Au secours ! On m'attaque !"
]


def is_bot_owner(ctx):
    user_id = ctx.author.id
    return user_id == 753240790779691109


@bot.command()
@commands.check(is_bot_owner)
async def load(ctx, name=None):
    if name:
        try:
            bot.load_extension(f"cogs.{name}")
        except:
            print(f"Erreur: Problème dans le chargement de: '{name}'")
            return
    await ctx.send(f"Extension chargée")


@bot.command()
@commands.check(is_bot_owner)
async def unload(ctx, name=None):
    if name:
        try:
            bot.unload_extension(f"cogs.{name}")
        except():
            print(f"Erreur: Problème dans le déchargement de: '{name}'")
            return
    await ctx.send("Extension déchargée")


@bot.command()
@commands.check(is_bot_owner)
async def reload(ctx, name=None):
    if name:
        try:
            bot.reload_extension(f"cogs.{name}")
        except:
            try:
                bot.load_extension(f"cogs.{name}")
            except:
                print(f"Erreur: Problème dans le rechargement de: '{name}'")
                return
    await ctx.send("Extension rechargée")


@bot.command()
@commands.check(is_bot_owner)
async def reloadHC(ctx):
    reload_help_command()
    await ctx.send("Help_command rechargé.")


@bot.command()
async def help(ctx, cmd=None):
    if cmd:
        try:
            say = help_commands[cmd]
            await ctx.send(say)
        except:
            await ctx.send(f"Il n'y a pas d'aides pour la commande {cmd}")
        return

    cogs = bot.cogs
    ctgs = {}
    keys = []
    hide_commands = ["load", "unload", "reload", "reloadHC"]
    default_commands = "DefaultCommands"

    for cog in cogs:
        ctgs[cog] = []
        keys.append(cog)
    ctgs[default_commands] = []
    keys.append(default_commands)

    cmds = bot.commands
    for cmd in cmds:
        name = cmd.name
        cog_name = cmd.cog_name
        if cog_name is None:
            cog_name = default_commands
        if name not in hide_commands:
            ctgs[cog_name].append(name)

    embed = discord.Embed(title="**Help**", description="Vous avez demandé de l'aide ?", colour=193095)
    embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)

    for i in range(len(keys)):
        ctg_name = keys[i]
        say = ""

        if len(ctgs[ctg_name]) == 0:
            continue

        for cmd_name in ctgs[ctg_name]:
            say += f"``{cmd_name}``"

            try:
                help_commands[cmd_name]
            except:
                if cmd_name != "help":
                    say += "/!\\"

            say += "\n"
        embed.add_field(name=ctg_name, value=say, inline=False)

    embed.set_footer(text="Faites -help <nom_de_la_commande> pour plus de précisions")
    try:
        await ctx.send(embed=embed)
    except:
        await ctx.send("Bug dans l'envoit de l'embed")


def update_members(guild: discord.guild):
    guild_id = guild.id
    members = guild.members
    for member in members:
        user_id = member.id
        username = member.display_name
        if member.id != bot.user.id:
            database_handler.create_user(user_id, guild_id, username)

    users_db = database_handler.get_all_users(guild_id)
    for user_db in users_db:
        user_db_id = user_db["userId"]
        delete = True
        for member in members:
            user_guild_id = member.id
            if user_guild_id == user_db_id:
                delete = False
                break
        if delete:
            database_handler.delete_role(user_db_id, guild_id)


def update_roles(guild: discord.guild):
    roles = guild.roles
    guild_id = guild.id
    for role in roles:
        role_id = role.id
        role_name_db = role.name
        database_handler.create_role(role_id, guild_id, role_name_db)

    roles_db = database_handler.get_all_roles(guild_id)
    for role_db in roles_db:
        role_db_id = role_db["roleId"]
        delete = True
        for role_guild in roles:
            role_guild_id = role_guild.id
            if role_guild_id == role_db_id:
                delete = False
                break
        if delete:
            database_handler.delete_role(role_db_id, guild_id)


def update_guild(guild: discord.guild):
    database_handler.create_guild(guild.id, guild.name)


def load_all_cogs():
    cogs = os.listdir("cogs")
    for cog_name in cogs:
        if cog_name.endswith(".py") and cog_name != "__init__.py":
            bot.load_extension(f"cogs.{cog_name[:-3]}")
    print("Cogs loaded")


def reload_help_command():
    p = os.path.abspath("help_command")
    help_commands.clear()
    with open(p, "r", encoding="UTF-8") as file:
        cmds = file.readlines()
        for cmd in cmds:
            try:
                cmd_list = cmd.split(":")
            except:
                print(f"Problème de définition de commande : '{cmd}'")
                continue
            if len(cmd_list) > 2:
                print(f"Il ne faut pas qu'il y ait plus de 1 fois ':' par ligne ({cmd})")
                continue
            first_part = cmd_list[0]
            second_part = cmd_list[1]
            if second_part.startswith(" "):
                second_part = second_part[1:]
            if second_part.endswith("\n"):
                second_part = second_part[:-1]
            help_commands[first_part] = second_part
        file.close()


@bot.event
async def on_ready():
    change_status.start()
    guilds = bot.guilds
    for guild in guilds:
        update_roles(guild)
        update_guild(guild)
        update_members(guild)
    load_all_cogs()
    reload_help_command()
    print("Ready")


@bot.event
async def on_guild_join(guild):
    update_roles(guild)
    update_members(guild)
    update_guild(guild)


@tasks.loop(minutes=1)
async def change_status():
    choice = random.choice(fun_fact)
    game = discord.Game(f"-help | {choice}")
    await bot.change_presence(status=discord.Status.dnd, activity=game)


@reloadHC.error
@load.error
@unload.error
@reload.error
async def loading_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send("Vous ne pouvez pas utiliser la commande de l'être sûprème !")


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("Je ne connais pas cette commande.")

    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Il manque un argument.")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("Vous n'avez pas les permissions pour faire cette commande.")
    elif isinstance(error.original, discord.Forbidden):
        await ctx.send("Oups, je n'ai pas le droit de faire ça, il me manque les permissions.")

token = "OTgyNzIyODMzNTE4MDYzNjM2.GpANVJ.Tcm3ZlC8fJeXyIB_cTMBrUBYmjz3BEtBGb2ObI"
bot.run(token)

""" Exemple Embed
@bot.command()
async def ban(ctx, user: discord.User, *reason):
    reason = ' '.join(reason)
    #await ctx.guild.ban(user, reason=reason)
    embed = discord.Embed(title="**Banissement**", description="Un modérateur à frappé!", url="https://fr.wikipedia.org/wiki/Tableau_p%C3%A9riodique_des_%C3%A9l%C3%A9ments")
    embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
    embed.set_thumbnail(url="https://www.goclecd.fr/wp-content/uploads/189-1893196_banhammer-v2-ban-hammer-png.png")
    embed.add_field(name="Mambre banni", value=user.name)
    embed.add_field(name="Raison", value=reason)
    embed.add_field(name="Modérateur", value=ctx.author.name)
    embed.set_footer(text=random.choice(fun_fact))

    await ctx.send(embed=embed)
"""