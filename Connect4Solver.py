import copy
import random
from numpy import inf
from typing import List

from Connect4Board import Colour as Colour
from Connect4Board import Connect4Board as Board

class Connect4Solver:

    # How deep to DFS for minimax algorithm
    DEPTH = 5

    # Scoring for partial lines of chips of the same colour
    # i.e. if 3 red pieces are in a row, score it highly
    # can maybe assign more meaningful values with neural network later
    SCORE_TWO = 1
    SCORE_THREE = 5
    SCORE_MODIFIER_BLOCK_OPPONENT = 2/3

    def __alternate_colour(self, initial_colour):
        if initial_colour == Colour.RED:
            return Colour.YELLOW
        return Colour.RED

    def play(self, game: Board):
        print(game)
        placing_colour = Colour.RED

        while game.still_playing():
            valid_input = False
            while not valid_input:
                input_col = int(input("Input column to place " + placing_colour.value + ": "))
                if input_col >= 0 and input_col < Board.COLUMNS and game.move_available(input_col):
                    valid_input = True
                else:
                    print("Invalid move")
            game.place_chip(placing_colour, input_col)
            print(game)

            if not game.still_playing():
                break

            # AI part
            minimax_move = self.solveBoard(game, Colour.YELLOW)
            game.place_chip(Colour.YELLOW, minimax_move)
            print(game)

        if game.get_winner() == Colour.EMPTY:
            print("Tie game!")
        else:
            print("The winner is " + game.get_winner().name)

    def solveBoard(self, game: Board, player: Colour) -> int:
        """
        Uses a mix of AI techniques to determine the optimal move given a game board
        :param game: The game state to solve
        :param player: The player for whom we want to find the optimal move
        :return: The column in which to play
        """
        # If able to win with this move, do it
        win_now = self.solveNaive(game, player)
        if win_now != -1:
            return win_now

        # Block a potential winning move from the opponent
        lose_next_turn = self.solveNaive(game, self.__alternate_colour(player))
        if lose_next_turn != -1:
            return lose_next_turn

        minimax = self.solve_minimax(game, player, self.DEPTH)
        print ("Minimax values:")
        print(minimax)
        optimal_moves = []
        if player == Colour.RED:
            for col in range(Board.COLUMNS):
                if minimax[col] == max(minimax):
                    optimal_moves.append(col)
        else:
            for col in range(Board.COLUMNS):
                if minimax[col] == min(minimax):
                    optimal_moves.append(col)

        if len(optimal_moves) == 1:
            return optimal_moves[0]

        # if multiple moves tied, pick the one with the best score

        # Based on advantage in game state if we make a move
        attacking_scores = self.solve_scoring(game, player)
        # Based on how much of an advantage the opponent would gain if they made this move
        # we don't want to allow these moves to happen, but will prioritize trying to win by attacking if both equal
        prophylactic_scores = self.solve_scoring(game, self.__alternate_colour(player))

        score_sums = [0] * Board.COLUMNS
        for col in optimal_moves:
            score_sums[col] = int(attacking_scores[col] + prophylactic_scores[col] * self.SCORE_MODIFIER_BLOCK_OPPONENT)

        print("Scores:")
        print(score_sums)

        # Add the move(s) with the highest score from the minimax optimal moves
        optimal_moves_from_scores = []
        for move in optimal_moves:
            if score_sums[move] == max(score_sums):
                optimal_moves_from_scores.append(move)

        if len(optimal_moves_from_scores) == 1:
            return optimal_moves_from_scores[0]

        # If we're still tied, prioritize the middle of the board
        central_proximity = [0] * Board.COLUMNS
        for move in optimal_moves_from_scores:
            central_proximity[move] = Board.COLUMNS / 2 + 1 - abs(3 - move)

        central_moves = []
        for move in optimal_moves_from_scores:
            if central_proximity[move] == max(central_proximity):
                central_moves.append(move)

        if len(central_moves) == 0:
            return central_moves[0]

        # Still tied, just pick randomly
        return random.choice(central_moves)

    def solveNaive(self, game: Board, player: Colour) -> int:
        """
        Check if there is a move for the current player to instantly win the game
        :param game: The board instance
        :param player: The colour of the player to place a chip
        :return: The column that wins the game, -1 if none
        """
        col = 0
        while col < Board.COLUMNS:
            if game.move_available(col):
                new_board = copy.deepcopy(game)
                new_board.place_chip(player, col)
                winner = new_board.get_winner()
                if winner != Colour.EMPTY:
                    return col
            col += 1
        return -1

    def __player_value(self, player: Colour):
        """
        Used for scoring in minimax
        :param player: The player to get a value for
        :return: 1 for RED or -1 for YELLOW
        """
        if player == Colour.RED:
            return 1
        return -1

    def solve_minimax(self, game: Board, player: Colour, depth: int) -> List[float]:
        """
        Determines the values of playing a move in each column via minimax (depth first search)
        Values are 1 or -1 if a victory is found within the depth, 0 if a draw is found or if we reach the end of the
        search without a result
        :param game: The board we are evaluating
        :param player: Whose turn it is
        :param depth: How many nodes down to search
        :return: The list of outcomes, where positive values benefit RED and negative benefit YELLOW
        """
        minimax_values = []
        player_value = self.__player_value(player)
        for col in range(Board.COLUMNS):
            if not game.move_available(col):
                minimax_values.append(-inf * player_value)
                continue
            new_board = copy.deepcopy(game)
            new_board.place_chip(player, col)
            value = self.place_chip_recursive(new_board, self.__alternate_colour(player), depth)
            minimax_values.append(value)
        return minimax_values

    def place_chip_recursive(self, game: Board, player: Colour, depth: int) -> int:
        """
        Depth first search of a tree of possible moves given a position, used for minimax
        Goes down to the specified depth making all possible moves to try to find wins/draws
        Immediately returns if a win or draw is found - alpha-beta pruning to avoid searching more when there
        is already a result
        :param game: The board to solve
        :param player: The player making the move for this iteration
        :param depth: How many levels down to search
        :return: 1 for RED win, -1 for YELLOW win, 0 for draw or inconclusive search
        """
        values = []
        col = 0
        while (col < Board.COLUMNS and game.move_available(col)): # for each child node (available moves)
            new_board = copy.deepcopy(game)
            new_board.place_chip(player, col)
            winner = new_board.get_winner()
            if winner == Colour.EMPTY and depth > 1:
                value = self.place_chip_recursive(new_board, self.__alternate_colour(player), depth -1)
            else: # hit the end of depth of tree or there is already a winner
                if winner == Colour.EMPTY:
                    value = 0
                else:
                    value = self.__player_value(winner)
            values.append(value)

            # alpha-beta pruning (no point checking other nodes)
            if value == self.__player_value(player):
                return value

            col += 1

        # Realistically this stuff is useless since all the values are 0, 1, or -1 (so we will return above)
        if len(values) == 0:
            return 0
        if self.__player_value(player) == 1:
            return max(values)
        if self.__player_value(player) == -1:
            return min(values)

    def solve_scoring(self, game: Board, player: Colour):
        """
        If naive algorithm and minimax can't find a result, score every possible move based on how close
        it brings the player to forming a winning line or to blocking an opposing winning line
        :param game: The board to evaluate
        :param player: Whose turn it is
        :return: A list of scores corresponding to how good each move is at the index (column)
        """
        scores = [0] * Board.COLUMNS
        col = 0
        while col < Board.COLUMNS:
            if game.move_available(col):
                new_board = copy.deepcopy(game)
                new_board.place_chip(player, col)
                scores[col] = self.get_score(new_board, player)
            col += 1
        return scores

    def get_score(self, game: Board, player: Colour):
        """
        For a given position, determines how many adjacent pieces of matching colours in groups of 2 or 3 can
        possibly be added to to form a group of 4 to win
        The potential move has already been made, don't have to think about future
        :param game: The board to evaluate
        :param player: Whose perspective we are evaluating the board from
        :return: The score for this board position2
        """
        score = 0
        for line in game.WINNING_LINES:
            matching_colour_chips_in_line = 0
            for position in line:
                # If the line contains a piece of the other colour, it won't contribute to the score
                if game.get_colour_at_position(position[0], position[1]) == self.__alternate_colour(player):
                    break
                # Figure out how many positions in the line are already desired colour, as opposed to empty
                if game.get_colour_at_position(position[0], position[1]) == player:
                    matching_colour_chips_in_line += 1
            else: # executed after for loop unless we break
                if matching_colour_chips_in_line == 2:
                    score += self.SCORE_TWO
                if matching_colour_chips_in_line == 3:
                    score += self.SCORE_THREE
        return score
