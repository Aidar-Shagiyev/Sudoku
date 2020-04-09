import kivy

kivy.require("1.11.1")

from kivy.config import Config

Config.set("graphics", "width", "720")
Config.set("graphics", "height", "800")

from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.properties import ObjectProperty, ListProperty, BooleanProperty
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.graphics import Line
from kivy.graphics import Color


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
                board.cells[i][cell.col].bg_color[-1] *= alpha_change
                board.cells[i][cell.col].bg_color[1] *= green_change
                board.cells[cell.row][i].bg_color[-1] *= alpha_change
                board.cells[cell.row][i].bg_color[1] *= green_change
            else:
                board.cells[i][cell.col].bg_color[-1] /= alpha_change
                board.cells[i][cell.col].bg_color[1] /= green_change
                board.cells[cell.row][i].bg_color[-1] /= alpha_change
                board.cells[cell.row][i].bg_color[1] /= green_change

        if self.text:
            for row in range(9):
                for col in range(9):
                    other_cell = board.cells[row][col]
                    if other_cell.digit.text and other_cell.digit.text == self.text:
                        other_cell.highlight = True
                    else:
                        other_cell.highlight = False



class Cell(RelativeLayout):
    grid = ObjectProperty(None)
    digit = ObjectProperty(None)
    bg_color = ListProperty([0.8, 0.8, 0.8, 1])
    highlight = BooleanProperty(False)
    guesses = ListProperty([0] * 9)

    def __init__(self, row, col, **kwargs):
        super().__init__(**kwargs)
        self.labels = []
        for i in range(9):
            label = Label(color=(0, 0, 0, self.guesses[i]), text=str(i + 1))
            self.grid.add_widget(
                label
            )
            self.labels.append(label)
        self.initial = False
        self.row = row
        self.col = col
        self.outline = None

    def on_guesses(self, instance, value):
        for guess, label in zip(value, self.labels):
            label.color[-1] = guess

    def on_keyboard(self, key_str):
        if key_str in "123456789":
            if self.digit.text:
                return True
            self.guesses[int(key_str) - 1] = 1 - self.guesses[int(key_str) - 1]
        elif key_str == "enter":
            if sum(self.guesses) != 1:
                return True
            guess_index = self.guesses.index(1)
            self.guesses[guess_index] = 0
            self.digit.text = str(guess_index + 1)
            self.digit.focused = False
        elif key_str == "backspace" and not self.initial:
            self.clean()
        return True

    def clean(self):
        self.digit.text = ""
        self.guesses = self.__class__.guesses.defaultvalue


class Board(GridLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cells = {}
        for row in range(9):
            self.cells[row] = {}
            for col in range(9):
                cell = Cell(row, col)
                self.cells[row][col] = cell
        self.boxes = {}
        for box_row in range(3):
            self.boxes[box_row] = {}
            for box_col in range(3):
                box = GridLayout(rows=3, cols=3, spacing=2)
                self.boxes[box_row][box_col] = box
                self.add_widget(box)
                for row in range(box_row * 3, box_row * 3 + 3):
                    for col in range(box_col * 3, box_col * 3 + 3):
                        box.add_widget(self.cells[row][col])

    def new_game(self):
        new_board = [
            [5, 1, 7, 6, 0, 0, 0, 3, 4],
            [2, 8, 9, 0, 0, 4, 0, 0, 0],
            [3, 4, 6, 2, 0, 5, 0, 9, 0],
            [6, 0, 2, 0, 0, 0, 0, 1, 0],
            [0, 3, 8, 0, 0, 6, 0, 4, 7],
            [0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 9, 0, 0, 0, 0, 0, 7, 8],
            [7, 0, 3, 4, 0, 0, 5, 6, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0],
        ]
        for i, row in enumerate(new_board):
            for j, num in enumerate(row):
                cell = self.cells[i][j]
                cell.clean()
                if num > 0:
                    cell.digit.text = str(num)
                    cell.bg_color[0] *= 0.8
                    cell.bg_color[1] *= 0.8
                    cell.bg_color[2] *= 0.8
                    cell.initial = True


class Game(FloatLayout):
    pass


class SudokuApp(App):
    def build(self):
        game = Game()
        return game


if __name__ == "__main__":
    SudokuApp().run()
