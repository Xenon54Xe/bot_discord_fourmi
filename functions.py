import os.path as path


class Function:
    def __init__(self):
        self.path = path.abspath(".")
        self.list_true = ['yes', 'y', 'true', 't', '1', 'enable', 'on', 'oui']
        self.list_false = ['no', 'n', 'false', 'f', '0', 'disable', 'off', 'non']
        self.list_all = ['all', 'a', 'everything', 'e', 'tout']
        self.list_none = ["None", "0", "", "Null", " "]
        self.guillemet = ["'", "\""]
        self.first_splitter = "/:"
        self.second_splitter = "/."

    def take_parts(self, string: str, marker: str) -> list[str]:
        founded_pos = []
        for i in range(len(string)):
            find_marker = ""
            if string[i] == marker[0]:
                for i_f in range(i, i + len(marker)):
                    find_marker += string[i_f]
                if find_marker == marker:
                    founded_pos.append(i + len(marker))

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

        return parts

    def take_numbers(self, string: str) -> str:
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
        numbers = numbers[:-1]
        return numbers
    
    def dict_to_str(self, dictionary: dict, first_splitter: str, second_splitter: str) -> str:
        string = ""
        for key in dictionary:
            value = dictionary[key]
            string += f"{key}{first_splitter}{value}{second_splitter}"
        string = string[:-2]
        return string

    def str_to_dict(self, string: str, first_splitter: str, second_splitter: str) -> dict:
        dictionary = {}

        sheets = string.split(second_splitter)
        if len(sheets) == 1:
            raise Exception(f"Marker: Marqueur {second_splitter} introuvable dans {string}")

        for sheet in sheets:
            parts = sheet.split(first_splitter)
            if len(parts) == 1:
                raise Exception(f"Marker: Marqueur {first_splitter} introuvable dans {sheet}")
            key = parts[0]
            value = parts[1]
            dictionary[key] = value
        return dictionary
