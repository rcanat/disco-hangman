import PIL.Image
import PIL.ImageDraw
from drafter import *
from bakery import assert_equal
from dataclasses import dataclass
from string import ascii_uppercase
import random
import io
import base64
import PIL


# general constants
MAX_GUESSES = 6
WORD_LIST = ["STINKY", "CARPET", "PYTHON", "HAMBURGER", "BUCKET"]

# graphics constants
IMAGE_WIDTH = 500
IMAGE_HEIGHT = 400
IMAGE_SIZE = (IMAGE_WIDTH, IMAGE_HEIGHT)

GALLOWS_LINE_THICKNESS = 5
GALLOWS_BASE_XCENTER = IMAGE_WIDTH - 100
GALLOWS_BASE_YPOS = IMAGE_HEIGHT - 100
GALLOWS_BASE_LENGTH_LEFT = 67
GALLOWS_BASE_LENGTH_RIGHT = 67
GALLOWS_POST_LENGTH = 267
GALLOWS_CROSSBEAM_LENGTH = 133
GALLOWS_ROPE_LENGTH = 33
GALLOWS_SUPPORT_SIZE = 33

HANGMAN_LINE_THICKNESS = 5
HANGMAN_XCENTER = GALLOWS_BASE_XCENTER - GALLOWS_CROSSBEAM_LENGTH
HANGMAN_YTOP = GALLOWS_BASE_YPOS - GALLOWS_POST_LENGTH + GALLOWS_ROPE_LENGTH
HANGMAN_HEAD_RADIUS = 26
HANGMAN_MOUTH_YPOS = HANGMAN_YTOP + HANGMAN_HEAD_RADIUS + 8
HANGMAN_MOUTH_RADIUS = 8
HANGMAN_TORSO_TOP = HANGMAN_YTOP + 2 * HANGMAN_HEAD_RADIUS
HANGMAN_TORSO_LENGTH = 100
HANGMAN_ARM_TOP = HANGMAN_TORSO_TOP + 16
HANGMAN_ARM_LENGTH = 33
HANGMAN_LEG_TOP = HANGMAN_TORSO_TOP + HANGMAN_TORSO_LENGTH
HANGMAN_LEG_LENGTH = 33

SUNGLASSES_YPOS = HANGMAN_YTOP + HANGMAN_HEAD_RADIUS - 5
SUNGLASSES_BRIDGE_RADIUS = 3
SUNGLASSES_LENS_WIDTH = 16
SUNGLASSES_LENS_HEIGHT = 16
SUNGLASSES_FRAME_RADIUS = SUNGLASSES_BRIDGE_RADIUS + SUNGLASSES_LENS_WIDTH + 3

WORD_LEFT_PAD = 33
LETTER_BLANK_THICKNESS = 4
LETTER_WIDTH = 33
LETTER_SPACING = 17
LETTER_BLANK_YPOS = IMAGE_HEIGHT - 17
LETTER_YPOS = LETTER_BLANK_YPOS - 8


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
    animation = generate_animation_html(generate_hangman_animation_frame(state))
    return Page(state, [
        "Welcome to Hangman!",
        animation,
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


def generate_hangman_animation(state: State) -> PIL.Image:
    """Based on the given State, generates a full animation to display the
    current hangman.
    
    Args:
        state (State): The current State of the site
    Returns:
        PIL.Image: The generated full animation
    """
    pass


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

    ), fill="black", width=GALLOWS_LINE_THICKNESS, joint="curve")

    # generate a list with the colors to draw each body part
    # this is indexed by the order the body parts change color
    body_part_colors  = ["tomato"] * state.wrong_guesses
    body_part_colors += ["lightgray"]  * (MAX_GUESSES - state.wrong_guesses)

    # draw the hangman - head and torso are drawn last so they are on top

    # left arm
    draw.line((
        (HANGMAN_XCENTER, HANGMAN_ARM_TOP),
        (HANGMAN_XCENTER - HANGMAN_ARM_LENGTH, HANGMAN_ARM_TOP + HANGMAN_ARM_LENGTH)
    ), fill=body_part_colors[2], width=HANGMAN_LINE_THICKNESS+1)

    # right arm
    draw.line((
        (HANGMAN_XCENTER, HANGMAN_ARM_TOP),
        (HANGMAN_XCENTER + HANGMAN_ARM_LENGTH, HANGMAN_ARM_TOP + HANGMAN_ARM_LENGTH)
    ), fill=body_part_colors[3], width=HANGMAN_LINE_THICKNESS+1)

    # left leg
    draw.line((
        (HANGMAN_XCENTER, HANGMAN_LEG_TOP),
        (HANGMAN_XCENTER - HANGMAN_LEG_LENGTH, HANGMAN_LEG_TOP + HANGMAN_LEG_LENGTH)
    ), fill=body_part_colors[4], width=HANGMAN_LINE_THICKNESS+1)

    # right leg
    draw.line((
        (HANGMAN_XCENTER, HANGMAN_LEG_TOP),
        (HANGMAN_XCENTER + HANGMAN_LEG_LENGTH, HANGMAN_LEG_TOP + HANGMAN_LEG_LENGTH)
    ), fill=body_part_colors[4], width=HANGMAN_LINE_THICKNESS+1)

    # torso
    draw.line((
        (HANGMAN_XCENTER, HANGMAN_TORSO_TOP),
        (HANGMAN_XCENTER, HANGMAN_TORSO_TOP + HANGMAN_TORSO_LENGTH)
    ), fill=body_part_colors[1], width=HANGMAN_LINE_THICKNESS)

    # head
    draw.circle(
        xy=(HANGMAN_XCENTER, HANGMAN_YTOP + HANGMAN_HEAD_RADIUS),
        radius=HANGMAN_HEAD_RADIUS,
        outline=body_part_colors[0],
        width=HANGMAN_LINE_THICKNESS
    )

    # mouth
    draw.line((
        (HANGMAN_XCENTER - HANGMAN_MOUTH_RADIUS, HANGMAN_MOUTH_YPOS),
        (HANGMAN_XCENTER + HANGMAN_MOUTH_RADIUS, HANGMAN_MOUTH_YPOS)
    ), fill=body_part_colors[0], width=2)
    
    # give him sunglasses because he's chill like that
    # bridge
    draw.line((
        (HANGMAN_XCENTER - SUNGLASSES_FRAME_RADIUS, SUNGLASSES_YPOS),
        (HANGMAN_XCENTER + SUNGLASSES_FRAME_RADIUS, SUNGLASSES_YPOS)
    ), fill=body_part_colors[0], width=2)

    # left lens
    draw.chord((
        (HANGMAN_XCENTER - SUNGLASSES_BRIDGE_RADIUS - SUNGLASSES_LENS_WIDTH, SUNGLASSES_YPOS - SUNGLASSES_LENS_HEIGHT/2),
        (HANGMAN_XCENTER - SUNGLASSES_BRIDGE_RADIUS, SUNGLASSES_YPOS + SUNGLASSES_LENS_HEIGHT/2)
    ), start=0, end=180, fill=body_part_colors[0])

    # right lens
    draw.chord((
        (HANGMAN_XCENTER + SUNGLASSES_BRIDGE_RADIUS, SUNGLASSES_YPOS - SUNGLASSES_LENS_HEIGHT/2),
        (HANGMAN_XCENTER + SUNGLASSES_BRIDGE_RADIUS + SUNGLASSES_LENS_WIDTH, SUNGLASSES_YPOS + SUNGLASSES_LENS_HEIGHT/2)
    ), start=0, end=180, fill=body_part_colors[0])

    # draw all of the letters and blanks
    for i, letter in enumerate(state.word):

        # the leftmost x position of this letter's blank
        letter_start_pos = WORD_LEFT_PAD + i * (LETTER_WIDTH + LETTER_SPACING)

        # draw the blank
        draw.line((
            (letter_start_pos, LETTER_BLANK_YPOS),
            (letter_start_pos + LETTER_WIDTH, LETTER_BLANK_YPOS)
        ), fill="black", width=LETTER_BLANK_THICKNESS)

        # draw the letter, if it was guessed
        if letter in state.guessed_letters:
            draw.text(
                xy=(letter_start_pos + 0.5 * LETTER_WIDTH, LETTER_BLANK_YPOS),
                text=letter,
                fill="tomato",
                anchor="md",
                stroke_width=1,
                font_size=LETTER_WIDTH
            )

    return frame


def generate_animation_uri(animation: PIL.Image) -> str:
    """Given a hangman animation, generates a URI for accessing it.
    
    Args:
        animation (PIL.Image): The hangman animation
    Returns:
        str: The URI for the animation
    """
    # create a new bytes buffer and save the animation to it
    buffer = io.BytesIO()
    animation.save(buffer, "PNG")

    # encode the byte data to base64 for use in the URI
    animation_data = buffer.getvalue()
    base64_data = base64.b64encode(animation_data).decode("utf-8")

    # return the URI
    return "data:image/png;base64," + base64_data


def generate_animation_html(animation: PIL.Image) -> str:
    """Given a hangman animation, generates an html tag to embed it to a Page.
    
    Args:
        animation (PIL.Image): The hangman animation
    Returns:
        str: The html tag for the animation
    """
    return f'<img src="{generate_animation_uri(animation)}"/>'


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

default_state = State(
    "", # name
    "QUESTION", # word
    ['Q', 'I', 'T', 'U'], # guessed_letters
    3,  # wrong_guesses
    []  # previous_games
)

frame = generate_hangman_animation_frame(default_state)
frame.save("hangman.png")

# start_server(default_state)
