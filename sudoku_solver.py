#!/usr/bin/python
# -*- encoding: utf8 -*-
"""Solves a Sudoku from file "sudoku.txt" or from file given on commandline"""
import sys
from copy import deepcopy
import Tkinter, ttk, tkMessageBox

DEPTH_LIMIT = 40

class SolutionError(BaseException): pass

def read_board(filename):
    board = []
    with open(filename)as f:
        for line in f:
            row = [int(c) for c in line if c in "0123456789"]
            for index, nr in enumerate(row):
                if nr == 0:
                    row[index] = None
            if len(row) == 9:
                board.append(row)
    if len(board) != 9:
        raise IOError("Invalid file!")
    return board

def print_raw(board):
    for i in range(9):
        for j in range(9):
            print board[i][j]

def print_board(board):
    def format_number(nr):
        if isinstance(nr, int):
            return str(nr)
        else:
            return " "
    print "+-------+-------+-------+"
    for row_nr, row in enumerate(board):
        print "|",
        print " ".join([format_number(nr) for nr in row[0:3]]),
        print "|",
        print " ".join([format_number(nr) for nr in row[3:6]]),
        print "|",
        print " ".join([format_number(nr) for nr in row[6:9]]),
        print "|"
        if (row_nr + 1) % 3 == 0:
            print "+-------+-------+-------+"

def get_field(board, i, j):
    i1, j1 = 3 * (i / 3), 3 * (j / 3)
    return board[i1][j1:j1 + 3] + \
           board[i1 + 1][j1:j1 + 3] + \
           board[i1 + 2][j1:j1 + 3]

def analyze_board(board):
    for i in range(9):
        for j in range(9):
            if not isinstance(board[i][j], int):
                board[i][j] = list(range(1,10))
                for nr in board[i]:
                    if isinstance(nr, int) and nr in board[i][j]:
                        board[i][j].remove(nr)
                for nr in zip(*board)[j]:
                    if isinstance(nr, int) and nr in board[i][j]:
                        board[i][j].remove(nr)
                for nr in get_field(board, i, j):
                    if isinstance(nr, int) and nr in board[i][j]:
                        board[i][j].remove(nr)

def is_solved(board):
    for i in range(9):
        for j in range(9):
            if not isinstance(board[i][j], int):
                return False
    return True

def enter_numbers(board):
    counter = 0
    for i in range(9):
        for j in range(9):
            if not isinstance(board[i][j], int) and len(board[i][j]) == 1:
                board[i][j] = board[i][j][0]
                counter += 1
    return counter

def simple_solve(board, depth=0):
    while not is_solved(board):
        analyze_board(board)
        counter = enter_numbers(board)
        if counter == 0:
            return False
    return True

def get_least_unknown(board):
    result = 0, 0
    length = 9
    for i in range(9):
        for j in range(9):
            if not isinstance(board[i][j], int):
                if len(board[i][j]) < length:
                    length = len(board[i][j])
                    result = i, j
    return result

def recursive_solve(board, solutions, depth=0):
    if depth > DEPTH_LIMIT:
        raise SolutionError()
    board = deepcopy(board)
    if simple_solve(board, depth + 1):
        solutions.append(board)
        return True
    else:
        i, j = get_least_unknown(board)
        for choice in board[i][j]:
            new_board = deepcopy(board)
            new_board[i][j] = choice
            if recursive_solve(new_board, solutions, depth=depth + 1):
                break

def solve(board):
    """Solves a given Sudoku
    
    Returns a list of solutions to the given sudoku. Both the solutions and the
    initial sudoku are two-dimensional lists fo dimension 9x9 containing only
    integer numbers from 1 to 9. The given sudoku can contain zeros as well,
    denoting empty cells.
    
    """
    solutions = []
    recursive_solve(board, solutions)
    return solutions


class TkBoard(ttk.Frame):
    def __init__(self, master=None, board=None, editable=False):
        ttk.Frame.__init__(self, master)
        self.pack()
        frame = ttk.Frame(self)
        frame.pack(padx=5, pady=5)
        self.entries = []
        for i in range(9):
            row = []
            row_frame = ttk.Frame(frame)
            row_frame.pack()
            for j in range(9):
                entry_var = Tkinter.StringVar()
                entry = ttk.Entry(row_frame,
                                  width = 2,
                                  justify = "center",
                                  textvariable = entry_var)
                if not editable:
                    entry["state"] = "readonly"
                entry.pack(side = "left")
                if board is not None and \
                            isinstance(board[i][j], int) and \
                            board[i][j] > 0:
                    entry_var.set(board[i][j])
                row.append(entry_var)
            self.entries.append(row)
        

class GUI(ttk.Frame):
    def __init__(self, master=None, board=None):
        ttk.Frame.__init__(self, master)
        self.master.title("Sudoku-Löser")
        self.pack()
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(padx=5, pady=5)
        self.tkboard = TkBoard(self, board=board, editable=True)
        self.notebook.add(self.tkboard, text="Aufgabe")
        self.button_solve = ttk.Button(self,
                                       text = "Sudoku lösen",
                                       width = 20,
                                       command = self.solve)
        self.button_solve.pack(padx=5, pady=5)
    
    def solve(self):
        # verify input:
        board = []
        for i in range(9):
            row = []
            for j in range(9):
                entry = self.tkboard.entries[i][j].get()
                try:
                    if entry == "":
                        row.append(None)
                    elif 1 <= int(entry) <= 9:
                        row.append(int(entry))
                    else:
                        raise ValueError()
                except ValueError as e:
                    tkMessageBox.showerror(
                            title = "Fehler",
                            message = "Ungültiger Wert in Feld "
                                      "({0},{1})".format(i+1, j+1)
                            )
                    return False
            board.append(row)
        # clear old solutions:
        for nr, tab in enumerate(self.notebook.tabs()):
            if nr > 0:
                self.notebook.forget(tab)
        try:
            # solve:
            solutions = solve(board)
            # display solutions:
            if len(solutions) == 0:
                tkMessageBox.showerror(title = "Fertig", message = "Keine Lösung gefunden.")
            elif len(solutions) == 1:
                tkMessageBox.showinfo(title = "Fertig", message = "Lösung gefunden.")
                self.notebook.add(TkBoard(self, board=solutions[0]), text="Lösung")
            elif len(solutions) <= 10:
                tkMessageBox.showinfo(title = "Fertig", message = "{0} Lösungen gefunden.".format(len(solutions)))
                for nr, solution in enumerate(solutions):
                    tkboard = TkBoard(self, board=solution)
                    self.notebook.add(tkboard, text="Lösung {0}".format(nr+1))
                    print_board(solution)
            else:
                tkMessageBox.showinfo(title = "Fertig", message = "{0} Lösungen gefunden.\nDie ersten zehn Lösungen werden angezeigt.".format(len(solutions)))
                for nr, solution in enumerate(solutions):
                    tkboard = TkBoard(self, board=solution)
                    self.notebook.add(tkboard, text="Lösung {0}".format(nr+1))
                    if nr >= 9:
                        break
        except SolutionError as e:
            tkMessageBox.showerror(title = "Abbruch", message = "Zu wenige Informationen.")


if __name__ == "__main__":
    if len(sys.argv) == 3 and "--cli" in sys.argv:
        filename = sys.argv[2]
        b = read_board(filename)
        print "Aufgabe:"
        print_board(b)
        solutions = solve(b)
        if len(solutions) == 0:
            print "Keine Lösung gefunden!"
        elif len(solutions) == 1:
            print "Lösung:"
            print_board(solutions[0])
        else:
            print "{0} Lösungen gefunden:".format(len(solutions))
            for nr, each in enumerate(solutions):
                print "{0}. Lösung".format(nr + 1)
                print_board(each)
    else:
        if len(sys.argv) == 2:
            board = read_board(sys.argv[1])
        else:
            board = None
        root = Tkinter.Tk()
        gui = GUI(master=root, board=board)
        gui.mainloop()
        root.destroy()
