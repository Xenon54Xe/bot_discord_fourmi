import calendar
import time
from os import path

import discord

from bot_discord_fourmi.BDD.database_handler import DatabaseHandler


class Function:
    def __init__(self):
        self.database_handler = DatabaseHandler("database.db")
        self.path = path.abspath("")
        self.list_true = ['True', 'yes', 'y', 'true', 't', '1', 'enable', 'on', 'oui', 'vrai']
        self.list_false = ['False', 'no', 'n', 'false', 'f', '0', 'disable', 'off', 'non', 'faux']
        self.list_all = ['all', 'a', 'everything', 'e', 'tout']
        self.list_none = ['None', 'none', '0', '', 'null', '']
        self.quote = ["'", "\""]
        self.value_splitter = "/v:"
        self.dict_splitter = "/d:"
        self.list_splitter = "/l:"
        self.event_keys = ["date", "event", "organisation", "permanent", "interval"]

    def take_parts(self, string: str, marker: str, take_first: bool = False) -> list[str]:
        founded_pos = []
        for i in range(len(string)):
            find_marker = ""
            if string[i] == marker[0]:
                for i_f in range(i, i + len(marker)):
                    if i_f > len(string) - 1:
                        break
                    find_marker += string[i_f]
                if find_marker == marker:
                    founded_pos.append(i + len(marker))

        if len(founded_pos) < 2:
            raise Exception(1, "Il manque les marqueurs !")
        elif int(len(founded_pos) / 2) != len(founded_pos) / 2 and not take_first:
            raise Exception(2, "Il n'y a pas un nombre pair de marqueurs !")

        parts = []
        time = 0
        while time < len(founded_pos):
            first_pos = founded_pos[time]
            second_pos = founded_pos[time + 1]
            text = ""
            for i in range(first_pos, second_pos - len(marker)):
                text += string[i]
            parts.append(text)
            time += 2
            if take_first:
                break

        return parts

    def find(self, string: str, target: str) -> list[tuple]:
        founded_pos = []
        for i in range(len(string)):
            find_target = ""
            if string[i] == target[0]:
                for i_f in range(i, i + len(target)):
                    if i_f > len(string) - 1:
                        break
                    find_target += string[i_f]
                if find_target == target:
                    founded_pos.append((i, i + len(target)))

        return founded_pos

    def take_numbers(self, string: str, to_int: bool = False):
        numbers = ""
        num = ""
        for letter in string:
            try:
                int(letter)
                num += letter
            except:
                if num != "":
                    numbers += f"{num} "
                    num = ""
        if num != "":
            numbers += num
        else:
            numbers = numbers[:-1]

        if numbers == "":
            raise Exception("No integer was found")

        if to_int:
            numbers = numbers.split(" ")
            return [self.reformat_type(i) for i in numbers]
        return numbers

    def dict_to_str(self, dictionary: dict, value_splitter: str = "/v:", dict_splitter: str = "/d:") -> str:
        string = ""
        for key in dictionary:
            value = dictionary[key]
            string += f"{key}{value_splitter}{value}{dict_splitter}"
        string = string[:-len(dict_splitter)]
        return string

    def str_to_dict(self, string: str, value_splitter: str = "/v:", dict_splitter: str = "/d:", auto_reformat=True) \
            -> dict:
        dictionary = {}
        if string == "":
            return {}

        try:
            sheets = string.split(dict_splitter)
        except:
            raise TypeError(f"'{string}' type is '{type(string)}' not str (str_to_dict)")

        for sheet in sheets:
            parts = sheet.split(value_splitter)
            if len(parts) == 1:
                raise Exception(f"Marker: Marqueur '{value_splitter}' introuvable dans '{sheet}'")

            key = self.reformat_type(parts[0])
            if auto_reformat:
                value = self.reformat_type(parts[1])
            else:
                value = parts[1]

            dictionary[key] = value
        return dictionary

    def list_to_str(self, list_: list, list_splitter: str = "/l:") -> str:
        string = ""
        if not isinstance(list_, list):
            raise TypeError(f"'{list_}' is '{type(list_)}' not list")
        for i in list_:
            string += f"{i}{list_splitter}"
        string = string[:-len(list_splitter)]
        return string

    def str_to_list(self, string: str, list_splitter: str = "/l:", auto_reformat: bool = True) -> list:
        if string is None or string == "":
            return []

        try:
            list = string.split(list_splitter)
        except:
            raise TypeError(f"'{string}' type is '{type(string)}' not str (str_to_list)")
        new_list = []
        for i in list:
            if auto_reformat:
                i = self.reformat_type(i)
            new_list.append(i)
        return new_list

    def pack_list_dict_to_str(self, list: list[dict], value_splitter: str = "/v:", dict_splitter: str = "/d:",
                              list_splitter: str = "/l:") -> str:
        try:
            list_dict_str = []
            for case in list:
                new_dict_str = self.dict_to_str(case, value_splitter, dict_splitter)
                list_dict_str.append(new_dict_str)
            return self.list_to_str(list_dict_str, list_splitter)
        except Exception as exc:
            raise exc

    def unpack_str_to_list_dict(self, string: str = None, value_splitter: str = "/v:", dict_splitter: str = "/d:",
                                list_splitter: str = "/l:") -> list[dict]:
        if string is None or string == "":
            return []

        try:
            current_list = self.str_to_list(string, list_splitter, auto_reformat=False)
            new_list = []
            for case in current_list:
                new_dict = self.str_to_dict(case, value_splitter, dict_splitter)
                new_list.append(new_dict)
            return new_list
        except Exception as exc:
            raise exc

    def pack_dict_list_to_str(self, dictionary: dict[int: list], value_splitter: str = "/v:", dict_splitter: str = "/d:",
                              list_splitter: str = "/l:") -> str:
        try:
            new_dict = {}
            for key in dictionary.keys():
                current_list = dictionary[key]
                new_dict[key] = self.list_to_str(current_list, list_splitter)
            return self.dict_to_str(new_dict, value_splitter, dict_splitter)
        except Exception as exc:
            raise exc

    def unpack_str_to_dict_list(self, string: str, value_splitter: str = "/v:", dict_splitter: str = "/d:",
                              list_splitter: str = "/l:") -> dict[int: list]:
        try:
            new_dict = self.str_to_dict(string, value_splitter, dict_splitter, auto_reformat=False)
            for key in new_dict.keys():
                value = new_dict[key]
                new_dict[key] = self.str_to_list(value, list_splitter)
            return new_dict
        except Exception as exc:
            raise exc

    def take_date(self, string: str) -> float:
        if self.in_format_date(string):
            date = self.take_numbers(string)
            date_struct = time.strptime(date, "%d %m %Y %H %M %S")
            date_float = calendar.timegm(date_struct)
            return date_float
        else:
            raise Exception(f"String not in format '%d %m %Y %H %M %S' : '{string}'")

    def in_format_date(self, string: str) -> bool:
        try:
            date = self.take_numbers(string)
            date_struct = time.strptime(date, "%d %m %Y %H %M %S")
            date_float = calendar.timegm(date_struct)
            return True
        except:
            return False

    def reformat_type(self, string: str) -> vars:
        if string == "True":
            return True
        elif string == "False":
            return False
        elif string == "None":
            return None
        try:
            x = eval(string)
            if isinstance(x, int) or isinstance(x, float):
                return x
        except:
            pass
        try:
            return self.take_numbers(string, to_int=True)
        except:
            return string

    def take_date_from_struct(self, struct: time.struct_time) -> list:
        year = struct.tm_year
        month = struct.tm_mon
        day = struct.tm_mday
        hour = struct.tm_hour
        minutes = struct.tm_min
        sec = struct.tm_sec
        return [year, month, day, hour, minutes, sec]

    def update_members(self, guild: discord.guild):
        guild_id = guild.id
        members = guild.members
        for member in members:
            user_id = member.id
            if member.bot:
                self.database_handler.delete_user(user_id, guild_id)
            else:
                username = member.display_name
                self.database_handler.create_user(user_id, guild_id, username)

        users_db = self.database_handler.get_all_users(guild_id)
        for user_db in users_db:
            user_db_id = user_db["userId"]
            delete = True
            for member in members:
                user_guild_id = member.id
                if user_guild_id == user_db_id:
                    delete = False
                    break
            if delete:
                self.database_handler.delete_role(user_db_id, guild_id)

    def update_roles(self, guild: discord.guild):
        roles = guild.roles
        guild_id = guild.id
        roles_to_add = []
        roles_to_pop = []
        print(guild.name)
        print(roles)
        for role in roles:
            role_id = role.id
            role_name = role.name
            if role.is_bot_managed() or role_name == "@everyone":
                roles_to_pop.append(role)
            else:
                roles_to_add.append(role)
        print("pop", roles_to_pop)
        print("add", roles_to_add)

        for role in roles_to_add:
            role_id = role.id
            role_name = role.name
            self.database_handler.create_role(role_id, guild_id, role_name)
        for role in roles_to_pop:
            role_id = role.id
            self.database_handler.delete_role(role_id, guild_id)

        roles_db = self.database_handler.get_all_roles(guild_id)
        print("####Roles DB ####")
        for role_db in roles_db:
            print(role_db)
            role_db_id = role_db["roleId"]
            found = False
            for role_guild in roles:
                role_guild_id = role_guild.id
                if role_guild_id == role_db_id:
                    print("found", role_guild.name)
                    found = True
                    break
            if found is False:
                self.database_handler.delete_role(role_db_id, guild_id)

    def update_guild(self, guild: discord.guild):
        self.database_handler.create_guild(guild.id, guild.name)

    def is_data_manager(self, ctx):
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
