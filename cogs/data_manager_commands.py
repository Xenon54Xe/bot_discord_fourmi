import discord
from discord.ext import commands, tasks
import sys
import time
from os import path

p = path.abspath(".")
sys.path.insert(1, p)

import BDD.database_handler as dbh
import functions as fc


def setup(bot):
    bot.add_cog(DataManagerCommands(bot))
    print("Loading DataManagerCommands...")


class DataManagerCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.database_handler = dbh.DatabaseHandler("database.db")
        self.event_dict = {}
        self.functions = fc.Function()

    def cog_check(self, ctx):
        member = ctx.author
        is_admin = member.guild_permissions.administrator
        if is_admin:
            return True

        guild_id = ctx.guild.id
        roles = member.roles
        for role in roles:
            role_id = role.id
            manager = self.database_handler.get_role(role_id, guild_id)["dataManager"]
            if manager:
                return True
        return False

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
        self.database_handler.set_channel_event(guild_id, channel_id)

        await ctx.send("Salon évent mis à jour.")

    @commands.command()
    async def setEvent(self, ctx, *, event: str):
        guild = ctx.guild
        guild_id = guild.id

        date_str = self.functions.take_parts(event, "'")  # vérifier que ça marche
        date_used = self.functions.take_numbers(date_str[0])

        try:
            date_struct = time.strptime(date_used, "%d %m %Y %H %M %S")
        except Exception as exc:
            print(exc)
            date_float = 0
        else:
            date_float = time.mktime(date_struct)

        db_event_str: str = self.database_handler.get_guild(guild_id)["event"]
        if db_event_str != "":
            event_lib = self.functions.str_to_dict(db_event_str, self.functions.first_splitter, self.functions.second_splitter)
        else:
            event_lib = {}
        event_lib[date_float] = event

        total_event = self.functions.dict_to_str(event_lib, self.functions.first_splitter, self.functions.second_splitter)

        self.database_handler.set_event(guild_id, total_event)
        self.recall_event.start()

    @tasks.loop(seconds=10)
    async def recall_event(self):
        guilds = self.bot.guilds
        remaining_events = 0

        for guild in guilds:
            guild_id = guild.id
            channel_id = self.database_handler.get_guild(guild_id)["channelEventId"]
            print(f"channelId = {channel_id}")
            channel = guild.get_channel(channel_id)
            if channel is None:
                channel = guild.text_channels[0]
                self.database_handler.set_channel_event(guild_id, channel.id)

            db_event = self.database_handler.get_guild(guild_id)["event"]
            event_lib = self.functions.str_to_dict(db_event, self.functions.first_splitter, self.functions.second_splitter)

            current_time = time.time()
            keys_to_pop = []
            for key in event_lib.keys():
                if float(key) <= current_time:
                    """
                    Affichage de l'event
                    """
                    await channel.send(event_lib[key])

                    keys_to_pop.append(key)
                else:
                    print(float(key) - current_time)

            for i in keys_to_pop:
                event_lib.pop(i)

            new_event_str = self.functions.dict_to_str(event_lib, self.functions.first_splitter, self.functions.second_splitter)
            self.database_handler.set_event(guild_id, new_event_str)

            if len(event_lib) > 0:
                remaining_events += 1

        if remaining_events == 0:
            self.recall_event.stop()

    @commands.command()
    async def getAllChoice(self, ctx):
        guild = ctx.guild
        guild_id = guild.id

        user = ctx.author
        channel = await user.create_dm()
        users = self.database_handler.get_all_users(guild_id)

        say = "__Choix__\n"
        for user in users:
            username = user["username"]
            choice = user["choice"]
            if choice is None:
                choice = ""
            say += f"{username} : {choice}\n"
        await channel.send(say)

    @commands.command()
    async def getAllAvailability(self, ctx):
        guild = ctx.guild
        guild_id = guild.id

        user = ctx.author
        channel = await user.create_dm()
        users = self.database_handler.get_all_users(guild_id)

        say = "__Disponibilités__\n"
        for user in users:
            username = user["username"]
            choice = user["availability"]
            if choice is None:
                choice = ""
            say += f"{username} : {choice}\n"
        await channel.send(say)
