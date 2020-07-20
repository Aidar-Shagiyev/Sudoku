import itertools
import random
import numpy as np
import kivy

kivy.require("1.11.1")

from kivy.config import Config

Config.set("graphics", "width", "720")
Config.set("graphics", "height", "800")

from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.properties import (
    ObjectProperty,
    ListProperty,
    BooleanProperty,
    StringProperty,
    NumericProperty,
    DictProperty,
)
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.clock import Clock


class CellDigit(TextInput):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def keyboard_on_key_down(self, window, keycode, text, modifiers):
        key, key_str = keycode
        if key_str in ["escape", "tab"]:
            return super().keyboard_on_key_down(window, keycode, text, modifiers)
        return self.parent.on_keyboard(key_str)

    def on_focus(self, instance, value):
        alpha_change = 0.9
        green_change = 0.9

        cell = self.parent
        board = cell.parent.parent

        for i in range(9):
            if value:
                board.cells[i, cell.col].bg_color[-1] *= alpha_change
                board.cells[i, cell.col].bg_color[1] *= green_change
                board.cells[cell.row, i].bg_color[-1] *= alpha_change
                board.cells[cell.row, i].bg_color[1] *= green_change
            else:
                board.cells[i, cell.col].bg_color[-1] /= alpha_change
                board.cells[i, cell.col].bg_color[1] /= green_change
                board.cells[cell.row, i].bg_color[-1] /= alpha_change
                board.cells[cell.row, i].bg_color[1] /= green_change

        if value and self.text and not board.solving:
            board.highlight_digit = self.text


class Cell(RelativeLayout):
    grid = ObjectProperty(None)
    digit = ObjectProperty(None)
    bg_color = ListProperty([0.8, 0.8, 0.8, 1])
    guesses = DictProperty({num: False for num in "123456789"})
    collisions = ListProperty([])
    collided = BooleanProperty(False)
    highlighted = NumericProperty(0)
    initial = BooleanProperty(False)
    backtracked = BooleanProperty(False)

    def __init__(self, row, col, **kwargs):
        super().__init__(**kwargs)
        self.labels = []
        for num in "123456789":
            label = Label(color=(0, 0, 0, self.guesses[num]), text=num)
            self.grid.add_widget(label)
            self.labels.append(label)
        self.row = row
        self.col = col
        self.outline = None

    def on_guesses(self, instance, value):
        for num, label in zip("123456789", self.labels):
            label.color[-1] = self.guesses[num]

    def on_collided(self, instance, value):
        gb_color_shift = 0.5
        if self.collided:
            self.bg_color[1] *= gb_color_shift
            self.bg_color[2] *= gb_color_shift
        else:
            self.bg_color[1] /= gb_color_shift
            self.bg_color[2] /= gb_color_shift

    def on_initial(self, instance, value):
        color_shift = 0.8
        if value:
            self.bg_color[0] *= color_shift
            self.bg_color[1] *= color_shift
            self.bg_color[2] *= color_shift
        else:
            self.bg_color[0] /= color_shift
            self.bg_color[1] /= color_shift
            self.bg_color[2] /= color_shift

    def on_backtracked(self, instance, value):
        color_shift = 0.7
        if value:
            self.bg_color[2] *= color_shift
        else:
            self.bg_color[2] /= color_shift

    def on_keyboard(self, key_str):
        if not key_str:
            return True
        if key_str in "123456789":
            if self.digit.text:
                return True
            self.guesses[key_str] = not self.guesses[key_str]
        elif key_str == "enter":
            guesses = [num for num, guess in self.guesses.items() if guess]
            if len(guesses) != 1:
                return True
            num = guesses[0]
            self.guesses[num] = 0
            self.digit.text = num

            # Check collisions:
            box = self.parent
            board = box.parent
            for i in range(9):
                for other in [
                    board.cells[self.row, i],
                    board.cells[i, self.col],
                    box.children[i],
                ]:
                    if other is not self and other.digit.text == self.digit.text:
                        other.collisions.append(self)
                        self.collisions.append(other)

            self.digit.focused = False
            board.highlight_digit = self.digit.text
        elif key_str == "backspace" and not self.initial:
            self.clean()
        return True

    def clean(self):
        self.digit.text = ""
        self.guesses = self.__class__.guesses.defaultvalue
        for other in self.collisions:
            other.collisions.remove(self)
        self.collisions = []
        self.initial = False


class Board(GridLayout):
    highlight_digit = StringProperty(None)
    new_game_menu = BooleanProperty(True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cells = {}
        for row, col in itertools.product(range(9), repeat=2):
            cell = Cell(row, col)
            self.cells[row, col] = cell
        self.boxes = {}
        for box_row, box_col in itertools.product(range(3), repeat=2):
            box = GridLayout(rows=3, cols=3, spacing=2)
            self.boxes[box_row, box_col] = box
            self.add_widget(box)
            for row in range(box_row * 3, box_row * 3 + 3):
                for col in range(box_col * 3, box_col * 3 + 3):
                    box.add_widget(self.cells[row, col])
        self.solving = False
        self._saved = []

    def get_cells(self, text):
        for cell in self.cells.values():
            if cell.digit.text == text:
                yield cell

    def new_game(self, mode, dt):
        mode_deletes = {"easy": 40, "medium": 47, "hard": 55}
        assert mode in mode_deletes

        self.new_game_menu = False
        self.highlight_digit = ""
        self.solving = False
        self._saved = []
        board = next(self._random_solve(np.zeros(shape=(9, 9), dtype=int)))

        # Remove some numbers.
        delete_count = 0
        for row, col in random.sample(
            list(itertools.product(range(9), repeat=2)), 9 * 9
        ):
            new_board = board.copy()
            new_board[row, col] = 0
            deleted = (row, col, board[row, col])
            if self._has_unique_solve(new_board, deleted):
                board = new_board
                delete_count += 1
                if delete_count > mode_deletes[mode]:
                    break

        for (row, col), cell in self.cells.items():
            cell.clean()
            num = board[row, col]
            if num > 0:
                cell.digit.text = str(num)
                cell.initial = True
        print("New Game!")

    def solve(self):
        self.solving = True
        for cell in self.cells.values():
            if not cell.digit.text:
                cell.guesses = {num: True for num in "123456789"}

        nums = list("123456789")

        def _highlight(dt):
            self.highlight_digit = nums[0]
            Clock.schedule_once(_resolve_guesses, 0.2)

        def _resolve_guesses(dt):
            num = nums.pop(0)
            for cell in self.get_cells(num):
                for i in range(9):
                    self.cells[cell.row, i].guesses[num] = False
                    self.cells[i, cell.col].guesses[num] = False
                    cell.parent.children[i].guesses[num] = False
            if nums:
                Clock.schedule_once(_highlight, 0.2)
            else:
                self.highlight_digit = ""
                Clock.schedule_once(_pick_cell, 0.2)

        def _pick_cell(dt):
            candidates = {x: [] for x in range(10)}
            for cell in self.cells.values():
                possible = sum(cell.guesses.values())
                if not cell.digit.text:
                    candidates[possible].append(cell)
            for x in range(10):
                if candidates[x]:
                    self._pick = candidates[x][0]
                    self._pick.digit.focused = True
                    Clock.schedule_once(_eval_pick, 0.2)
                    return
            else:
                for cell in self.cells.values():
                    cell.backtracked = False
                    cell.digit.focused = False
                self.solving = False
                print("Done!")

        def _eval_pick(dt):
            cell = self._pick
            if cell.backtracked:
                self._load()
            guesses = [num for num, guess in cell.guesses.items() if guess]
            if len(guesses) == 0:
                assert not cell.digit.text
                cell.collisions.append(0)
                cell.backtracked = False
                self._saved[-1][1].digit.focused = True
                self._pick = self._saved[-1][1]
                Clock.schedule_once(_eval_pick, 0.2)
                return
            num = guesses[0]
            cell.guesses[num] = 0
            cell.backtracked = False
            if len(guesses) > 1:
                self._save(cell)
                cell.backtracked = True
                cell.guesses = {x: 0 for x in cell.guesses}
            cell.digit.text = num
            nonlocal nums
            nums = [num]
            _resolve_guesses(0)

        Clock.schedule_once(_highlight, 0.2)

    def _save(self, backtracked_cell):
        saved_cells = {}
        for (row, col), cell in self.cells.items():
            to_save = [cell.digit.text, cell.collisions.copy(), cell.guesses.copy()]
            saved_cells[row, col] = to_save
        self._saved.append((saved_cells, backtracked_cell))

    def _load(self):
        saved_cells = self._saved.pop()[0]
        for (row, col), cell in self.cells.items():
            from_save = saved_cells[row, col]
            cell.digit.text = from_save[0]
            cell.collisions = from_save[1]
            cell.guesses = from_save[2]

    def _random_solve(self, board: np.array):
        """Generate solves of the board in random order using backtracking."""
        zeros = np.argwhere(board == 0)
        if len(zeros) == 0:
            yield board
            return
        row, col = zeros[0]
        disallowed = set()
        for i in range(9):
            disallowed.add(board[row, i])
            disallowed.add(board[i, col])
            disallowed.add(board[row // 3 * 3 + i // 3, col // 3 * 3 + i % 3])
        allowed = set(range(1, 10)) - disallowed
        for num in random.sample(allowed, len(allowed)):
            new_board = board.copy()
            new_board[row, col] = num
            yield from self._random_solve(new_board)

    def _has_unique_solve(self, board: np.array, cell):
        """Check if the board has more solves when the cell is deleted."""

        def _resolve_guesses(board, guesses, row, col, num):
            guesses[row, :, num - 1] = np.logical_or(False, board[row, :])
            guesses[:, col, num - 1] = np.logical_or(False, board[:, col])
            box_row = row // 3 * 3
            box_col = col // 3 * 3
            guesses[
                box_row : box_row + 3, box_col : box_col + 3, num - 1
            ] = np.logical_or(
                False, board[box_row : box_row + 3, box_col : box_col + 3]
            )

        board = board.copy()
        guesses = np.ones(shape=(9, 9, 9), dtype=bool)
        for (row, col), num in np.ndenumerate(board):
            if num:
                _resolve_guesses(board, guesses, row, col, num)
        row, col, num = cell
        guesses[row, col, num - 1] = False
        backtrack = []
        while True:
            guesses_sum = guesses.sum(axis=2)
            row, col = np.unravel_index(guesses_sum.argmin(), guesses_sum.shape)
            possibles = np.argwhere(guesses[row, col]).flatten()
            if len(possibles) == 0:
                if not backtrack:
                    return True
                board, guesses = backtrack.pop()
                continue
            num = possibles[0] + 1
            if len(possibles) > 1:
                guesses[row, col, num - 1] = False
                backtrack.append((board.copy(), guesses.copy()))
            board[row, col] = num
            guesses[row, col] = True
            _resolve_guesses(board, guesses, row, col, num)
            if board.all():
                return False


class Game(FloatLayout):
    pass


class SudokuApp(App):
    def build(self):
        game = Game()
        return game


if __name__ == "__main__":
    SudokuApp().run()
