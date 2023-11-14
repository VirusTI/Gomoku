# -*- coding: utf-8 -*-
from enum import Enum


class User:
    def __init__(
            self,
            id: int,
            username: str = "",
            rating: int = 100,
            is_ready_to_play: bool = False,
            current_game_id: int = 0,
            games_played: int = 0,
            maximal_rating: int = 100):
        self.id = id
        self.username = username
        self.rating = rating
        self.is_ready_to_play = is_ready_to_play
        self.current_game_id = current_game_id
        self.games_played = games_played
        self.maximal_rating = maximal_rating


class Cell(Enum):
    EMPTY = 0
    CIRCLE = 1  # first player
    CROSS = 2  # second player

    def str(self):
        if self == Cell.EMPTY:
            return ' '
        elif self == Cell.CIRCLE:
            return '⚪️'
        elif self == Cell.CROSS:
            return '✖️'


class Board:
    def __init__(self, sizeX: int = 8, sizeY: int = 12):
        self.sizeX = sizeX
        self.sizeY = sizeY
        self.field = [[Cell.EMPTY for i in range(sizeX)] for j in range(sizeY)]

    def check_finish_situation(self):
        for i in range(self.sizeY):
            for j in range(self.sizeX):
                if self.field[i][j] == Cell.EMPTY:
                    continue
                else:
                    if j + 4 < self.sizeX and self.field[i][j] == self.field[i][j +
                                                                                1] == self.field[i][j + 2] == \
                            self.field[i][j + 3] == self.field[i][j + 4]:
                        return self.field[i][j]
                    elif i + 4 < self.sizeY and self.field[i][j] == self.field[i + 1][j] == self.field[i + 2][j] == \
                            self.field[i + 3][j] == self.field[i + 4][j]:
                        return self.field[i][j]
                    elif j + 4 < self.sizeX and i + 4 < self.sizeY and self.field[i][j] == self.field[i + 1][j + 1] == self.field[i + 2][
                            j + 2] == self.field[i + 3][j + 3] == self.field[i + 4][j + 4] and i + 4 < self.sizeY:
                        return self.field[i][j]
                    elif j + 4 < self.sizeX and self.field[i][j] == self.field[i - 1][j + 1] == self.field[i - 2][
                            j + 2] == self.field[i - 3][j + 3] == self.field[i - 4][j + 4] and i - 4 >= 0:
                        return self.field[i][j]
        return Cell.EMPTY

    def check_draw(self):
        for i in range(self.sizeX):
            for j in range(self.sizeY):
                if self.field[i][j] == Cell.EMPTY:
                    return False
        return True

    def make_turn(self, y: int, x: int, cell: Cell):
        self.field[y][x] = cell

    def __getitem__(self, pos: tuple):
        y, x = pos
        return self.field[y][x]
