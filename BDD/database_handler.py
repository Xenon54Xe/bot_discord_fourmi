import os
import sqlite3


class DatabaseHandler:
    def __init__(self, database_name: str):
        self.con = sqlite3.connect(f"{os.path.dirname(os.path.abspath(__file__))}/{database_name}")
        self.con.row_factory = sqlite3.Row

    def create_user(self, user_id: int, guild_id: int, username: str):
        cursor = self.con.cursor()
        if self.user_exists_with(user_id, guild_id):  # Vérifie si user existe déjà
            query = f"UPDATE User SET username = ? WHERE (userId, guildId) = (?, ?);"
            cursor.execute(query, (username, user_id, guild_id))
        else:
            query = f"INSERT INTO User (userId, guildId, username) VALUES (?, ?, ?);"
            cursor.execute(query, (user_id, guild_id, username))
        cursor.close()
        self.con.commit()

    def delete_user(self, user_id: int, guild_id: int):
        if self.user_exists_with(user_id, guild_id):
            cursor = self.con.cursor()
            query = f"DELETE FROM User WHERE (userId, guildId) = (?, ?);"
            cursor.execute(query, (user_id, guild_id))
            cursor.close()
            self.con.commit()

    def get_all_users(self, guild_id: int) -> map:
        cursor = self.con.cursor()
        query = f"SELECT * FROM User WHERE guildId = ?;"
        cursor.execute(query, (guild_id,))
        result = cursor.fetchall()
        cursor.close()

        return map(dict, result)

    def get_user(self, user_id: int, guild_id: int) -> dict:
        cursor = self.con.cursor()
        query = f"SELECT * FROM User WHERE (userId, guildId) = (?, ?);"
        cursor.execute(query, (user_id, guild_id))
        result = cursor.fetchall()
        cursor.close()

        if len(result) > 1:
            print(f"Il y a trop d'utilisateurs ayant l'id : {user_id}, dans la guild : {guild_id}")

        return dict(result[0])

    def set_choice(self, user_id: int, guild_id: int, new_choices: str = None):
        cursor = self.con.cursor()
        query = f"UPDATE User SET choice = ? WHERE (userId, guildId) = (?, ?);"
        cursor.execute(query, (new_choices, user_id, guild_id))
        cursor.close()
        self.con.commit()

    def set_availability(self, user_id: int, guild_id: int, availability: str = None):
        cursor = self.con.cursor()
        query = f"UPDATE User SET availability = ? WHERE (userId, guildId) = (?, ?);"
        cursor.execute(query, (availability, user_id, guild_id))
        cursor.close()
        self.con.commit()

    def set_speciality(self, user_id: int, guild_id: int, speciality: str = None):
        cursor = self.con.cursor()
        query = f"UPDATE User SET speciality = ? WHERE (userId, guildId) = (?, ?);"
        cursor.execute(query, (speciality, user_id, guild_id))
        cursor.close()
        self.con.commit()

    def set_ad(self, user_id: int, guild_id: int, ad: str = None):
        cursor = self.con.cursor()
        query = f"UPDATE User SET ad = ? WHERE (userId, guildId) = (?, ?);"
        cursor.execute(query, (ad, user_id, guild_id))
        cursor.close()
        self.con.commit()

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
    def create_role(self, role_id: int, guild_id: int, role_name):
        cursor = self.con.cursor()
        if self.role_exists_with(role_id, guild_id):  # Vérifie si role existe déjà
            query = f"UPDATE Role SET roleName = ? WHERE (roleId, guildId) = (?, ?);"
            cursor.execute(query, (role_name, role_id, guild_id))
        else:
            query = f"INSERT INTO Role (roleId, guildId, roleName) VALUES (?, ?, ?);"
            cursor.execute(query, (role_id, guild_id, role_name))
        cursor.close()
        self.con.commit()

    def delete_role(self, role_id: int, guild_id: int):
        if self.role_exists_with(role_id, guild_id):
            cursor = self.con.cursor()
            query = f"DELETE FROM Role WHERE (roleId, guildId) = (?, ?);"
            cursor.execute(query, (role_id, guild_id))
            cursor.close()
            self.con.commit()

    def get_all_roles(self, guild_id: int) -> map:
        cursor = self.con.cursor()
        query = f"SELECT * FROM Role WHERE guildId = ?;"
        cursor.execute(query, (guild_id,))
        result = cursor.fetchall()
        cursor.close()

        return map(dict, result)

    def get_role(self, role_id: int, guild_id: int) -> dict:
        if self.role_exists_with(role_id, guild_id):
            cursor = self.con.cursor()
            query = f"SELECT * FROM Role WHERE (roleId, guildId) = (?, ?);"
            cursor.execute(query, (role_id, guild_id))
            result = cursor.fetchall()
            cursor.close()

            return dict(result[0])
        else:
            raise Exception(f"Role not found : role_id='{role_id}', guild_id='{guild_id}'")

    def set_role_ad_value(self, role_id: int, guild_id: int, value: int):
        cursor = self.con.cursor()
        query = f"UPDATE Role SET adValue = ? WHERE (roleId, guildId) = (?, ?);"
        cursor.execute(query, (value, role_id, guild_id))
        cursor.close()
        self.con.commit()

    def set_role_is_data_manager(self, role_id: int, guild_id: int, data_manager: bool):
        cursor = self.con.cursor()
        query = f"UPDATE Role SET isDataManager = ? WHERE (roleId, guildId) = (?, ?);"
        cursor.execute(query, (data_manager, role_id, guild_id))
        cursor.close()
        self.con.commit()

    def set_role_is_movable(self, role_id: int, guild_id: int, movable: bool):
        cursor = self.con.cursor()
        query = f"UPDATE Role SET isMovable = ? WHERE (roleId, guildId) = (?, ?);"
        cursor.execute(query, (movable, role_id, guild_id))
        cursor.close()
        self.con.commit()

    def set_role_is_event(self, role_id: int, guild_id: int, event: bool):
        cursor = self.con.cursor()
        query = f"UPDATE Role SET isEvent = ? WHERE (roleId, guildId) = (?, ?);"
        cursor.execute(query, (event, role_id, guild_id))
        cursor.close()
        self.con.commit()

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
    def create_guild(self, guild_id: int, guild_name: str):
        cursor = self.con.cursor()
        if self.guild_exists_with(guild_id):
            query = "UPDATE Guild SET guildName = ? WHERE guildId = ?;"
            cursor.execute(query, (guild_name, guild_id))
        else:
            query = "INSERT INTO Guild (guildId, guildName) VALUES (?, ?);"
            cursor.execute(query, (guild_id, guild_name))
        cursor.close()
        self.con.commit()

    def delete_guild(self, guild_id: int):
        if self.guild_exists_with(guild_id):
            cursor = self.con.cursor()
            query = "DELETE FROM Guild WHERE guildId = ?;"
            cursor.execute(query, (guild_id,))
            cursor.close()
            self.con.commit()

    def get_all_guilds(self) -> map:
        cursor = self.con.cursor()
        query = f"SELECT * FROM Guild;"
        cursor.execute(query)
        result = cursor.fetchall()
        cursor.close()

        return map(dict, result)

    def get_guild(self, guild_id: int) -> dict:
        cursor = self.con.cursor()
        query = f"SELECT * FROM Guild WHERE guildId = ?;"
        cursor.execute(query, (guild_id,))
        result = cursor.fetchall()
        cursor.close()

        return dict(result[0])

    def set_event(self, guild_id: int, event: str):
        cursor = self.con.cursor()
        query = f"UPDATE Guild SET event = ? WHERE guildId = ?;"
        cursor.execute(query, (event, guild_id))
        cursor.close()
        self.con.commit()

    def set_time_before_call(self, guild_id: int, seconds: int):
        cursor = self.con.cursor()
        query = f"UPDATE Guild SET timeBeforeLastCall = ? WHERE guildId = ?;"
        cursor.execute(query, (seconds, guild_id))
        cursor.close()
        self.con.commit()

    def set_suggestion(self, guild_id: int, suggestion: str):
        cursor = self.con.cursor()
        query = f"UPDATE Guild SET suggestion = ? WHERE guildId = ?;"
        cursor.execute(query, (suggestion, guild_id))
        cursor.close()
        self.con.commit()

    def set_cmd_channel(self, guild_id: int, channel_id: int = None):
        cursor = self.con.cursor()
        query = f"UPDATE Guild SET cmdChannelId = ? WHERE guildId = ?;"
        cursor.execute(query, (channel_id, guild_id))
        cursor.close()
        self.con.commit()

    def set_event_channel(self, guild_id: int, channel_id: int):
        cursor = self.con.cursor()
        query = f"UPDATE Guild SET eventChannelId = ? WHERE guildId = ?;"
        cursor.execute(query, (channel_id, guild_id))
        cursor.close()
        self.con.commit()

    def set_ad_channel(self, guild_id: int, channel_id: int):
        cursor = self.con.cursor()
        query = f"UPDATE Guild SET adChannelId = ? WHERE guildId = ?;"
        cursor.execute(query, (channel_id, guild_id))
        cursor.close()
        self.con.commit()

    def guild_exists_with(self, guild_id: int) -> bool:
        cursor = self.con.cursor()
        query = f"SELECT * FROM Guild WHERE guildId = ?;"
        cursor.execute(query, (guild_id,))
        result = cursor.fetchall()
        cursor.close()

        return len(result) == 1
