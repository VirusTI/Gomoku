import sqlite3

from src.data_types import User


class DatabaseInterface():
    @staticmethod
    def __dict_factory(__cursor, row):
        dict = {}
        for idx, col in enumerate(__cursor.description):
            dict[col[0]] = row[idx]
        return dict

    @staticmethod
    def __build_cur(filename: str):
        __connection = sqlite3.connect(filename, check_same_thread=False)
        __connection.row_factory = DatabaseInterface.__dict_factory
        return __connection

    def __init__(self, filename: str):
        self.__connection = self.__build_cur(filename)
        self.__cursor = self.__connection.cursor()

    def __del__(self):
        self.__connection.close()

    def clear_oppened_games(self):
        self.__cursor.execute("Update users SET current_game_id=0")
        self.__connection.commit()

    def get_user(self, id: int) -> User:
        try:
            user = list(
                self.__cursor.execute(
                    "SELECT * FROM users WHERE id=?", (id,)))[0]
            return User(**user)
        except BaseException:
            raise Exception("User not found")

    def get_global_rating(self, id: int) -> int:
        try:
            cur_rating = self.get_user(id).rating
            global_rating = len(
                list(
                    self.__cursor.execute(
                        "SELECT rating FROM users WHERE rating>=?", (cur_rating,))))
            return global_rating
        except BaseException:
            raise Exception("User not found")

    def get_num_of_users(self) -> int:
        return len(list(self.__cursor.execute("SELECT * FROM users")))

    def create_user(self, user: User):
        try:
            d = user.__dict__
            query = "INSERT INTO users (" + " ,".join(d.keys()) + \
                ") VALUES (" + "?, " * (len(d.values()) - 1) + "? )"
            self.__cursor.execute(query, [i for i in d.values()])
            self.__connection.commit()
        except BaseException:
            pass

    def delete_user(self, id: int):
        self.__cursor.execute("DELETE FROM users WHERE id=?", (id,))
        self.__connection.commit()

    def update_user(self, id: int, **params):
        d = params
        for key in d.keys():
            self.__cursor.execute(
                "UPDATE users SET " + key + "=? WHERE id=?", (d[key], id))
        self.__connection.commit()

    def find_closest_player_by_rating(self, id: int, cur_rating: int) -> User:
        is_ready_to_play_flag = True
        users_with_higher_rating = list(
            self.__cursor.execute(
                "SELECT * FROM users WHERE rating>=? AND is_ready_to_play=? AND NOT id=? ORDER BY rating",
                (cur_rating, is_ready_to_play_flag, id)))
        users_with_lower_rating = list(
            self.__cursor.execute(
                "SELECT * FROM users WHERE rating<? AND is_ready_to_play=? AND NOT id=? ORDER BY rating DESC",
                (cur_rating, is_ready_to_play_flag, id)))
        minimal_delta_rating = float("inf")

        if len(users_with_higher_rating) > 0:
            minimal_delta_rating = users_with_higher_rating[0]["rating"] - cur_rating
        if len(users_with_lower_rating) > 0:
            minimal_delta_rating = min(
                minimal_delta_rating,
                cur_rating -
                users_with_lower_rating[0]["rating"])
        if minimal_delta_rating == float("inf"):
            raise Exception("User not found")
        else:
            if len(users_with_higher_rating) > 0 and minimal_delta_rating == users_with_higher_rating[0][
                    "rating"] - cur_rating:
                return User(**users_with_higher_rating[0])
            else:
                return User(**users_with_lower_rating[0])
