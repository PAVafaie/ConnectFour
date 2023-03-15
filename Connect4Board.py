import copy
from enum import Enum
from collections import Counter
from typing import List, Tuple


class Colour(Enum):
    EMPTY = "⚫"
    RED = "🔴"
    YELLOW = "🟡"


class Connect4Board:
    ROWS, COLUMNS = 6, 7

    WINNING_LINES = None
    WINNING_LINES_BY_POSITION = None

    def __init__(self, moves_made = 0, last_move = (-1, -1), board = None, column_chip_count = None, available_moves = [True] * COLUMNS):
        """
        Constructor for Connect4Board
        self.moves_made used for determining game state
        self.winner game state
        self.board tracks the chips placed in the game
        self.column_chip_count tracks how many chips are stacked in each column
        self.available_moves tracks which columns still have space to place a chip
        self.winning_lines combinations of 4 adjacent board slots that constitute a win
        """
        self.moves_made = moves_made
        self.last_move = last_move
        self.winner = Colour.EMPTY

        if board is not None:
            self.board = board
        else:
            self.board = [[Colour.EMPTY for i in range(self.COLUMNS)] for j in range(self.ROWS)]

        if column_chip_count is not None:
            self.column_chip_count = column_chip_count
        else:
            columns = []
            for col in range(self.COLUMNS):
                columns.append(col)
            self.column_chip_count = Counter(columns)
            for key in self.column_chip_count.keys():
                self.column_chip_count[key] = 0

        self.available_moves = available_moves

        # Only generate these static variables once for speed
        if Connect4Board.WINNING_LINES is None:
            Connect4Board.WINNING_LINES = self.generate_winning_lines()
        if Connect4Board.WINNING_LINES_BY_POSITION is None:
            Connect4Board.WINNING_LINES_BY_POSITION = [[None for i in range(self.COLUMNS)] for j in range(self.ROWS)]
            for i in range(Connect4Board.ROWS):
                for j in range(Connect4Board.COLUMNS):
                    Connect4Board.WINNING_LINES_BY_POSITION[i][j] = self.generate_winning_lines_for_positions(i, j)

        self.winning_lines = self.WINNING_LINES
        self.winning_lines_by_positions = self.WINNING_LINES_BY_POSITION

    def __str__(self):
        board_string = ""
        for i in range(self.ROWS):
            for j in range(self.COLUMNS):
                board_string += self.board[i][j].value
            board_string += "\n"
        return board_string

    def __deepcopy__(self, memodict={}):
        last_move = (self.last_move[0], self.last_move[1])
        new_board = [[col for col in row] for row in self.board]
        new_column_chip_count = copy.copy(self.column_chip_count)
        new_available_moves = [available for available in self.available_moves]
        return Connect4Board(self.moves_made, last_move, new_board, new_column_chip_count, new_available_moves)

    def move_available(self, column: int) -> bool:
        """
        Checks if a move is available
        :param column: The column to place the chip
        :return: Boolean, whether the column has room to play
        """
        return self.available_moves[column]

    def place_chip(self, player: Colour, column: int) -> None:
        """
        Place a chip at the bottom of the selected column
        Simulate "dropping" the chip, should go to lowest (highest number) unoccupied row index
        :param player: the colour of the chip to place
        :param column: which column index to place in
        :return: None
        """
        row_placed_at = self.ROWS - self.column_chip_count[column] - 1
        if row_placed_at < 0:
            raise ValueError("Tried to place chip in full column " + str(column))
        self.board[row_placed_at][column] = player
        self.__update_column_availability(column)
        self.moves_made += 1
        self.last_move = (row_placed_at, column)
        self.winner = self.check_winner_from_last_move()

    def __update_column_availability(self, column: int) -> None:
        """
        Called after placing a chip, increments column chip count
        If column is now full set column not available for moves
        :param column: which column the move was made in
        :return: None
        """
        self.column_chip_count[column] += 1
        if self.column_chip_count[column] == self.ROWS:
            self.available_moves[column] = False

    def check_winner_from_last_move(self) -> Colour:
        """
        Checks the winning lines we have stored for each position, for the position of the last move made
        Faster implementation that doesn't check entire board, needed for minimax
        :return: Which colour of player has won the game, EMPTY if none
        """
        if self.last_move == (-1, -1):
            return Colour.EMPTY
        last_row = self.last_move[0]
        last_col = self.last_move[1]
        last_move_colour = self.board[last_row][last_col]
        for line in self.winning_lines_by_positions[last_row][last_col]:
            # where line[0][0] is the row of the first coordinate, line[0][1] is the col of the first coordinate
            if self.board[line[0][0]][line[0][1]] == last_move_colour and \
                    self.board[line[1][0]][line[1][1]] == last_move_colour and \
                    self.board[line[2][0]][line[2][1]] == last_move_colour:
                return last_move_colour
        return Colour.EMPTY

    def check_winner_from_board(self) -> Colour:
        """
        Evaluates the entire board to see if the game has been won
        :return: Which colour of player has won the game, EMPTY if none
        """
        for line in self.winning_lines:
            # where line[0][0] is the row of the first coordinate, line[0][1] is the col of the first coordinate
            if self.board[line[0][0]][line[0][1]] != Colour.EMPTY and \
                    self.board[line[0][0]][line[0][1]] == self.board[line[1][0]][line[1][1]] and \
                    self.board[line[1][0]][line[1][1]] == self.board[line[2][0]][line[2][1]] and \
                    self.board[line[2][0]][line[2][1]] == self.board[line[3][0]][line[3][1]]:
                return self.board[line[0][0]][line[0][1]]
        return Colour.EMPTY

    def still_playing(self):
        """
        Getter, checks if the game is still ongoing
        :return: True if the game has yet to be won or tied, False if it is over
        """
        if self.winner != Colour.EMPTY or self.moves_made == self.ROWS * self.COLUMNS:
            return False
        return True

    def get_winner(self):
        return self.winner

    def get_colour_at_position(self, row, column):
        return self.board[row][column]

    def get_moves_made(self):
        return self.moves_made

    @staticmethod
    def generate_winning_lines() -> List[List[Tuple[int, int]]]:
        '''
        Generates lists of 4 tuples, where the tuples have the board coordinates of 4-in-a-row lines
        of form [[(0, 0), (0, 1), (0, 2), (0, 3)], [(0, 1), (0, 2), (0, 3), (0, 4)], [(0, 2), (0, 3), (0, 4), (0, 5)], ...
        :return: List of lists, where the inner lists have 4 coordinates which go together to form a win
        '''
        horizontal_lines = []
        for row in range(Connect4Board.ROWS):
            for starting_col in range(Connect4Board.COLUMNS - 3):
                horizontal_lines.append([(row, starting_col), (row, starting_col + 1),
                                         (row, starting_col + 2), (row, starting_col + 3)])
        vertical_lines = []
        for col in range(Connect4Board.COLUMNS):
            for starting_row in range(Connect4Board.ROWS - 3):
                vertical_lines.append([(starting_row, col), (starting_row + 1, col),
                                       (starting_row + 2, col), (starting_row + 3, col)])
        diagonal_falling_lines = []
        for starting_row in range(Connect4Board.ROWS - 3):
            for starting_col in range(Connect4Board.COLUMNS - 3):
                diagonal_falling_lines.append([(starting_row, starting_col), (starting_row + 1, starting_col + 1),
                                               (starting_row + 2, starting_col + 2),
                                               (starting_row + 3, starting_col + 3)])
        diagonal_rising_lines = []
        for starting_row in range(4, Connect4Board.ROWS):
            for starting_col in range(Connect4Board.COLUMNS - 3):
                diagonal_rising_lines.append([(starting_row, starting_col), (starting_row - 1, starting_col + 1),
                                              (starting_row - 2, starting_col + 2),
                                              (starting_row - 3, starting_col + 3)])
        return horizontal_lines + vertical_lines + diagonal_falling_lines + diagonal_rising_lines

    @staticmethod
    def generate_winning_lines_for_positions(row: int, column: int) -> List[List[Tuple[int, int]]]:
        """
        Generates a list of lines (lists) where each line is a winning line, excludes the position itself
        Winning lines are included in this list if the line contains the position
        We use these winning lines to be able to check if the game has been won based on the last move
        can just check these lines rather than the entire board

        >>> generate_winning_lines_for_positions(0, 0)
        [[(0, 1), (0, 2), (0, 3)], [(1, 0), (2, 0), (3, 0)], [(1, 1), (3, 2), (3, 3)]]

        :param row: The row of the position we want winning lines for
        :param column: The column of the position we want winning lines for
        :return: List of winning lines for the position, less the position
        """
        winning_lines = []
        for line in Connect4Board.WINNING_LINES:
            if (row, column) in line:
                added_line = line[:]
                added_line.remove((row, column))
                winning_lines.append(added_line)
        return winning_lines
