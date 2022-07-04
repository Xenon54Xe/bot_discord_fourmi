import os
import sqlite3

from bot_discord_fourmi.functions import Function


class DatabaseHandler:
    def __init__(self, database_name: str):
        self.functions = Function()
        self.con = sqlite3.connect(f"{os.path.dirname(os.path.abspath(__file__))}/{database_name}")
        self.check()
        self.con.row_factory = sqlite3.Row

    # vérifie que la BDD soit bien formée
    def check(self):
        cursor = self.con.cursor()
        try:
            cursor.execute("SELECT * FROM Guild LIMIT 1")
            cursor.execute("SELECT * FROM User LIMIT 1")
            cursor.execute("SELECT * FROM Role LIMIT 1")
        except Exception as exc:
            print(exc)
            self.initialise()

    # initialise la BDD
    def initialise(self):
        with open("database.db", "w", encoding="UTF-8") as file:
            file.write("")
            file.close()

        cursor = self.con.cursor()

        with open("init_instruction.sql", "r", encoding="UTF-8") as file:
            instructions = file.readlines()
            text = ""
            for line in instructions:
                text += line
            file.close()

        parts = self.functions.take_parts(text, "/i:")

        for query in parts:
            cursor.execute(query)
        self.con.commit()

        return self.con

    # ajoute un utilisateur dans la BDD
    def add_user(self, user_id: int, guild_id: int, username: str):
        if user_id != -1 and self.user_exists_with(user_id, guild_id):
            raise Exception(f"User '{username}' already exist.")
        cursor = self.con.cursor()
        query = "INSERT INTO User (userId, guildId, username) VALUES (?, ?, ?);"
        cursor.execute(query, (user_id, guild_id, username))
        cursor.close()
        self.con.commit()

    # met à jour un utilisateur dans la BDD
    def update_user(self, user_id: int, guild_id: int, username: str):
        if not self.user_exists_with(user_id, guild_id):
            raise Exception(f"User '{username}' not already exist.")
        cursor = self.con.cursor()
        query = "UPDATE User SET username = ? WHERE (userId, guildId) = (?, ?);"
        cursor.execute(query, (username, user_id, guild_id))
        cursor.close()
        self.con.commit()

    # supprime un utilisateur de la BDD, peut utiliser l'id dans la BDD
    def remove_user(self, user_id: int = None, guild_id: int = None, bdd_id: int = None):
        cursor = self.con.cursor()
        if bdd_id is None:
            if user_id != -1 and not self.user_exists_with(user_id, guild_id):
                raise Exception(f"The user with the id : '{user_id}' not already exist.")
            query = f"DELETE FROM User WHERE (userId, guildId) = (?, ?);"
            cursor.execute(query, (user_id, guild_id))
        else:
            query = "DELETE FROM User WHERE id = ?;"
            cursor.execute(query, (bdd_id,))
        cursor.close()
        self.con.commit()

    # retourne tous les utilisateurs ayant la même guild_id
    def get_all_users(self, guild_id: int) -> list:
        cursor = self.con.cursor()
        query = f"SELECT * FROM User WHERE guildId = ?;"
        cursor.execute(query, (guild_id,))
        result = cursor.fetchall()
        cursor.close()

        return list(map(dict, result))

    # retourne les infos d'un utilisateur
    def get_user(self, user_id: int = None, guild_id: int = None, bdd_id: int = None) -> dict:
        cursor = self.con.cursor()
        if bdd_id is None:
            if not self.user_exists_with(user_id, guild_id):
                raise Exception(f"The user with the id '{user_id}' not already exist.")
            query = f"SELECT * FROM User WHERE (userId, guildId) = (?, ?);"
            cursor.execute(query, (user_id, guild_id))
        else:
            query = "SELECT * FROM User WHERE id = ?;"
            cursor.execute(query, (bdd_id,))
        result = cursor.fetchall()
        cursor.close()

        return dict(result[0])

    # définit les choix d'un utilisateur
    def set_choice(self, user_id: int = None, guild_id: int = None, new_choices: str = None, bdd_id: int = None):
        cursor = self.con.cursor()
        if bdd_id is None:
            query = "UPDATE User SET choice = ? WHERE (userId, guildId) = (?, ?);"
            cursor.execute(query, (new_choices, user_id, guild_id))
        else:
            query = "UPDATE User SET choice = ? WHERE id = ?;"
            cursor.execute(query, (new_choices, bdd_id))
        cursor.close()
        self.con.commit()

    # définit les disponibilités d'un utilisateur
    def set_availability(self, user_id: int = None, guild_id: int = None, availability: str = None, bdd_id: int = None):
        cursor = self.con.cursor()
        if bdd_id is None:
            query = f"UPDATE User SET availability = ? WHERE (userId, guildId) = (?, ?);"
            cursor.execute(query, (availability, user_id, guild_id))
        else:
            query = "UPDATE User SET availability = ? WHERE id = ?;"
            cursor.execute(query, (availability, bdd_id))
        cursor.close()
        self.con.commit()

    # définit les spécialités d'un utilisateur
    def set_speciality(self, user_id: int = None, guild_id: int = None, speciality: str = None, bdd_id: int = None):
        cursor = self.con.cursor()
        if bdd_id is None:
            query = f"UPDATE User SET speciality = ? WHERE (userId, guildId) = (?, ?);"
            cursor.execute(query, (speciality, user_id, guild_id))
        else:
            query = "UPDATE User SET speciality = ? WHERE id = ?;"
            cursor.execute(query, (speciality, bdd_id))
        cursor.close()
        self.con.commit()

    # définit les pourcentages d'un utilisateur
    def set_percentages(self, user_id: int = None, guild_id: int = None, percentage: str = None, bdd_id: int = None):
        cursor = self.con.cursor()
        if bdd_id is None:
            query = f"UPDATE User SET percentage = ? WHERE (userId, guildId) = (?, ?);"
            cursor.execute(query, (percentage, user_id, guild_id))
        else:
            query = "UPDATE User SET percentage = ? WHERE id = ?;"
            cursor.execute(query, (percentage, bdd_id))
        cursor.close()
        self.con.commit()

    # définit les annonces d'un utilisateur
    def set_ad(self, user_id: int, guild_id: int, ad: str = None):
        cursor = self.con.cursor()
        query = f"UPDATE User SET ad = ? WHERE (userId, guildId) = (?, ?);"
        cursor.execute(query, (ad, user_id, guild_id))
        cursor.close()
        self.con.commit()

    # retourne si un utilisateur existe ou pas
    def user_exists_with(self, user_id: int, guild_id: int) -> bool:
        cursor = self.con.cursor()
        query = f"SELECT * FROM User WHERE (userId, guildId) = (?, ?);"
        cursor.execute(query, (user_id, guild_id))
        result = cursor.fetchall()
        cursor.close()

        return len(result) == 1

    """
    Roles managing
    """
    # ajoute un rôle dans la BDD
    def add_role(self, role_id: int, guild_id: int, role_name: str):
        if self.role_exists_with(role_id, guild_id):
            raise Exception(f"Role '{role_name}' already exist.")
        cursor = self.con.cursor()
        query = "INSERT INTO Role (roleId, guildId, roleName) VALUES (?, ?, ?);"
        cursor.execute(query, (role_id, guild_id, role_name))
        cursor.close()
        self.con.commit()

    # met à jour un rôle dans la BDD
    def update_role(self, role_id: int, guild_id: int, role_name: str):
        if not self.role_exists_with(role_id, guild_id):
            raise Exception(f"Role '{role_name}' not already exist.")
        cursor = self.con.cursor()
        query = "UPDATE Role SET roleName = ? WHERE (roleId, guildId) = (?, ?);"
        cursor.execute(query, (role_name, role_id, guild_id))
        cursor.close()
        self.con.commit()

    # supprime un rôle de la BDD
    def remove_role(self, role_id: int, guild_id: int):
        if not self.role_exists_with(role_id, guild_id):
            raise Exception(f"The role with the id : '{role_id}' not already exist.")
        cursor = self.con.cursor()
        query = f"DELETE FROM Role WHERE (roleId, guildId) = (?, ?);"
        cursor.execute(query, (role_id, guild_id))
        cursor.close()
        self.con.commit()

    # donne tous les rôles ayant la même guild_id
    def get_all_roles(self, guild_id: int) -> list:
        cursor = self.con.cursor()
        query = f"SELECT * FROM Role WHERE guildId = ?;"
        cursor.execute(query, (guild_id,))
        result = cursor.fetchall()
        cursor.close()

        return list(map(dict, result))

    # retourne les infos d'un rôle
    def get_role(self, role_id: int, guild_id: int) -> dict:
        if not self.role_exists_with(role_id, guild_id):
            raise Exception(f"The role with the id '{role_id}' not already exist.")
        cursor = self.con.cursor()
        query = f"SELECT * FROM Role WHERE (roleId, guildId) = (?, ?);"
        cursor.execute(query, (role_id, guild_id))
        result = cursor.fetchall()
        cursor.close()

        return dict(result[0])

    # définit le nombre d'annonces qu'un rôle peut envoyer
    def set_role_ad_value(self, role_id: int, guild_id: int, value: int):
        cursor = self.con.cursor()
        query = f"UPDATE Role SET adValue = ? WHERE (roleId, guildId) = (?, ?);"
        cursor.execute(query, (value, role_id, guild_id))
        cursor.close()
        self.con.commit()

    # définit si un rôle est data_manager ou pas
    def set_role_is_data_manager(self, role_id: int, guild_id: int, data_manager: bool):
        cursor = self.con.cursor()
        query = f"UPDATE Role SET isDataManager = ? WHERE (roleId, guildId) = (?, ?);"
        cursor.execute(query, (data_manager, role_id, guild_id))
        cursor.close()
        self.con.commit()

    # définit si un rôle est movable ou pas
    def set_role_is_movable(self, role_id: int, guild_id: int, movable: bool):
        cursor = self.con.cursor()
        query = f"UPDATE Role SET isMovable = ? WHERE (roleId, guildId) = (?, ?);"
        cursor.execute(query, (movable, role_id, guild_id))
        cursor.close()
        self.con.commit()

    # définit si un rôle est event ou pas
    def set_role_is_event(self, role_id: int, guild_id: int, event: bool):
        cursor = self.con.cursor()
        query = f"UPDATE Role SET isEvent = ? WHERE (roleId, guildId) = (?, ?);"
        cursor.execute(query, (event, role_id, guild_id))
        cursor.close()
        self.con.commit()

    # retourne si un rôle existe ou pas
    def role_exists_with(self, role_id: int, guild_id: int) -> bool:
        cursor = self.con.cursor()
        query = f"SELECT * FROM Role WHERE (roleId, guildId) = (?, ?);"
        cursor.execute(query, (role_id, guild_id))
        result = cursor.fetchall()
        cursor.close()

        return len(result) == 1

    """
    Guild managing
    """
    # ajoute un serveur dans la BDD
    def add_guild(self, guild_id: int, guild_name: str):
        if self.guild_exists_with(guild_id):
            raise Exception(f"Guild '{guild_name}' already exist.")
        cursor = self.con.cursor()
        query = "INSERT INTO Guild (guildId, guildName) VALUES (?, ?);"
        cursor.execute(query, (guild_id, guild_name))
        cursor.close()
        self.con.commit()

    # met à jour un serveur dans la BDD
    def update_guild(self, guild_id: int, guild_name: str):
        if not self.guild_exists_with(guild_id):
            raise Exception(f"Guild '{guild_name}' not already exist.")
        cursor = self.con.cursor()
        query = "UPDATE Guild SET guildName = ? WHERE guildId = ?;"
        cursor.execute(query, (guild_name, guild_id))
        cursor.close()
        self.con.commit()

    # supprime un serveur de la BDD
    def remove_guild(self, guild_id: int):
        if not self.guild_exists_with(guild_id):
            raise Exception(f"The guild with the id : '{guild_id}' not already exist.")
        cursor = self.con.cursor()
        query = f"DELETE FROM Guild WHERE guildId = ?;"
        cursor.execute(query, (guild_id,))
        cursor.close()
        self.con.commit()

    # retourne tous les serveurs de la BDD
    def get_all_guilds(self) -> list:
        cursor = self.con.cursor()
        query = f"SELECT * FROM Guild;"
        cursor.execute(query)
        result = cursor.fetchall()
        cursor.close()

        return list(map(dict, result))

    # retourne les infos d'un serveur
    def get_guild(self, guild_id: int) -> dict:
        if not self.guild_exists_with(guild_id):
            raise Exception(f"The guild with the id '{guild_id}' not already exist.")
        cursor = self.con.cursor()
        query = f"SELECT * FROM Guild WHERE guildId = ?;"
        cursor.execute(query, (guild_id,))
        result = cursor.fetchall()
        cursor.close()

        return dict(result[0])

    # définit le salon des commandes d'un serveur
    def set_cmd_channel(self, guild_id: int, channel_id: int = None):
        cursor = self.con.cursor()
        query = f"UPDATE Guild SET cmdChannelId = ? WHERE guildId = ?;"
        cursor.execute(query, (channel_id, guild_id))
        cursor.close()
        self.con.commit()

    # définit les évenements d'un serveur
    def set_event(self, guild_id: int, event: str):
        cursor = self.con.cursor()
        query = f"UPDATE Guild SET event = ? WHERE guildId = ?;"
        cursor.execute(query, (event, guild_id))
        cursor.close()
        self.con.commit()

    # définit le salon des évenements d'un serveur
    def set_event_channel(self, guild_id: int, channel_id: int):
        cursor = self.con.cursor()
        query = f"UPDATE Guild SET eventChannelId = ? WHERE guildId = ?;"
        cursor.execute(query, (channel_id, guild_id))
        cursor.close()
        self.con.commit()

    # définit le temps qui sépare le premier et le deuxième affichage d'un évenement
    def set_time_before_call(self, guild_id: int, seconds: int):
        cursor = self.con.cursor()
        query = f"UPDATE Guild SET timeBeforeLastCall = ? WHERE guildId = ?;"
        cursor.execute(query, (seconds, guild_id))
        cursor.close()
        self.con.commit()

    # définit le salon des annonces d'un serveur
    def set_ad_channel(self, guild_id: int, channel_id: int):
        cursor = self.con.cursor()
        query = f"UPDATE Guild SET adChannelId = ? WHERE guildId = ?;"
        cursor.execute(query, (channel_id, guild_id))
        cursor.close()
        self.con.commit()

    # définit les suggestions d'un serveur
    def set_suggestion(self, guild_id: int, suggestion: str):
        cursor = self.con.cursor()
        query = f"UPDATE Guild SET suggestion = ? WHERE guildId = ?;"
        cursor.execute(query, (suggestion, guild_id))
        cursor.close()
        self.con.commit()

    # retourne si un serveur existe ou pas
    def guild_exists_with(self, guild_id: int) -> bool:
        cursor = self.con.cursor()
        query = f"SELECT * FROM Guild WHERE guildId = ?;"
        cursor.execute(query, (guild_id,))
        result = cursor.fetchall()
        cursor.close()

        return len(result) == 1


bdd = DatabaseHandler("database.db")
