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

This file contains the hierarchy of player classes.
"""
from __future__ import annotations
import random
import pygame

from block import Block
from goal import Goal, generate_goals

from actions import Action, KEY_ACTION, ROTATE_CLOCKWISE, \
    ROTATE_COUNTER_CLOCKWISE, \
    SWAP_HORIZONTAL, SWAP_VERTICAL, SMASH, PASS, PAINT, COMBINE


def create_players(num_human: int, num_random: int, smart_players: list[int]) \
        -> list[Player]:
    """Return a new list of Player objects.

    <num_human> is the number of human player, <num_random> is the number of
    random players, and <smart_players> is a list of difficulty levels for each
    SmartPlayer that is to be created.

    The list should contain <num_human> HumanPlayer objects first, then
    <num_random> RandomPlayer objects, then the same number of SmartPlayer
    objects as the length of <smart_players>. The difficulty levels in
    <smart_players> should be applied to each SmartPlayer object, in order.

    Player ids are given in the order that the players are created, starting
    at id 0.

    Each player is assigned a random goal.
    """
    all_players = []
    player_id = 0
    goals = generate_goals(num_human + num_random + len(smart_players))

    for _ in range(num_human):
        random.shuffle(goals)
        choose_goal_human = random.choice(goals)
        all_players.append(HumanPlayer(player_id, choose_goal_human))
        goals.remove(choose_goal_human)
        player_id += 1

    for _ in range(num_random):
        random.shuffle(goals)
        choose_goal_random = random.choice(goals)
        all_players.append(RandomPlayer(player_id, choose_goal_random))
        goals.remove(choose_goal_random)
        player_id += 1

    for smart_player in smart_players:
        random.shuffle(goals)
        choose_gaol_smart = random.choice(goals)
        all_players.append(
            SmartPlayer(player_id, choose_gaol_smart, smart_player))
        goals.remove(choose_gaol_smart)
        player_id += 1

    return all_players


def _get_block(block: Block, location: tuple[int, int], level: int) -> \
        Block | None:
    """Return the Block within <block> that is at <level> and includes
    <location>. <location> is a coordinate-pair (x, y).

    A block includes all locations that are strictly inside it, as well as
    locations on the top and left edges. A block does not include locations that
    are on the bottom or right edge.

    If a Block includes <location>, then so do its ancestors. <level> specifies
    which of these blocks to return. If <level> is greater than the level of
    the deepest block that includes <location>, then return that deepest block.

    If no Block can be found at <location>, return None.

    Preconditions:
        - block.level <= level <= block.max_depth
    """

    # check if block includes location
    block_left = block.position[0]
    block_right = block.position[0] + block.size
    block_top = block.position[1]
    block_bottom = block.position[1] + block.size
    if not (block_left <= location[0] < block_right
            and block_top <= location[1] < block_bottom):
        return None
    else:
        if block.level == level:
            return block
        for child in block.children:
            child_block = _get_block(child, location, level)
            if child_block:
                return child_block
        return None
    # return None


def _is_valid_move(player: Player, board_copy: Block,
                   random_move: Action) -> bool:
    """Checks if the move is valid.
    """
    if random_move.short_name == 'paint':
        if not random_move.apply(board_copy, {'colour': player.goal.colour}):
            return False
        else:
            return True
    else:
        if not random_move.apply(board_copy, {}):
            return False
        else:
            return True


class Player:
    """A player in the Blocky game.

    This is an abstract class. Only child classes should be instantiated.

    Instance Attributes:
    - id: This player's number.
    - goal: This player's assigned goal for the game.
    - penalty: The penalty accumulated by this player through their actions.
    """
    id: int
    goal: Goal
    penalty: int

    def __init__(self, player_id: int, goal: Goal) -> None:
        """Initialize this Player.
        """
        self.goal = goal
        self.id = player_id
        self.penalty = 0

    def get_selected_block(self, board: Block) -> Block | None:
        """Return the block that is currently selected by the player.

        If no block is selected by the player, return None.
        """
        raise NotImplementedError

    def process_event(self, event: pygame.event.Event) -> None:
        """Update this player based on the pygame event.
        """
        raise NotImplementedError

    def generate_move(self, board: Block) -> \
            tuple[Action, Block] | None:
        """Return a potential move to make on the <board>.

        The move is a tuple consisting of an action and
        the block the action will be applied to.

        Return None if no move can be made, yet.
        """
        raise NotImplementedError


class HumanPlayer(Player):
    """A human player.

    Instance Attributes:
    - _level: The level of the Block that the user selected most recently.
    - _desired_action: The most recent action that the user is attempting to do.

    Representation Invariants:
    - self._level >= 0
    """
    _level: int
    _desired_action: Action | None

    def __init__(self, player_id: int, goal: Goal) -> None:
        """Initialize this HumanPlayer with the given <renderer>, <player_id>
        and <goal>.
        """
        Player.__init__(self, player_id, goal)

        # This HumanPlayer has not yet selected a block, so set _level to 0
        # and _selected_block to None.
        self._level = 0
        self._desired_action = None

    def get_selected_block(self, board: Block) -> Block | None:
        """Return the block that is currently selected by the player based on
        the position of the mouse on the screen and the player's desired level.

        If no block is selected by the player, return None.
        """
        mouse_pos = pygame.mouse.get_pos()
        block = _get_block(board, mouse_pos, self._level)

        return block

    def process_event(self, event: pygame.event.Event) -> None:
        """Respond to the relevant keyboard events made by the player based on
        the mapping in KEY_ACTION, as well as the W and S keys for changing
        the level.
        """
        if event.type == pygame.KEYUP:
            if event.key in KEY_ACTION:
                self._desired_action = KEY_ACTION[event.key]
            elif event.key == pygame.K_w:
                self._level -= 1
                self._desired_action = None
            elif event.key == pygame.K_s:
                self._level += 1
                self._desired_action = None

    def generate_move(self, board: Block) -> \
            tuple[Action, Block] | None:
        """Return the move that the player would like to perform. The move may
        not be valid.

        Return None if the player is not currently selecting a block.

        This player's desired action gets reset after this method is called.
        """
        block = self.get_selected_block(board)

        if block is None or self._desired_action is None:
            self._correct_level(board)
            self._desired_action = None
            return None
        else:
            move = self._desired_action, block

            self._desired_action = None
            return move

    def _correct_level(self, board: Block) -> None:
        """Correct the level of the block that the player is currently
        selecting, if necessary.
        """
        self._level = max(0, min(self._level, board.max_depth))


class ComputerPlayer(Player):
    """A computer player. This class is still abstract,
    as how it generates moves is still to be defined
    in a subclass.

    Instance Attributes:
    - _proceed: True when the player should make a move, False when the
                player should wait.
    """
    _proceed: bool

    def __init__(self, player_id: int, goal: Goal) -> None:
        Player.__init__(self, player_id, goal)

        self._proceed = False

    def get_selected_block(self, board: Block) -> Block | None:
        return None

    def process_event(self, event: pygame.event.Event) -> None:
        if (event.type == pygame.MOUSEBUTTONDOWN
                and event.button == pygame.BUTTON_LEFT):
            self._proceed = True

    # Note: this is included just to make pyTA happy; as it thinks
    #       we forgot to implement this abstract method otherwise :)
    def generate_move(self, board: Block) -> \
            tuple[Action, Block] | None:
        raise NotImplementedError


class RandomPlayer(ComputerPlayer):
    """A computer player who chooses completely random moves."""

    def generate_move(self, board: Block) -> \
            tuple[Action, Block] | None:
        """Return a valid, randomly generated move only during the player's
        turn.  Return None if the player should not make a move yet.

        A valid move is a move other than PASS that can be successfully
        performed on the <board>.

        This function does not mutate <board>.

        """
        if not self._proceed:
            return None
        else:
            # randomly pick a move you want to try
            # randomly pick a board
            # check if it is a valid move
            # if not select other move
            board_copy = board.create_copy()
            random_block = None

            # get valid board
            while random_block is None:
                x = random.randint(0, board_copy.size)
                y = random.randint(0, board_copy.size)
                b_level = random.randint(0, board.max_depth)
                random_block = _get_block(board_copy, (x, y), b_level)

            valid_moves_lst = [ROTATE_CLOCKWISE, ROTATE_COUNTER_CLOCKWISE,
                               SWAP_HORIZONTAL, SWAP_VERTICAL, SMASH,
                               COMBINE, PAINT]

            # valid_moves_lst = [PAINT]
            random.shuffle(valid_moves_lst)
            random_move = random.choice(valid_moves_lst)

            # if move is not valid, select another move
            while not _is_valid_move(self, random_block, random_move):
                random_move = random.choice(valid_moves_lst)

            # know random_move is valid / True
            self._proceed = False
            # get block selected
            block_selected = _get_block(board, random_block.position,
                                        random_block.level)
            return random_move, block_selected


class SmartPlayer(ComputerPlayer):
    """A computer player who chooses moves by assessing a series of random
    moves and choosing the one that yields the best score.

    Private Instance Attributes:
    - _num_test: The number of moves this SmartPlayer will test out before
                 choosing a move.
    """
    _num_test: int

    def __init__(self, player_id: int, goal: Goal, difficulty: int) -> None:
        """Initialize this SmartPlayer with a <player_id> and <goal>.

        Use <difficulty> to determine and record how many moves this SmartPlayer
        will assess before choosing a move. The higher the value for
        <difficulty>, the more moves this SmartPlayer will assess, and hence the
        more difficult an opponent this SmartPlayer will be.

        Preconditions:
        - difficulty >= 0
        """
        ComputerPlayer.__init__(self, player_id, goal)
        self._num_test = difficulty

    def generate_move(self, board: Block) -> \
            tuple[Action, Block] | None:
        """Return a valid move only during the player's turn by assessing
        multiple valid moves and choosing the move that results in the highest
        score for this player's goal. This score should also account for the
        penalty of the move. Return None if the player should not make a move.

        A valid move is a move other than PASS that can be successfully
        performed on the <board>. If no move can be found that is better than
        the current score, this player will pass.

        This method does not mutate <board>.
        """
        if not self._proceed:
            return None
        else:
            # current_score
            original_score = self.goal.score(board)

            board_copy = board.create_copy()
            random_block = None

            # get valid board
            while random_block is None:
                x = random.randint(0, board_copy.size)
                y = random.randint(0, board_copy.size)
                b_level = random.randint(0, board.max_depth)
                random_block = _get_block(board_copy, (x, y), b_level)

            valid_moves_lst = [ROTATE_CLOCKWISE, ROTATE_COUNTER_CLOCKWISE,
                               SWAP_HORIZONTAL, SWAP_VERTICAL, SMASH,
                               COMBINE, PAINT]
            random.shuffle(valid_moves_lst)

            current_score = original_score
            best_move = valid_moves_lst[0]
            # generate n valid moves
            # generate_valid_moves = []
            for _ in range(self._num_test):
                random_move = random.choice(valid_moves_lst)

                while not _is_valid_move(self, random_block, random_move):
                    random_move = random.choice(valid_moves_lst)

                # you have a random move
                # get the score based on move
                # if score > current_score
                #   set current score = score and store the best_move
                if random_move.short_name in {'paint', 'combine'}:
                    # if random_move.short_name == 'paint' \
                    #         or random_move.short_name == 'combine':
                    score = self.goal.score(random_block) - 1
                elif random_move.short_name == 'smash':
                    score = self.goal.score(random_block) - 2
                else:
                    score = self.goal.score(random_block)

                if score > current_score:
                    current_score = score
                    best_move = random_move
                # generate_valid_moves.append(random_move)
                #
                # valid_moves_lst.remove(random_move)
            self._proceed = False
            board_selected = _get_block(board, random_block.position,
                                        random_block.level)
            if original_score == current_score or self._num_test == 0:
                return PASS, board_selected
            else:
                return best_move, board


if __name__ == '__main__':
    import python_ta

    python_ta.check_all(config={
        'allowed-io': ['process_event'],
        'allowed-import-modules': [
            'doctest', 'python_ta', 'random', 'typing', 'actions', 'block',
            'goal', 'pygame', '__future__'
        ],
        'max-attributes': 10,
        'generated-members': 'pygame.*'
    })
