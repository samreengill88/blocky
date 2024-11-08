"""CSC148 Assignment 2

CSC148 Winter 2024
Department of Computer Science,
University of Toronto

This code is provided solely for the personal and private use of
students taking the CSC148 course at the University of Toronto.
Copying for purposes other than this use is expressly prohibited.
All forms of distribution of this code, whether as given or with
any changes, are expressly prohibited.

Authors: Diane Horton, David Liu, Mario Badr, Sophia Huynh, Misha Schwartz,
Jaisie Sin, and Joonho Kim

All of the files in this directory and all subdirectories are:
Copyright (c) Diane Horton, David Liu, Mario Badr, Sophia Huynh,
Misha Schwartz, Jaisie Sin, and Joonho Kim

Module Description:

This file contains the hierarchy of Goal classes and related helper functions.
"""
from __future__ import annotations
# import math
import random
from block import Block
from settings import colour_name, COLOUR_LIST


def generate_goals(num_goals: int) -> list[Goal]:
    """Return a randomly generated list of goals with length <num_goals>.

    Each goal must be randomly selected from the two types of Goals provided
    and must have a different randomly generated colour from COLOUR_LIST.
    No two goals can have the same colour.

    Preconditions:
    - num_goals <= len(COLOUR_LIST)

    >>> goals = generate_goals(3)
    >>> len(goals)
    3
    >>> goals[0].colour != goals[1].colour != goals[2].colour
    True
    """
    available_colours = COLOUR_LIST.copy()
    random.shuffle(available_colours)
    goals = []
    for _ in range(num_goals):
        # choose random color
        goal_color = random.choice(available_colours)
        # choose random goal
        goal = random.choice([PerimeterGoal, BlobGoal])

        # set color of the goal
        goal_instance = goal(goal_color)

        # make sure no two goals with same color
        available_colours.remove(goal_color)
        goals.append(goal_instance)
    return goals


def flatten(block: Block) -> list[list[tuple[int, int, int]]]:
    """Return a two-dimensional list representing <block> as rows and columns of
    unit cells.

    Return a list of lists L, where,
    for 0 <= i, j < 2^{max_depth - self.level}
        - L[i] represents column i and
        - L[i][j] represents the unit cell at column i and row j.

    Each unit cell is represented by a tuple of 3 ints, which is the colour
    of the block at the cell location[i][j].

    L[0][0] represents the unit cell in the upper left corner of the Block.


    """
    if len(block.children) == 0 and block.level == block.max_depth:
        return [[block.colour]]
    elif len(block.children) == 0 and block.level != block.max_depth:

        size = 2 ** (block.max_depth - block.level)
        lst_size_x_size = []
        for i in range(size):
            lst = []
            for _ in range(size):
                lst.append(block.colour)
            lst_size_x_size.append(lst)
        return lst_size_x_size
    else:
        flaten_lst = []
        l_0 = flatten(block.children[0])
        l_1 = flatten(block.children[1])
        l_2 = flatten(block.children[2])
        l_3 = flatten(block.children[3])

        for i in range(len(l_0)):
            l_1[i].extend(l_2[i])
            flaten_lst.append(l_1[i])

        for j in range(len(l_0)):
            l_0[j].extend(l_3[j])
            flaten_lst.append((l_0[j]))

        return flaten_lst


class Goal:
    """A player goal in the game of Blocky.

    This is an abstract class. Only child classes should be instantiated.

    Instance Attributes:
    - colour: The target colour for this goal, that is the colour to which
              this goal applies.
    """
    colour: tuple[int, int, int]

    def __init__(self, target_colour: tuple[int, int, int]) -> None:
        """Initialize this goal to have the given <target_colour>.
        """
        self.colour = target_colour

    def score(self, board: Block) -> int:
        """Return the current score for this goal on the given <board>.

        The score is always greater than or equal to 0.
        """
        raise NotImplementedError

    def description(self) -> str:
        """Return a description of this goal.
        """
        raise NotImplementedError


class PerimeterGoal(Goal):
    """A goal to maximize the presence of this goal's target colour
    on the board's perimeter.
    """

    def score(self, board: Block) -> int:
        """Return the current score for this goal on the given board.

        The score is always greater than or equal to 0.

        The score for a PerimeterGoal is defined to be the number of unit cells
        on the perimeter whose colour is this goal's target colour. Corner cells
        count twice toward the score.
        """
        score_sum = 0

        # flatten lst
        flatten_lst = flatten(board)

        size = len(flatten_lst)

        if len(board.children) == 0:
            if board.colour == self.colour:
                score_sum += 4
        else:
            for i in range(size):  # cols
                for j in range(size):  # rows
                    # check perimeter
                    score_sum += self._calculate_perimeter_cell(i, j, size,
                                                                flatten_lst)

        return score_sum

    def _check_perimeter_cell(self, i: int, j: int, size: int) -> int:
        """ Checks if its perimeter cell.
        """
        return i == 0 or j == 0 or i == size - 1 or j == size - 1

    def _calculate_perimeter_cell(self, i: int, j: int, size: int,
                                  flatten_lst: list) -> int:
        """Calculates the score for perimeter cell.
        """
        if self._check_perimeter_cell(i, j, size):
            if flatten_lst[i][j] == self.colour:
                if self._check_corners(i, j, size):
                    return 2
                else:
                    return 1
        return 0

    def _check_corners(self, i: int, j: int, size: int) -> bool:
        """Check corners of the board.
        """
        return (i == 0 and j == 0) or (i == size - 1 and j == 0) or \
            (i == 0 and j == size - 1) or (i == size - 1 and j == size - 1)

    def description(self) -> str:
        """Return a description of this goal.
        """
        return f'Maximize the presence of {colour_name(self.colour)} on the ' \
               f'perimeter'


class BlobGoal(Goal):
    """A goal to create the largest connected blob of this goal's target
    colour, anywhere within the Block.
    """

    def score(self, board: Block) -> int:
        """Return the current score for this goal on the given board.

        The score is always greater than or equal to 0.

        The score for a BlobGoal is defined to be the total number of
        unit cells in the largest connected blob within this Block.
        """

        flatten_board = flatten(board)
        visited = [[-1 for _ in v_row] for v_row in flatten_board]

        lst = []
        for row_index, row in enumerate(flatten_board):
            for tuple_index, color_value in enumerate(row):
                pos = (row_index, tuple_index)
                if color_value == self.colour:

                    lst.append(self._undiscovered_blob_size(pos,
                                                            flatten_board,
                                                            visited))
        # assert max(lst) >= 0
        return max(lst)

    def _undiscovered_blob_size(self, pos: tuple[int, int],
                                board: list[list[tuple[int, int, int]]],
                                visited: list[list[int]]) -> int:
        """Return the size of the largest connected blob in <board> that
        (a) is of this Goal's target <colour>,
        (b) includes the cell at <pos>, and
        (c) involves only cells that are not in <visited>.

        <board> is the flattened board on which to search for the blob.
        <visited> is a parallel structure (to <board>) that, in each cell,
        contains:
            -1 if this cell has never been visited
            0  if this cell has been visited and discovered
               not to be of the target colour
            1  if this cell has been visited and discovered
               to be of the target colour

        Update <visited> so that all cells that are visited are marked with
        either 0 or 1.

        If <pos> is out of bounds for <board>, return 0.

        """
        target_color = self.colour
        x = pos[0]
        y = pos[1]

        #   check if <pos> is out of bounds for <board>
        if x < 0 or x >= len(board) or y < 0 or y >= len(board):
            return 0
        elif visited[x][y] != -1:
            return 0
        elif board[x][y] != target_color:
            visited[x][y] = 0
            return 0
        else:
            # know: board[x][y] == target_color
            visited[x][y] = 1
            blob_size = 1
            # neighbours of the cell
            cell_neighbours = [(x, y - 1), (x - 1, y), (x, y + 1), (x + 1, y)]

            for cell_x, cell_y in cell_neighbours:
                blob_size += self._undiscovered_blob_size((cell_x, cell_y),
                                                          board, visited)

            return blob_size

    def description(self) -> str:
        """Return a description of this goal.
        """
        return f'Create the largest connected blob of' \
               f' {colour_name(self.colour)}'


if __name__ == '__main__':
    import python_ta

    python_ta.check_all(config={
        'allowed-import-modules': [
            'doctest', 'python_ta', 'random', 'typing', 'block', 'settings',
            'math', '__future__'
        ],
        'max-attributes': 15
    })
