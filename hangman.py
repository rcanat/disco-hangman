import PIL.Image
import PIL.ImageDraw
from drafter import *
from bakery import assert_equal
from dataclasses import dataclass
from string import ascii_uppercase
import random
import PIL


# general constants
MAX_GUESSES = 6
WORD_LIST = ["STINKY", "CARPET", "PYTHON", "HAMBURGER", "BUCKET"]

# graphics constants
IMAGE_WIDTH = 300
IMAGE_HEIGHT = 300
IMAGE_SIZE = (IMAGE_WIDTH, IMAGE_HEIGHT)

GALLOWS_BASE_XCENTER = IMAGE_WIDTH - 67
GALLOWS_BASE_YPOS = 200
GALLOWS_BASE_LENGTH_LEFT = 33
GALLOWS_BASE_LENGTH_RIGHT = 33
GALLOWS_POST_LENGTH = 167
GALLOWS_CROSSBEAM_LENGTH = 100
GALLOWS_ROPE_LENGTH = 33
GALLOWS_SUPPORT_SIZE = 33

HANGMAN_XCENTER = GALLOWS_BASE_XCENTER - GALLOWS_CROSSBEAM_LENGTH
HANGMAN_YTOP = GALLOWS_BASE_YPOS - GALLOWS_POST_LENGTH + GALLOWS_ROPE_LENGTH


@dataclass
class GameResult:
    name: str
    word: str
    won: bool
    guesses: int


@dataclass
class State:
    name: str
    word: str
    guessed_letters: list[str]
    wrong_guesses: int
    previous_games: list[GameResult]


@route
def index(state: State) -> Page:
    """Main menu page with a button to start a new game and a button to view
    results of previous games."""
    return Page(state, [
        "Welcome to Hangman!",
        Image("title_screen.png"),
        Button("New Game", new_game)
    ])
    
    
@route
def new_game(state: State) -> Page:
    """Page that asks the user for their name and lets them begin the game."""
    return Page(state, [
        "Please enter your name:",
        TextBox("name", state.name),
        Button("Play!", initialize_game)
    ])


@route
def initialize_game(state: State, name: str) -> Page:
    """Updates the player's name, generates the mystery word, and goes to the
    main game page."""
    state.name = name
    state.word = random.choice(WORD_LIST)
    return game_page(state)


@route
def game_page(state: State) -> Page:
    """The main game page where the user can guess letters"""
    
    # create a string that shows the positions of guessed characters
    word_display = ""
    for letter in state.word:
        
        # show the letter if it has been guessed
        if letter in state.guessed_letters:
            word_display += letter
            
        # show '_' if the letter has not been guessed
        else:
            word_display += '_'
    
    # add a space between each letter in the display
    word_display = ' '.join(word_display)
    
    # create a string that shows the letters that were already guessed
    guessed_display  = "Guessed Letters: "
    guessed_display += ", ".join(state.guessed_letters)
    
    # page setup
    return Page(state, [
        "Guess a Letter!",
        Image(f"hangman{str(state.wrong_guesses)}.png"),
        word_display,
        TextBox("guess"),
        Button("Go", check_guess),
        guessed_display
    ])
    

@route
def check_guess(state: State, guess: str) -> Page:
    """Adjust the state based on the user's guess and go back to the game. If
    the user has no guesses left, send them to the lose screen instead. If the
    user has guessed the word, send them to the win screen instead."""
    
    # case insensitive
    guess = guess.upper()
    if is_valid_guess(state.guessed_letters, guess):
        
        # add the guess to the list of guessed letters
        state.guessed_letters.append(guess)
        state.guessed_letters.sort()
        
        # check if the guess is wrong
        if guess not in state.word:
            state.wrong_guesses += 1
    
    # return the appropriate page based on the state
    if has_won(state):
        return win_screen(state)
    
    if has_lost(state):
        return lose_screen(state)
    
    return game_page(state)


@route
def win_screen(state: State) -> Page:
    """The page to display when the user wins"""
    return Page(state, [
        f"You won! The word was {state.word}",
        Image("win.png"),
        Button("Main Menu", reset)
    ])


@route
def lose_screen(state: State) -> Page:
    """The page to display when the user loses"""
    return Page(state, [
        f"You lost! The word was {state.word}",
        Image("lose.png"),
        Button("Main Menu", reset)
    ])


@route
def reset(state: State) -> Page:
    """Resets the word, guessed_letters, and wrong_guesses attributes of the
    current state and redirects to index."""
    state.word = ""
    state.guessed_letters = []
    state.wrong_guesses = 0
    return index(state)


def is_valid_guess(guessed_letters: list[str], guess: str) -> bool:
    """Returns whether or not the guess is valid, meaning it is a single
    English letter that was not guessed already. Assumes the guess was already
    converted to uppercase.
    
    Args:
        guessed_letters (list[str]): List of letters that have been guessed
        guess (str): The guess to check
    Returns:
        bool: Whether or not the guess is valid
    """    
    # generate a list of all letters that were not guessed
    valid_letters = [l for l in ascii_uppercase if l not in guessed_letters]
    
    # check if the guess is valid
    return guess in valid_letters


def has_won(state: State) -> bool:
    """Based on the given State, determines if the user has won (guessed all of
    the letters in the word).

    Args:
        state (State): The current State of the site
    Returns:
        bool: Whether or not the user has won
    """
    # check if any letters have not been guessed yet
    for letter in state.word:
        if letter not in state.guessed_letters:
            return False
    return True


def has_lost(state: State) -> bool:
    """Based on the given State, determines if the user has lost (no more
    guesses remaining).

    Args:
        state (State): The current State of the site
    Returns:
        bool: Whether or not the user has lost
    """
    return state.wrong_guesses == MAX_GUESSES


def generate_hangman_animation(state: State) -> None:
    """Based on the given State, generates an animation to display the current
    hangman. This animation is saved as hangman.gif.
    
    Args:
        state (State): The current State of the site
    """
    frame = generate_hangman_animation_frame(state)
    frame.save("hangman.png")


def generate_hangman_animation_frame(state: State) -> PIL.Image:
    """Based on the given State, generates a single frame to display the
    current hangman.

    Args:
        state (State): The current State of the site
    Returns:
        PIL.Image: The generated animation frame
    """
    # generate a blank white image
    frame = PIL.Image.new("RGB", IMAGE_SIZE, "white")
    draw = PIL.ImageDraw.Draw(frame)
    
    # draw the gallows
    draw.line((

        # base
        (GALLOWS_BASE_XCENTER - GALLOWS_BASE_LENGTH_LEFT, GALLOWS_BASE_YPOS),
        (GALLOWS_BASE_XCENTER + GALLOWS_BASE_LENGTH_RIGHT, GALLOWS_BASE_YPOS),

        # post
        (GALLOWS_BASE_XCENTER, GALLOWS_BASE_YPOS),
        (GALLOWS_BASE_XCENTER, GALLOWS_BASE_YPOS - GALLOWS_POST_LENGTH),

        # support
        (GALLOWS_BASE_XCENTER, GALLOWS_BASE_YPOS - GALLOWS_POST_LENGTH + GALLOWS_SUPPORT_SIZE),
        (GALLOWS_BASE_XCENTER - GALLOWS_SUPPORT_SIZE, GALLOWS_BASE_YPOS - GALLOWS_POST_LENGTH),
        (GALLOWS_BASE_XCENTER, GALLOWS_BASE_YPOS - GALLOWS_POST_LENGTH),

        # crossbar
        (HANGMAN_XCENTER, GALLOWS_BASE_YPOS - GALLOWS_POST_LENGTH),

        # rope
        (HANGMAN_XCENTER, HANGMAN_YTOP)

    ), "black", 5)

    return frame


# unit tests for is_valid_guess
assert_equal(is_valid_guess(["C"], "A"), True)
assert_equal(is_valid_guess(["H", "B"], "B"), False)
assert_equal(is_valid_guess(["F", "X"], "P"), True)
assert_equal(is_valid_guess([], "2"), False)
assert_equal(is_valid_guess(["C", "D", "E"], "AB"), False)

# unit tests for has_won
assert_equal(has_won(State("", "LIST", ["C", "D", "E"], 0, [])), False)
assert_equal(has_won(State("", "BOOL", ["B", "L", "O"], 0, [])), True)
assert_equal(has_won(State("", "PYTHON", [], 0, [])), False)

# unit tests for has_lost
assert_equal(has_lost(State("", "BAKERY", [], 0, [])), False)
assert_equal(has_lost(State("", "ABSTRACT", [], 6, [])), True)
assert_equal(has_lost(State("", "DRAFTER", [], 5, [])), False)


# start the site server
# hide_debug_information()

new_state = State(
    "", # name
    "", # word
    [], # guessed_letters
    0,  # wrong_guesses
    []  # previous_games
)

generate_hangman_animation(new_state)
#start_server(new_state)
