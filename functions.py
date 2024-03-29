import calendar
import time
from os import path

import discord


class Function:
    def __init__(self):
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
        self.user_data_name = ["choice", "availability", "speciality", "percentage"]
        self.user_speciality = ["cac", "vel", "tir"]
        self.user_data_percentage = ["army"] + self.user_speciality
        self.user_type = ["normal", "virtual"]
        self.warning = "__**/!\\ **__"
        self.max_text_length = 80

    # retourne tout ce qui est entre les balises
    def take_parts(self, string: str, marker: str, take_first: bool = False) -> [str]:
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

    def take_parts_with_numbers(self, string: str, list: [tuple]) -> [str]:
        new_list = []
        for tpl in list:
            text = ""
            for i in range(tpl[0], tpl[1]):
                text += string[i]
            new_list.append(text)
        return new_list

    # retourne un texte dans lequel il y a tous les nombres séparés par un espace
    # ou retourne une liste de tous les nombres
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
            return [int(i) for i in numbers]
        return numbers

    # retourne la date sous forme de float depuis epoch
    def take_date(self, string: str) -> float:
        if self.is_format_date(string):
            date = self.take_numbers(string)
            date_struct = time.strptime(date, "%d %m %Y %H %M %S")
            date_float = calendar.timegm(date_struct)
            return date_float
        else:
            raise Exception(f"String not in format '%d %m %Y %H %M %S' : '{string}'")

    # retourne une liste contenant l'année, le mois, le jour, l'heure, la minute et la seconde
    def take_date_from_struct(self, struct: time.struct_time) -> list:
        year = struct.tm_year
        month = struct.tm_mon
        day = struct.tm_mday
        hour = struct.tm_hour
        minutes = struct.tm_min
        sec = struct.tm_sec
        return [year, month, day, hour, minutes, sec]

    # retourne la/les position(s) de début et de fin de la cible
    def find(self, string: str, target: str) -> [tuple]:
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

    # retourne le type d'un texte, str si pas trouvé
    def reformat_type(self, string: str) -> vars:
        if string == "True":
            return True
        elif string == "False":
            return False
        elif string == "None":
            return None
        try:
            x = int(string)
            y = float(string)
            if x == y:
                return x
            else:
                return y
        except:
            return string

    # retourne un texte qui peux être converti en dict
    def dict_to_str(self, dictionary: dict, value_splitter: str = "/v:", dict_splitter: str = "/d:") -> str:
        string = ""
        for key in dictionary:
            value = dictionary[key]
            string += f"{key}{value_splitter}{value}{dict_splitter}"
        string = string[:-len(dict_splitter)]
        return string

    # retourne un dictionnaire depuis un texte
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

    # retourne un texte qui pourrait être converti en dictionnaire de listes
    def pack_dict_list_to_str(self, dictionary: dict, value_splitter: str = "/v:", dict_splitter: str = "/d:",
                              list_splitter: str = "/l:") -> str:
        try:
            new_dict = {}
            for key in dictionary.keys():
                current_list = dictionary[key]
                new_dict[key] = self.list_to_str(current_list, list_splitter)
            return self.dict_to_str(new_dict, value_splitter, dict_splitter)
        except Exception as exc:
            raise exc

    # retourne un dictionnaire de listes depuis un texte
    def unpack_str_to_dict_list(self, string: str, value_splitter: str = "/v:", dict_splitter: str = "/d:",
                              list_splitter: str = "/l:") -> dict:
        if string == "" or string is None:
            return {}
        try:
            new_dict = self.str_to_dict(string, value_splitter, dict_splitter, auto_reformat=False)
            for key in new_dict.keys():
                value = new_dict[key]
                new_dict[key] = self.str_to_list(value, list_splitter)
            return new_dict
        except Exception as exc:
            raise exc

    # retourne un texte qui pourrait être converti en liste
    def list_to_str(self, list_: list, list_splitter: str = "/l:") -> str:
        string = ""
        if not isinstance(list_, list):
            raise TypeError(f"'{list_}' is '{type(list_)}' not list")
        for i in list_:
            string += f"{i}{list_splitter}"
        string = string[:-len(list_splitter)]
        return string

    # retourne une liste depuis un texte
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

    # retourne un texte qui pourrait être converti en liste de dictionnaires
    def pack_list_dict_to_str(self, list: [dict], value_splitter: str = "/v:", dict_splitter: str = "/d:",
                              list_splitter: str = "/l:") -> str:
        try:
            list_dict_str = []
            for case in list:
                new_dict_str = self.dict_to_str(case, value_splitter, dict_splitter)
                list_dict_str.append(new_dict_str)
            return self.list_to_str(list_dict_str, list_splitter)
        except Exception as exc:
            raise exc

    # retourne une liste de dictionnaires depuis un texte
    def unpack_str_to_list_dict(self, string: str = None, value_splitter: str = "/v:", dict_splitter: str = "/d:",
                                list_splitter: str = "/l:") -> [dict]:
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

    # vérifie qu'un texte soit possible à convertir en date
    def is_format_date(self, string: str) -> bool:
        try:
            date = self.take_numbers(string)
            date_struct = time.strptime(date, "%d %m %Y %H %M %S")
            date_float = calendar.timegm(date_struct)
            return True
        except:
            return False

    def take_data_for_percentage(self, args) -> tuple:
        # trouver les clés
        keys_pos = []
        for i in self.user_data_percentage:
            try:
                find = self.find(args, i)[0]
                keys_pos.append(find)
            except:
                continue

        # mettre dans l'ordre les clés
        new_keys_pos = []
        for key in keys_pos:
            has_found_place = False
            if len(new_keys_pos) > 0:
                for i in range(len(new_keys_pos)):
                    if key[0] < new_keys_pos[i][0]:
                        new_keys_pos.insert(i, key)
                        has_found_place = True
                if has_found_place is False:
                    new_keys_pos.append(key)
            else:
                new_keys_pos.append(key)
        keys_pos = new_keys_pos

        # définir les zones où chercher
        list_pos = []
        for i in range(len(keys_pos)):
            start = keys_pos[i][0]
            try:
                end = keys_pos[i + 1][0]
            except:
                end = len(args)
            list_pos.append((start, end))

        # récupérer les parties et les mettre dans une liste
        parts = self.take_parts_with_numbers(args, list_pos)
        percent_list = []
        for i in parts:
            y = self.take_numbers(i, to_int=True)
            if len(y) != 3:
                return (False, f"Dans __'{i}'__ il faut 3 nombres. Et vous avez écrit **"
                        f"'{self.take_numbers(i)}'**.")
            x = i[0:4].replace(" ", "")
            percent_list.append((x, y))

        return True, percent_list

    def get_prerequis_embed(self) -> discord.Embed:
        dictionary = {
            "Salons": ["Un salon pour les **commandes**, que vous renseignez grâce à la commande\n``-setChannelCMD``",
                       "Un salon pour les **évenements**, que vous renseignez grâce à la commande\n``-setChannelEvent``",
                       "Un salon pour les **annonces** que vous renseignez grâce à la commande\n``-setChannelAd``"],
            "Rôles": [
                "Un rôle **dataManager** qui permettra à des membres de s'occuper du bot sans avoir besoin d'être admin"
                ", que vous renseignez grâce à la commande\n``-setRoleManager``",
                "Un rôle **event** qui sera mentionné lorsqu'un évenement est affiché, que vous renseignez grâce à "
                "la commande\n``-setRoleEvent``"]
        }

        embed = discord.Embed(title="Prérequis",
                              description="Une liste de tout ce qu'il faut pour que le bot fonctionne correctement")

        for key in dictionary.keys():
            values = dictionary[key]
            text = ""
            for value in values:
                text += f"- {value}\n"
            embed.add_field(name=key, value=text, inline=False)

        embed.set_footer(text="Bonjour !")
        return embed
