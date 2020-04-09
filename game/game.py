import kivy

kivy.require("1.11.1")

from kivy.config import Config

Config.set("graphics", "width", "720")
Config.set("graphics", "height", "800")

from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.properties import ObjectProperty, ListProperty
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label


class CellDigit(TextInput):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def keyboard_on_key_down(self, window, keycode, text, modifiers):
        key, key_str = keycode
        if key_str in ["escape", "tab"]:
            return super().keyboard_on_key_down(window, keycode, text, modifiers)
        return self.parent.on_keyboard(key_str)


class Cell(RelativeLayout):
    grid = ObjectProperty(None)
    digit = ObjectProperty(None)
    bg_color = ListProperty([1, 1, 1, 1])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.guesses = {}
        for i in range(9):
            label = Label(color=(0, 0, 0, 0))
            self.guesses[str(i + 1)] = label
            self.grid.add_widget(label)
            label.text = str(i + 1)
        self.initial = False
        self.row = None
        self.col = None

    def on_keyboard(self, key_str):
        if key_str in "123456789":
            if self.digit.text:
                return True
            guess = self.guesses[key_str]
            guess.color[-1] = 1 - guess.color[-1]
        elif key_str == "enter":
            the_guess = None
            for guess in self.guesses.values():
                if guess.color[-1] == 1:
                    if the_guess is not None:
                        return True
                    the_guess = guess
            if the_guess is not None:
                self.digit.text = the_guess.text
                the_guess.color[-1] = 0
        elif key_str == "backspace" and not self.initial:
            self.clean()
        return True

    def clean(self):
        self.digit.text = ""
        for guess in self.guesses.values():
            guess.color[-1] = 0


class Board(GridLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cells = {}
        for row in range(9):
            self.cells[row] = {}
            for col in range(9):
                cell = Cell()
                cell.row = row
                cell.col = col
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
        new_board = [[5, 1, 7, 6, 0, 0, 0, 3, 4], [2, 8, 9, 0, 0, 4, 0, 0, 0],
                      [3, 4, 6, 2, 0, 5, 0, 9, 0], [6, 0, 2, 0, 0, 0, 0, 1, 0],
                      [0, 3, 8, 0, 0, 6, 0, 4, 7], [0, 0, 0, 0, 0, 0, 0, 0, 0],
                      [0, 9, 0, 0, 0, 0, 0, 7, 8], [7, 0, 3, 4, 0, 0, 5, 6, 0],
                      [0, 0, 0, 0, 0, 0, 0, 0, 0]]
        for i, row in enumerate(new_board):
            for j, num in enumerate(row):
                cell = self.cells[i][j]
                cell.clean()
                if num > 0:
                    cell.digit.text = str(num)
                    cell.bg_color = [0.8, 0.8, 0.8, 1]
                    cell.initial = True


class Game(FloatLayout):
    pass


class SudokuApp(App):
    def build(self):
        game = Game()
        return game


if __name__ == "__main__":
    SudokuApp().run()
