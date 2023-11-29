"""
https://www.youtube.com/watch?v=I2lOwRiGNy4
https://github.com/PiyushG14/Pygame-sudoku/blob/main/sudoku_solver.py
https://github.com/PiyushG14/Pygame-sudoku/blob/main/sudoku.py
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from enum import Enum
from typing import Any

import pygame

# from pygame.display import flip

pygame.init()

CFG_DIR = "/home/jvh/.local/share/sudoku"
FONT = pygame.font.SysFont("JetBrainsMono Nerd Font", 50)
FONT_MARKS = pygame.font.SysFont("JetBrainsMono Nerd Font", 18)
FONT_PROB = pygame.font.SysFont("JetBrainsMono Nerd Font", 12)

C_W = 100
WIDTH = 11 * C_W
GAP = 3

VALUE_COLOR = (0, 0, 0)
BG_COLOR = (251, 247, 245)
BG_IMMUTABLE = (230, 230, 230)
FOCUS_COLOR = (255, 218, 0)
FOCUS_MARK_COLOR = (150, 200, 255)
IMMUTABLE_FOCUS = (215, 215, 215)
INVALID_COLOR = (215, 95, 95)
INVALID_FOCUS = (165, 80, 80)
ERROR_FOCUS = (168, 34, 34)
ERROR_COLOR = (190, 35, 35)
LINE_COLOR = (149, 149, 149)

VALID_DIGIT_EVENTS = [
    pygame.K_1,
    pygame.K_2,
    pygame.K_3,
    pygame.K_4,
    pygame.K_5,
    pygame.K_6,
    pygame.K_7,
    pygame.K_8,
    pygame.K_9,
]
VALID_NAV_EVENTS = [
    pygame.K_h,
    pygame.K_j,
    pygame.K_k,
    pygame.K_l,
    pygame.K_LEFT,
    pygame.K_DOWN,
    pygame.K_UP,
    pygame.K_RIGHT,
]


class Mode(Enum):
    STARTING, PLAYING, SOLVED = range(3)


class Focus(Enum):
    NONE, INSERT, MARK = range(3)


class Cell:
    def __init__(self, row: int, col: int, value: int) -> None:
        self.value: dict[Mode, int] = {
            Mode.STARTING: value,
            Mode.PLAYING: value,
            Mode.SOLVED: value,
        }
        self.marks: list[int] = []
        self.probability: str = ""
        self.location: tuple[int, int] = (col * C_W + GAP, row * C_W + GAP)
        self.surface = pygame.Surface((C_W - GAP, C_W - GAP))
        # self.location: tuple[int, int]
        # self.surface: pygame.Surface
        self.focus: Focus = Focus.NONE
        self.invalid: bool = False
        self.error: bool = False

    def init_marks(self, marks: list[int]) -> None:
        self.marks = marks

    def add_mark(self, num: int) -> None:
        if len(self.marks) < 4:
            self.marks.append(num)

    def clear_marks(self) -> None:
        self.marks = []

    def set_focus(self, status: Focus) -> None:
        self.focus = status

    def set_invalid(self, status: bool) -> None:
        self.invalid = status

    def set_error(self, status: bool) -> None:
        self.error = status

    def get_val(self, mode: Mode = Mode.PLAYING) -> int:
        return self.value[mode]

    def set_val(self, val: int, mode: Mode = Mode.PLAYING) -> None:
        self.value[mode] = val

    def set_to_original(self) -> None:
        self.value[Mode.PLAYING] = self.value[Mode.STARTING]

    def set_to_solved(self) -> None:
        self.value[Mode.PLAYING] = self.value[Mode.SOLVED]

    def validate(self) -> None:
        value = self.value[Mode.PLAYING]
        if value != 0:
            self.error = value != self.value[Mode.SOLVED]

    def is_mutable(self) -> bool:
        return self.value[Mode.STARTING] == 0

    def get_background(self, mode: Mode) -> tuple[int, int, int]:
        if mode in [Mode.STARTING, Mode.SOLVED]:
            bgcolor = BG_COLOR if self.is_mutable() else BG_IMMUTABLE
        else:
            if self.error:
                bgcolor = ERROR_FOCUS if self.focus else ERROR_COLOR
            elif self.invalid:
                bgcolor = INVALID_FOCUS if self.focus else INVALID_COLOR
            else:
                if self.focus == Focus.INSERT:
                    bgcolor = FOCUS_COLOR if self.is_mutable() else IMMUTABLE_FOCUS
                elif self.focus == Focus.MARK:
                    bgcolor = FOCUS_MARK_COLOR if self.is_mutable() else IMMUTABLE_FOCUS
                else:
                    bgcolor = BG_COLOR if self.is_mutable() else BG_IMMUTABLE
        return bgcolor


class SudokuGrid:
    """Represents the data of all the Cell's in the Puzzle
    The rows and columns all have Cell objects.
    The index for rows and columns has a range of 1..9."""

    def __init__(self) -> None:
        # self.game_path = os.path.join(CFG_DIR, f"current-sudoku.json")
        self.game_path: str
        self.level: str
        self.game_data: dict[str, Any]
        self.grid: list[list[Cell]] = []
        self.init_grid()
        self.setup_game_data()
        self.setup_game()

    def find_options(self, row: int, col: int, mode: Mode = Mode.PLAYING) -> list[int]:
        """Row and Col are sudoku-coordinates."""
        used = {self.grid[row][c].get_val(mode) for c in range(1, 10)}
        used = used | {self.grid[r][col].get_val(mode) for r in range(1, 10)}
        r0 = ((row - 1) // 3) * 3 + 1  # first row of square
        c0 = ((col - 1) // 3) * 3 + 1  # first column of square
        used = used | {
            self.grid[r][c].get_val(mode)
            for r in range(r0, r0 + 3)
            for c in range(c0, c0 + 3)
        }.difference({0})
        return list(set(range(1, 10)).difference(used))

    def reset_to_start(self) -> None:
        """Reset "current" data_map to original values"""
        for row in range(1, 10):
            for col in range(1, 10):
                self.grid[row][col].set_to_original()
                self.grid[row][col].set_focus(Focus.NONE)
                self.grid[row][col].invalid = False

    def get_cell(self, row: int, col: int) -> Cell:
        return self.grid[row][col]

    def is_valid_move(self, row: int, col: int, num: int, mode: Mode) -> bool:
        """Check for Column, row and sub-grid."""
        # is num in range of 1..9
        if not 0 < num < 10:
            return False
        return num in self.find_options(row, col, mode)

    def solve_sudoku(self) -> bool:
        """doc"""
        # step 1: pre-fill solution with hidden singles
        for row in range(1, 10):
            for col in range(1, 10):
                if self.grid[row][col].is_mutable():
                    options = self.find_options(row, col, Mode.SOLVED)
                    if len(options) == 1:
                        self.grid[row][col].set_val(options[0], Mode.SOLVED)

        # step 2: use backtracking to fill remaining empty cells
        if self.solver():
            print("Puzzle is solved !!!!")
            self.print(Mode.SOLVED)
            return True
        else:
            print("Puzzle could not be solved !!!!")
            return False

    def solver(self) -> int | None:
        for row in range(1, 10):
            for col in range(1, 10):
                if self.grid[row][col].get_val(Mode.SOLVED) == 0:
                    options = self.find_options(row, col, Mode.SOLVED)
                    for num in options:
                        self.grid[row][col].set_val(num, Mode.SOLVED)
                        if self.solver():
                            return True
                        self.grid[row][col].set_val(0, Mode.SOLVED)
                    return False
        return True

    def find_probability(self, toggle: bool) -> None:
        for row in range(1, 10):
            for col in range(1, 10):
                if toggle and self.grid[row][col].get_val() == 0:
                    self.grid[row][col].probability = "".join(
                        sorted(
                            [
                                str(x)
                                for x in self.find_options(row, col)
                                if x not in self.grid[row][col].marks
                            ],
                        ),
                    )
                else:
                    self.grid[row][col].probability = ""

    def validate(self) -> None:
        for row in range(1, 10):
            for col in range(1, 10):
                self.grid[row][col].validate()

    def setup_game_data(self) -> None:
        if len(sys.argv) == 1:
            # set current puzzle config file for next load
            file_path = os.path.join(CFG_DIR, "current-sudoku-puzzle.cfg")
            with open(file_path) as f:
                lines = f.readlines()
                if len(lines) == 2:
                    self.game_path = lines[0].strip()
                    self.level = lines[1].strip()
                else:
                    print("current-sudoku-puzzle.cfg not found or corrupted")
                    sys.exit()
        else:
            parser = argparse.ArgumentParser()
            parser.add_argument("date", type=str, help="Sudoku date")
            parser.add_argument(
                "-l",
                "--level",
                type=str,
                choices=["easy", "medium", "hard"],
                required=True,
                help="Sudoku level",
            )
            args = parser.parse_args()
            self.level = args.level
            self.game_path = os.path.join(CFG_DIR, f"nytimes-{args.date}-sudoku.json")

            # set current puzzle config file for next load
            file_path = os.path.join(CFG_DIR, "current-sudoku-puzzle.cfg")
            with open(file_path, "w") as f:
                f.write(self.game_path + "\n")
                f.write(self.level)

        # read game date from json file
        with open(self.game_path) as f:
            self.game_data = json.loads(f.read())

    def init_grid(self) -> None:
        for row in range(10):
            if row == 0:
                self.grid.append([Cell(0, col, -1) for col in range(10)])
            else:
                self.grid.append(
                    [Cell(row, 0, -1)] + [Cell(row, col, 0) for col in range(1, 10)],
                )

    def load_grid_data(self, data: str, mode: Mode) -> None:
        for row, data in enumerate(data.split("/")):
            for col, val in enumerate([int(s) for s in list(data)]):
                self.grid[row + 1][col + 1].set_val(val, mode)

    def load_grid_marks(self, marks: str) -> None:
        for row, marks in enumerate(marks.split("/")):
            for col, mark in enumerate(marks.split("|")):
                self.grid[row + 1][col + 1].init_marks([int(s) for s in list(mark)])

    def setup_game(self) -> None:
        data = self.game_data[self.level]["puzzle"]
        # initialise grid with starting puzzle
        self.load_grid_data(data["original"], Mode.STARTING)
        self.load_grid_data(data["original"], Mode.PLAYING)
        self.load_grid_data(data["original"], Mode.SOLVED)

        if "solution" not in data:
            # this is a new game and needs to be solved
            if not self.solve_sudoku():
                sys.exit()
        else:
            # load saved solution & current game & markings
            self.load_grid_data(data["current"], Mode.PLAYING)
            self.load_grid_data(data["solution"], Mode.SOLVED)
            self.load_grid_marks(data["marks"])
        print(f"init sudoku: {self.game_path}\n")

    def values_to_string(self, mode: Mode) -> str:
        grid_str = ""
        for r in range(1, 10):
            for c in range(1, 10):
                grid_str += str(self.grid[r][c].value[mode])
            grid_str += "/"
        return grid_str[:-1]

    def marks_to_string(self) -> str:
        marks_str = ""
        for r in range(1, 10):
            for c in range(1, 10):
                for m in self.grid[r][c].marks:
                    marks_str += str(m)
                marks_str += "|"
            marks_str = marks_str[:-1] + "/"
        return marks_str[:-1]

    def write_game_status(self) -> None:
        data = self.game_data[self.level]["puzzle"]
        data["original"] = self.values_to_string(Mode.STARTING)
        data["current"] = self.values_to_string(Mode.PLAYING)
        data["solution"] = self.values_to_string(Mode.SOLVED)
        data["marks"] = self.marks_to_string()

        file_path = os.path.join(CFG_DIR, self.game_path)
        with open(file_path, "w") as f:
            f.write(json.dumps(self.game_data, indent=1))

    def print(self, mode: Mode = Mode.PLAYING) -> None:
        print()
        for row in range(0, 10):
            print(f"{row}> ", end="")
            for col in range(0, 10):
                print(f"{self.grid[row][col].value[mode]}, ", end="")
            print()


class SudokuBoard:
    """Board has 9 rows and 9 columns of Cell objects.
    The index for rows and columns has a range of 1..9."""

    def __init__(self, screen: pygame.Surface) -> None:
        self.screen = screen
        self.grid = SudokuGrid()
        self.mode: Mode = Mode.PLAYING
        self.prob_toggle = False
        self.curr_row: int = 5
        self.curr_col: int = 5
        self.draw_board()
        self.write_puzzle()
        pygame.display.flip()

    def clear_cell(self, cell: Cell, mode: Mode) -> None:
        cell.surface.fill(cell.get_background(mode))
        self.screen.blit(cell.surface, cell.location)

    def write_cell_value(self, cell: Cell, mode: Mode) -> None:
        value = cell.get_val(mode)
        if value != 0:
            self.screen.blit(
                FONT.render(str(value), True, VALUE_COLOR),
                (
                    (cell.location[0] + ((C_W - 30) // 2)),
                    (cell.location[1] + ((C_W - 65) // 2)),
                ),
            )

    def write_cell_marks(self, cell: Cell) -> None:
        for i in range(len(cell.marks)):
            if i == 0:
                xy = ((cell.location[0] + 6), (cell.location[1] + 3))
            elif i == 1:
                xy = ((cell.location[0] + C_W - 20), (cell.location[1] + 3))
            elif i == 2:
                xy = ((cell.location[0] + C_W - 20), (cell.location[1] + C_W - 28))
            else:
                # i == 3
                xy = ((cell.location[0] + 6), (cell.location[1] + C_W - 28))
            self.screen.blit(
                FONT_MARKS.render(str(cell.marks[i]), True, VALUE_COLOR),
                xy,
            )

    def write_cell_probability(self, cell: Cell) -> None:
        if cell.get_val() == 0:
            self.screen.blit(
                FONT_PROB.render(cell.probability, True, VALUE_COLOR),
                (
                    (cell.location[0] + ((C_W - 30) // 2)),
                    (cell.location[1] + ((C_W - 25) // 2)),
                ),
            )

    def write_cell(self, cell: Cell, mode: Mode = Mode.PLAYING) -> None:
        """Rewrite complete content of cell with value indicated by `mode."""
        self.clear_cell(cell, mode)
        self.write_cell_value(cell, mode)
        if not mode == Mode.SOLVED:
            self.write_cell_marks(cell)
            self.write_cell_probability(cell)

    def write_puzzle(self) -> None:
        for row in range(1, 10):
            for col in range(1, 10):
                # cell = self.grid[row][col])
                self.write_cell(self.grid.grid[row][col], self.mode)

    def toggle_mode(self) -> None:
        self.mode = Mode.PLAYING if self.mode == Mode.SOLVED else Mode.SOLVED

    def reset_puzzle(self) -> None:
        """Update "current" data_map with original values and display"""
        self.grid.reset_to_start()
        self.mode = Mode.PLAYING
        self.write_puzzle()
        self.curr_row = 5
        self.curr_col = 5

    def validate_puzzle(self) -> None:
        """Check "current" data_map for errors against solution
        and mark the relevant cell's as error"""
        self.grid.validate()
        self.mode = Mode.PLAYING
        self.write_puzzle()
        self.curr_row = 5
        self.curr_col = 5

    def valid_move(self, num: int) -> bool:
        return self.grid.is_valid_move(self.curr_row, self.curr_col, num, Mode.PLAYING)

    def get_curr_cell(self) -> Cell:
        return self.grid.grid[self.curr_row][self.curr_col]

    def move_left(self) -> None:
        self.curr_col = self.curr_col - 1 if self.curr_col > 1 else self.curr_col

    def move_down(self) -> None:
        self.curr_row = self.curr_row + 1 if self.curr_row < 9 else self.curr_row

    def move_up(self) -> None:
        self.curr_row = self.curr_row - 1 if self.curr_row > 1 else self.curr_row

    def move_right(self) -> None:
        self.curr_col = self.curr_col + 1 if self.curr_col < 9 else self.curr_col

    def move_mouse_click(self, position: tuple[int, int]) -> None:
        x, y = position
        row = y // C_W
        col = x // C_W
        if 0 < row < 10 and 0 < col < 10:
            self.curr_row = row
            self.curr_col = col

    def save_game(self) -> None:
        self.grid.write_game_status()

    def draw_board(self) -> None:
        """Draw 10 horizontal and 10 vertical lines."""
        self.screen.fill(BG_COLOR)
        for i in range(0, 10):
            if i % 3 == 0:
                pygame.draw.line(  # vertical line
                    self.screen,
                    LINE_COLOR,
                    (C_W + C_W * i, C_W),
                    (C_W + C_W * i, 10 * C_W),
                    6,
                )
                pygame.draw.line(  # horizontal line
                    self.screen,
                    LINE_COLOR,
                    (C_W, C_W + C_W * i),
                    (10 * C_W, C_W + C_W * i),
                    6,
                )
            pygame.draw.line(  # vertical line
                self.screen,
                LINE_COLOR,
                (C_W + C_W * i, C_W),
                (C_W + C_W * i, 10 * C_W),
                1,
            )
            pygame.draw.line(  # horizontal line
                self.screen,
                LINE_COLOR,
                (C_W, C_W + C_W * i),
                (10 * C_W, C_W + C_W * i),
                1,
            )


class GameLoop:
    def __init__(self) -> None:
        self.screen = pygame.display.set_mode((WIDTH, WIDTH))
        pygame.display.set_caption("Sudoku")
        self.board = SudokuBoard(self.screen)

    def run_main_loop(self) -> None:
        run: bool = True
        while run:
            # play game
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    # command mode
                    if event.unicode == ":":
                        self.command_mode()

                    # insert-mode
                    if event.key == pygame.K_i:
                        self.insert_mode()
                        break

                    # marking-mode
                    if event.key == pygame.K_m:
                        self.mark_mode()
                        break

                    # quit game
                    if event.mod & pygame.KMOD_CTRL and event.key == pygame.K_q:
                        run = False
                        pygame.quit()
                        return

                # close button window
                if event.type == pygame.QUIT:
                    run = False
                    pygame.quit()
                    return

    def command_mode(self) -> None:
        """Handle commands in 'command-mode'."""
        run: bool = True
        while run:
            for event in pygame.event.get():
                if event.key == pygame.K_q:  # quit game
                    pygame.quit()
                    sys.exit()

                if event.key == pygame.K_s:
                    self.board.toggle_mode()
                    self.board.write_puzzle()
                    pygame.display.update()
                    run = False
                    break

                if event.key == pygame.K_p:
                    # self.board.prob_toggle = not self.board.prob_toggle
                    self.board.grid.find_probability(True)
                    self.board.write_puzzle()
                    pygame.display.update()
                    run = False
                    break

                if event.key == pygame.K_c:
                    # self.board.prob_toggle = not self.board.prob_toggle
                    self.board.grid.find_probability(False)
                    self.board.write_puzzle()
                    pygame.display.update()
                    run = False
                    break

                if event.key == pygame.K_r:
                    self.board.reset_puzzle()
                    pygame.display.update()
                    run = False
                    break

                # write sudoku data
                if event.key == pygame.K_w:
                    self.board.save_game()
                    run = False
                    break

                # verify current-mode
                if event.key == pygame.K_v:
                    self.board.validate_puzzle()
                    pygame.display.update()
                    run = False
                    break

    def insert_mode(self) -> None:
        """We only update cells in `current` state"""
        curr_cell = self.board.get_curr_cell()
        curr_cell.set_focus(Focus.INSERT)
        self.board.write_cell(curr_cell)
        pygame.display.update()

        run: bool = True
        while run:
            for event in pygame.event.get():
                pygame.display.update()

                # if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                #     curr_cell = self.mouse_navigation(curr_cell)
                #     curr_cell.set_focus(Focus.INSERT)
                #     self.board.write_cell(curr_cell)
                #     continue

                if event.type == pygame.KEYDOWN:
                    # leave insert-mode
                    if event.key == pygame.K_ESCAPE:
                        curr_cell.set_focus(Focus.NONE)
                        self.board.write_cell(curr_cell)
                        run = False
                        break

                    # check for navigation keys
                    if event.key in VALID_NAV_EVENTS:
                        curr_cell = self.keyboard_navigate(
                            curr_cell,
                            event,
                            Focus.INSERT,
                        )
                        continue

                    # update current cell with valid "solved" value
                    if event.unicode == "?":
                        if curr_cell.is_mutable():
                            curr_cell.set_to_solved()
                            self.board.write_cell(curr_cell)
                        continue

                    # clear current cell
                    if event.key == pygame.K_0:
                        if curr_cell.is_mutable():
                            curr_cell.set_val(0)
                            curr_cell.set_invalid(False)
                            curr_cell.set_error(False)
                            self.board.write_cell(curr_cell)
                        continue

                    # valid input
                    if event.key in VALID_DIGIT_EVENTS:
                        if curr_cell.is_mutable():
                            num = event.key - 48
                            if self.board.valid_move(num):
                                curr_cell.set_invalid(False)
                            else:
                                curr_cell.set_invalid(True)
                            curr_cell.set_val(num)
                            self.board.write_cell(curr_cell)
                        continue
            pygame.display.update()

    def mark_mode(self) -> None:
        curr_cell = self.board.get_curr_cell()
        curr_cell.set_focus(Focus.MARK)
        self.board.write_cell(curr_cell)
        pygame.display.update()

        run: bool = True
        while run:
            for event in pygame.event.get():
                pygame.display.update()

                # if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                #     curr_cell = self.mouse_navigation(curr_cell)
                #     curr_cell.set_focus(Focus.MARK)
                #     self.board.write_cell(curr_cell)
                #     # pygame.display.update()
                #     continue

                if event.type == pygame.KEYDOWN:
                    # leave mark-mode
                    if event.key == pygame.K_ESCAPE:
                        curr_cell.set_focus(Focus.NONE)
                        self.board.write_cell(curr_cell)
                        # pygame.display.update()
                        run = False
                        break

                    # check for navigation keys
                    if event.key in VALID_NAV_EVENTS:
                        curr_cell = self.keyboard_navigate(curr_cell, event, Focus.MARK)
                        continue

                    # clear current cell
                    if event.key == pygame.K_0:
                        if curr_cell.is_mutable():
                            curr_cell.clear_marks()
                            curr_cell.set_invalid(False)
                            curr_cell.set_error(False)
                            self.board.write_cell(curr_cell)
                        continue

                    # add 1..5 mark to this cell
                    if event.key in VALID_DIGIT_EVENTS:
                        if curr_cell.is_mutable():
                            num = event.key - 48
                            if self.board.valid_move(num):
                                curr_cell.set_invalid(False)
                                curr_cell.add_mark(num)
                            else:
                                curr_cell.set_invalid(True)
                                curr_cell.add_mark(num)
                            self.board.write_cell(curr_cell)
                        continue
            pygame.display.update()

    def keyboard_navigate(
        self,
        curr_cell: Cell,
        event: pygame.event,
        focus: Focus,
    ) -> Cell:
        """Navigate focused cell in 'insert-mode'.
        Using keys h, j, k, l or left, down, up, right"""
        curr_cell.set_focus(Focus.NONE)
        self.board.write_cell(curr_cell)

        if event.key in [pygame.K_h, pygame.K_LEFT]:
            self.board.move_left()
        if event.key in [pygame.K_j, pygame.K_DOWN]:
            self.board.move_down()
        if event.key in [pygame.K_k, pygame.K_UP]:
            self.board.move_up()
        if event.key in [pygame.K_l, pygame.K_RIGHT]:
            self.board.move_right()

        curr_cell = self.board.get_curr_cell()
        curr_cell.set_focus(focus)
        self.board.write_cell(curr_cell)
        pygame.display.update()
        return curr_cell

    def mouse_navigation(self, curr_cell: Cell) -> Cell:
        # "unfocus current cell"
        curr_cell.set_focus(Focus.NONE)
        self.board.write_cell(curr_cell)

        self.board.move_mouse_click(pygame.mouse.get_pos())
        return self.board.get_curr_cell()


def main() -> None:
    game = GameLoop()
    game.run_main_loop()


if __name__ == "__main__":
    main()
