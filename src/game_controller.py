from threading import Timer

from src.data_types import User, Board, Cell
from src.database_utils import DatabaseInterface as DB
from src.io_init import RequestProcessor as RP


class Game:
    def __init__(
            self,
            player1: User,
            player2: User,
            board: Board,
            turn: int,
            player1_display_id: int,
            player2_display_id: int):
        self.player1 = player1  # player who starts game
        self.player2 = player2  # second player
        self.board = board  # board
        self.turn = turn  # id of user who makes turn
        self.id = hash((player1.id, player2.id))
        self.player1_game_display_id = player1_display_id
        self.player2_game_display_id = player2_display_id

    def check_winning(self):
        if self.board.check_finish_situation() == Cell.CIRCLE:
            return self.player1
        elif self.board.check_finish_situation() == Cell.CROSS:
            return self.player2
        else:
            return None

    def check_draw(self):
        return self.board.check_draw()

    def make_turn(self, y: int, x: int):
        if self.board.field[y][x] == Cell.EMPTY:
            if self.turn == self.player1.id:
                self.board.make_turn(y, x, Cell.CIRCLE)
                self.turn = self.player2.id

            else:
                self.board.make_turn(y, x, Cell.CROSS)
                self.turn = self.player1.id
        else:
            raise Exception("Cell is not empty")


class GameController():
    @staticmethod
    def __raiting_counting(rating_A: int,
                           rating_B: int,
                           points_A: float,
                           points_B: float,
                           k: int = 20) -> (int,
                                            int):
        delta_rating = max(min(400, rating_B - rating_A), -400)
        expected_points_A = 1 / (1 + 10 ** (delta_rating / 400))
        expected_points_B = 1 / (1 + 10 ** (-delta_rating / 400))
        new_rating_A = rating_A + k * (points_A - expected_points_A)
        new_rating_B = rating_B + k * (points_B - expected_points_B)
        return int(round(new_rating_A)), int(round(new_rating_B))

    def __check_opponent_is_found(self, user_id: int):
        user = self.database_interface.get_user(user_id)
        if user.is_ready_to_play:
            self.database_interface.update_user(
                user_id, is_ready_to_play=False)
            # TODO send message to user: " opponent is not found "
            self.request_processor.gui_output.print_text(
                user_id, "opponent is not found")

    def __close_game(self, game: Game):
        self.request_processor.gui_output.close_board(
            game.player1.id, game.player1_game_display_id)
        self.request_processor.gui_output.close_board(
            game.player2.id, game.player2_game_display_id)

        self.database_interface.update_user(
            game.player1.id,
            current_game_id=0,
            games_played=game.player1.games_played + 1)
        self.database_interface.update_user(
            game.player2.id,
            current_game_id=0,
            games_played=game.player2.games_played + 1)

        self.__print_rating(game.player1.id)
        self.__print_rating(game.player2.id)

        del self.__games[game.id]

    def __process_draw(self, game: Game, last_turn_user: User):
        self.request_processor.gui_output.print_text(
            game.player1.id, "Draw!")
        self.request_processor.gui_output.print_text(
            game.player2.id, "Draw!")

        p1_new_rating, p2_new_rating = self.__raiting_counting(
            game.player1.rating, game.player2.rating, 0.5, 0.5)

        self.database_interface.update_user(
            game.player1.id, maximal_rating=max(
                game.player1.maximal_rating, p1_new_rating))
        self.database_interface.update_user(
            game.player2.id, maximal_rating=max(
                game.player2.maximal_rating, p2_new_rating))

        self.database_interface.update_user(
            game.player1.id, rating=p1_new_rating)
        self.database_interface.update_user(
            game.player2.id, rating=p2_new_rating)

        self.__close_game(game)

    def __process_wining(self, game: Game, last_turn_user: User):
        p1, p2 = game.player1, game.player2
        id1, id2 = game.player1_game_display_id, game.player2_game_display_id

        if game.check_winning() is p2:
            p1, p2 = p2, p1
            id1, id2 = id2, id1

        self.request_processor.gui_output.print_text(
            p1.id, "You won!")
        self.request_processor.gui_output.print_text(
            p2.id, "You lost!")

        p1_new_rating, p2_new_rating = self.__raiting_counting(
            p1.rating, p2.rating, 1., 0.)

        self.database_interface.update_user(
            p1.id, maximal_rating=max(p1.maximal_rating, p1_new_rating))
        self.database_interface.update_user(
            p2.id, maximal_rating=max(p2.maximal_rating, p2_new_rating))

        self.database_interface.update_user(
            p1.id, rating=p1_new_rating)
        self.database_interface.update_user(
            p2.id, rating=p2_new_rating)

        self.__close_game(game)

    def __print_rating(self, user_id: int):
        rating = self.database_interface.get_user(user_id).rating
        self.request_processor.gui_output.print_text(
            user_id, "Your rating is " + str(rating) + " now")

    def __init__(self, waiting_time: int = 10):
        self.request_processor = RP()
        self.database_interface = DB("database.db")
        self.waiting_time = waiting_time
        self.__games = dict()
        self.database_interface.clear_oppened_games()

        @self.request_processor.request_handler('user_registration')
        def register_new_user(user_id: int, username: str):
            self.database_interface.create_user(
                User(id=user_id, username=username))
            self.request_processor.gui_output.print_welcome(
                user_id, "Hello, " + username)
            self.__print_rating(user_id)

        @self.request_processor.request_handler('get_statistics')
        def get_statistic(user_id: int):
            user = self.database_interface.get_user(user_id)
            rating = user.rating
            games_played = user.games_played
            maximal_rating = user.maximal_rating
            global_rating = self.database_interface.get_global_rating(user_id)
            num_of_players = self.database_interface.get_num_of_users()
            text = "Your rating is " + str(rating) + "\n"
            text += "Your maximal rating is " + str(maximal_rating) + "\n"
            text += "You have already played " + str(games_played) + " games\n"
            text += "Your global rating is " + \
                str(global_rating) + " / " + str(num_of_players) + "\n"
            self.request_processor.gui_output.print_text(user_id, text)

        @self.request_processor.request_handler('start_game')
        def open_game(user_id: int):
            user = self.database_interface.get_user(user_id)
            if user.current_game_id != 0:
                self.request_processor.gui_output.print_text(
                    user_id, "You are already in game")

            else:
                self.database_interface.update_user(
                    user.id, is_ready_to_play=True)
                try:
                    opponent = self.database_interface.find_closest_player_by_rating(
                        user.id, user.rating)
                    self.database_interface.update_user(
                        user.id, is_ready_to_play=False)
                    self.database_interface.update_user(
                        opponent.id, is_ready_to_play=False)

                    # new game between user and opponent
                    blank_board = Board()
                    player1_display_id = self.request_processor.gui_output.draw_board(
                        user.id, blank_board, user.username)
                    player2_display_id = self.request_processor.gui_output.draw_board(
                        opponent.id, blank_board, user.username)

                    new_game = Game(
                        user,
                        opponent,
                        blank_board,
                        user.id,
                        player1_display_id,
                        player2_display_id)
                    self.__games[new_game.id] = new_game

                    self.database_interface.update_user(
                        user.id, current_game_id=new_game.id)
                    self.database_interface.update_user(
                        opponent.id, current_game_id=new_game.id)

                except Exception as e:
                    if e.args[0] == "User not found":
                        self.request_processor.gui_output.print_text(
                            user.id, "waiting for opponent...")
                        search_timeout = Timer(
                            self.waiting_time, self.__check_opponent_is_found, [
                                user.id])
                        search_timeout.start()
                    else:
                        raise e

        @self.request_processor.request_handler('button_pushing')
        def process_button_pushing(user_id: int, y: int, x: int):
            user = self.database_interface.get_user(user_id)

            if user.current_game_id == 0:
                self.request_processor.gui_output.print_text(
                    user_id, "You are not in game")

            else:
                game = self.__games[user.current_game_id]

                if game.turn == user_id:
                    if game.board[y, x] == Cell.EMPTY:
                        game.make_turn(y, x)
                        game.turn = game.player2.id if user_id == game.player1.id else game.player1.id
                        next_turns_player = game.player2.username if user_id == game.player1.id else game.player1.username

                        game.player1_game_display_id = self.request_processor.gui_output.update_board(
                            game.player1.id, game.player1_game_display_id, game.board, next_turns_player)
                        game.player2_game_display_id = self.request_processor.gui_output.update_board(
                            game.player2.id, game.player2_game_display_id, game.board, next_turns_player)

                        if game.check_winning():
                            self.__process_wining(game, user)

                        elif game.check_draw():
                            self.__process_draw(game, user)

                    else:
                        self.request_processor.gui_output.print_text(
                            user_id, "Cell is not empty")

                else:
                    self.request_processor.gui_output.print_text(
                        user_id, "It's not your turn")

    def start(self):
        self.request_processor.start_polling()
