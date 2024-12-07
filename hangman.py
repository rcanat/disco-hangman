from drafter import *
from bakery import assert_equal
from string import ascii_uppercase
from dataclasses import dataclass
import random


# constants
MAX_GUESSES = 6


@dataclass
class GameResult:
    name: str
    word: str
    guesses: int
    won: bool


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
        Image("title_screen.png" , width=400, height=400),
        Button("New Game", new_game),
        Button("View Previous Games", previous_games)
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

    # update the player's name
    state.name = name

    # generate the mystery word
    with open("words.txt") as file:
        word_list = file.read().split()
    state.word = random.choice(word_list).upper()

    # go to the main game page
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
        Image(f"hangman{str(state.wrong_guesses)}.png", width=400, height=400),
        word_display,
        TextBox("guess"),
        Button("Go", check_guess),
        guessed_display,
        Button("Main Menu", reset)
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
    else:
        # Larry is mad
        return mad(state, guess)
    
    # return the appropriate page based on the state
    if has_won(state):
        return win_screen(state)
    
    if has_lost(state):
        return lose_screen(state)
    
    return game_page(state)


@route
def mad(state: State, guess: str) -> Page:
    """The page to display when the player tries to break the game by inputting
    invalid guesses. This sets the player at one guess remaining."""
    state.wrong_guesses = MAX_GUESSES - 1
    return Page(state, [
        Image("mad.png", width=400, height=400),
        "Larry over here is mad that you tried to break the game with your invalid guess.",
        f"Seriously? {guess}? We both know that's not a valid letter. Stop being stupid.",
        "Think about what you did and try again. You now have one guess left.",
        Button("I'm Sorry Larry", game_page)
    ])


@route
def win_screen(state: State) -> Page:
    """The page to display when the user wins. Also adds this game's result to
    state.previous_games."""

    # add the game to the list of previous games
    state.previous_games.append(GameResult(
        name=state.name,
        word=state.word,
        guesses=len(state.guessed_letters),
        won=True
    ))

    # return the new page
    return Page(state, [
        f"You won! The word was {state.word}",
        Image("win.png", width=400, height=400),
        Button("Main Menu", reset)
    ])


@route
def lose_screen(state: State) -> Page:
    """The page to display when the user loses. Also adds this game's result to
    state.previous_games."""

    # add the game to the list of previous games
    state.previous_games.append(GameResult(
        name=state.name,
        word=state.word,
        guesses=len(state.guessed_letters),
        won=False
    ))

    # return the new page
    return Page(state, [
        f"You lost! The word was {state.word}",
        Image("lose.png", width=400, height=400),
        Button("Main Menu", reset)
    ])


@route
def previous_games(state: State) -> Page:
    """The page where the user can view results of previous games"""

    # check if there are previous games and decide what to display
    if state.previous_games:
        display = Table(state.previous_games)
    else:
        display = "No previous games. Go play one!"
    
    # return the new page
    return Page(state, [
        Button("Main Menu", reset),
        display
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

# route unit tests (auto-generated by drafter)
assert_equal(
 check_guess(State(name='I Love Python', word='ALGORITHM', guessed_letters=['E', 'O', 'R', 'T'], wrong_guesses=1,
                   previous_games=[GameResult(name='Give Me 100% Pls', word='DOG', guesses=5, won=True)]), 'c'),
 Page(state=State(name='I Love Python',
                 word='ALGORITHM',
                 guessed_letters=['C', 'E', 'O', 'R', 'T'],
                 wrong_guesses=2,
                 previous_games=[GameResult(name='Give Me 100% Pls', word='DOG', guesses=5, won=True)]),
     content=['Guess a Letter!',
              Image(url='hangman2.png', width=400, height=400),
              '_ _ _ O R _ T _ _',
              TextBox(name='guess', kind='text', default_value=''),
              Button(text='Go', url='/check_guess'),
              'Guessed Letters: C, E, O, R, T',
              Button(text='Main Menu', url='/reset')]))

assert_equal(
 check_guess(State(name='I Love Python', word='ALGORITHM', guessed_letters=['E', 'O'], wrong_guesses=1,
                   previous_games=[GameResult(name='Give Me 100% Pls', word='DOG', guesses=5, won=True)]), 'r'),
 Page(state=State(name='I Love Python',
                 word='ALGORITHM',
                 guessed_letters=['E', 'O', 'R'],
                 wrong_guesses=1,
                 previous_games=[GameResult(name='Give Me 100% Pls', word='DOG', guesses=5, won=True)]),
     content=['Guess a Letter!',
              Image(url='hangman1.png', width=400, height=400),
              '_ _ _ O R _ _ _ _',
              TextBox(name='guess', kind='text', default_value=''),
              Button(text='Go', url='/check_guess'),
              'Guessed Letters: E, O, R',
              Button(text='Main Menu', url='/reset')]))

assert_equal(
 check_guess(State(name='I Love Python', word='ALGORITHM', guessed_letters=['C', 'E', 'O', 'R', 'S', 'T'],
                   wrong_guesses=3, previous_games=[GameResult(name='Give Me 100% Pls', word='DOG', guesses=5,
                                                               won=True)]), 'm'),
 Page(state=State(name='I Love Python',
                 word='ALGORITHM',
                 guessed_letters=['C', 'E', 'M', 'O', 'R', 'S', 'T'],
                 wrong_guesses=3,
                 previous_games=[GameResult(name='Give Me 100% Pls', word='DOG', guesses=5, won=True)]),
     content=['Guess a Letter!',
              Image(url='hangman3.png', width=400, height=400),
              '_ _ _ O R _ T _ M',
              TextBox(name='guess', kind='text', default_value=''),
              Button(text='Go', url='/check_guess'),
              'Guessed Letters: C, E, M, O, R, S, T',
              Button(text='Main Menu', url='/reset')]))

assert_equal(
 check_guess(State(name='Give Me 100% Pls', word='DOG', guessed_letters=['A', 'D', 'E', 'O'], wrong_guesses=5,
                   previous_games=[]), 'g'),
 Page(state=State(name='Give Me 100% Pls',
                 word='DOG',
                 guessed_letters=['A', 'D', 'E', 'G', 'O'],
                 wrong_guesses=5,
                 previous_games=[GameResult(name='Give Me 100% Pls', word='DOG', guesses=5, won=True)]),
     content=['You won! The word was DOG',
              Image(url='win.png', width=400, height=400),
              Button(text='Main Menu', url='/reset')]))

assert_equal(
 reset(State(name='Give Me 100% Pls', word='DOG', guessed_letters=['A', 'D', 'E', 'G', 'O'], wrong_guesses=5,
             previous_games=[GameResult(name='Give Me 100% Pls', word='DOG', guesses=5, won=True)])),
 Page(state=State(name='Give Me 100% Pls',
                 word='',
                 guessed_letters=[],
                 wrong_guesses=0,
                 previous_games=[GameResult(name='Give Me 100% Pls', word='DOG', guesses=5, won=True)]),
     content=['Welcome to Hangman!',
              Image(url='title_screen.png', width=400, height=400),
              Button(text='New Game', url='/new_game'),
              Button(text='View Previous Games', url='/previous_games')]))

assert_equal(
 check_guess(State(name='Give Me 100% Pls', word='DOG', guessed_letters=['A'], wrong_guesses=1, previous_games=[]),
             'e'),
 Page(state=State(name='Give Me 100% Pls', word='DOG', guessed_letters=['A', 'E'], wrong_guesses=2, previous_games=[]),
     content=['Guess a Letter!',
              Image(url='hangman2.png', width=400, height=400),
              '_ _ _',
              TextBox(name='guess', kind='text', default_value=''),
              Button(text='Go', url='/check_guess'),
              'Guessed Letters: A, E',
              Button(text='Main Menu', url='/reset')]))

assert_equal(
 game_page(State(name='I Love Python', word='ALGORITHM', guessed_letters=['C', 'E', 'M', 'N', 'O', 'P', 'R', 'S', 'T'],
                 wrong_guesses=5, previous_games=[GameResult(name='Give Me 100% Pls', word='DOG', guesses=5, 
                                                             won=True)])),
 Page(state=State(name='I Love Python',
                 word='ALGORITHM',
                 guessed_letters=['C', 'E', 'M', 'N', 'O', 'P', 'R', 'S', 'T'],
                 wrong_guesses=5,
                 previous_games=[GameResult(name='Give Me 100% Pls', word='DOG', guesses=5, won=True)]),
     content=['Guess a Letter!',
              Image(url='hangman5.png', width=400, height=400),
              '_ _ _ O R _ T _ M',
              TextBox(name='guess', kind='text', default_value=''),
              Button(text='Go', url='/check_guess'),
              'Guessed Letters: C, E, M, N, O, P, R, S, T',
              Button(text='Main Menu', url='/reset')]))

assert_equal(
 check_guess(State(name='I Love Python', word='ALGORITHM',
                   guessed_letters=['C', 'E', 'M', 'N', 'O', 'P', 'R', 'S', 'T'], wrong_guesses=5,
                   previous_games=[GameResult(name='Give Me 100% Pls', word='DOG', guesses=5, won=True)]), 'y'),
 Page(state=State(name='I Love Python',
                 word='ALGORITHM',
                 guessed_letters=['C', 'E', 'M', 'N', 'O', 'P', 'R', 'S', 'T', 'Y'],
                 wrong_guesses=6,
                 previous_games=[GameResult(name='Give Me 100% Pls', word='DOG', guesses=5, won=True),
                                 GameResult(name='I Love Python', word='ALGORITHM', guesses=10, won=False)]),
     content=['You lost! The word was ALGORITHM',
              Image(url='lose.png', width=400, height=400),
              Button(text='Main Menu', url='/reset')]))

assert_equal(
 index(State(name='', word='', guessed_letters=[], wrong_guesses=0, previous_games=[])),
 Page(state=State(name='', word='', guessed_letters=[], wrong_guesses=0, previous_games=[]),
     content=['Welcome to Hangman!',
              Image(url='title_screen.png', width=400, height=400),
              Button(text='New Game', url='/new_game'),
              Button(text='View Previous Games', url='/previous_games')]))

assert_equal(
 check_guess(State(name='I Love Python', word='ALGORITHM', guessed_letters=['C', 'E', 'M', 'N', 'O', 'R', 'S', 'T'],
                   wrong_guesses=4, previous_games=[GameResult(name='Give Me 100% Pls', word='DOG', guesses=5,
                                                               won=True)]), 'p'),
 Page(state=State(name='I Love Python',
                 word='ALGORITHM',
                 guessed_letters=['C', 'E', 'M', 'N', 'O', 'P', 'R', 'S', 'T'],
                 wrong_guesses=5,
                 previous_games=[GameResult(name='Give Me 100% Pls', word='DOG', guesses=5, won=True)]),
     content=['Guess a Letter!',
              Image(url='hangman5.png', width=400, height=400),
              '_ _ _ O R _ T _ M',
              TextBox(name='guess', kind='text', default_value=''),
              Button(text='Go', url='/check_guess'),
              'Guessed Letters: C, E, M, N, O, P, R, S, T',
              Button(text='Main Menu', url='/reset')]))

assert_equal(
 check_guess(State(name='Give Me 100% Pls', word='DOG', guessed_letters=['A', 'E'], wrong_guesses=5,
                   previous_games=[]), 'o'),
 Page(state=State(name='Give Me 100% Pls',
                 word='DOG',
                 guessed_letters=['A', 'E', 'O'],
                 wrong_guesses=5,
                 previous_games=[]),
     content=['Guess a Letter!',
              Image(url='hangman5.png', width=400, height=400),
              '_ O _',
              TextBox(name='guess', kind='text', default_value=''),
              Button(text='Go', url='/check_guess'),
              'Guessed Letters: A, E, O',
              Button(text='Main Menu', url='/reset')]))

assert_equal(
 check_guess(State(name='Give Me 100% Pls', word='DOG', guessed_letters=['A', 'E', 'O'], wrong_guesses=5,
                   previous_games=[]), 'd'),
 Page(state=State(name='Give Me 100% Pls',
                 word='DOG',
                 guessed_letters=['A', 'D', 'E', 'O'],
                 wrong_guesses=5,
                 previous_games=[]),
     content=['Guess a Letter!',
              Image(url='hangman5.png', width=400, height=400),
              'D O _',
              TextBox(name='guess', kind='text', default_value=''),
              Button(text='Go', url='/check_guess'),
              'Guessed Letters: A, D, E, O',
              Button(text='Main Menu', url='/reset')]))

assert_equal(
 check_guess(State(name='I Love Python', word='ALGORITHM', guessed_letters=['C', 'E', 'O', 'R', 'T'], wrong_guesses=2,
                   previous_games=[GameResult(name='Give Me 100% Pls', word='DOG', guesses=5, won=True)]), 's'),
 Page(state=State(name='I Love Python',
                 word='ALGORITHM',
                 guessed_letters=['C', 'E', 'O', 'R', 'S', 'T'],
                 wrong_guesses=3,
                 previous_games=[GameResult(name='Give Me 100% Pls', word='DOG', guesses=5, won=True)]),
     content=['Guess a Letter!',
              Image(url='hangman3.png', width=400, height=400),
              '_ _ _ O R _ T _ _',
              TextBox(name='guess', kind='text', default_value=''),
              Button(text='Go', url='/check_guess'),
              'Guessed Letters: C, E, O, R, S, T',
              Button(text='Main Menu', url='/reset')]))

assert_equal(
 previous_games(State(name='I Love Python', word='', guessed_letters=[], wrong_guesses=0, 
                      previous_games=[GameResult(name='Give Me 100% Pls', word='DOG', guesses=5, won=True),
                                      GameResult(name='I Love Python', word='ALGORITHM', guesses=10, won=False)])),
 Page(state=State(name='I Love Python',
                 word='',
                 guessed_letters=[],
                 wrong_guesses=0,
                 previous_games=[GameResult(name='Give Me 100% Pls', word='DOG', guesses=5, won=True),
                                 GameResult(name='I Love Python', word='ALGORITHM', guesses=10, won=False)]),
     content=[Button(text='Main Menu', url='/reset'),
              Table(rows=[['Give Me 100% Pls', 'DOG', '5', 'True'], ['I Love Python', 'ALGORITHM', '10', 'False']])]))

assert_equal(
 reset(State(name='I Love Python', word='ALGORITHM',
             guessed_letters=['C', 'E', 'M', 'N', 'O', 'P', 'R', 'S', 'T', 'Y'], wrong_guesses=6,
             previous_games=[GameResult(name='Give Me 100% Pls', word='DOG', guesses=5, won=True),
                             GameResult(name='I Love Python', word='ALGORITHM', guesses=10, won=False)])),
 Page(state=State(name='I Love Python',
                 word='',
                 guessed_letters=[],
                 wrong_guesses=0,
                 previous_games=[GameResult(name='Give Me 100% Pls', word='DOG', guesses=5, won=True),
                                 GameResult(name='I Love Python', word='ALGORITHM', guesses=10, won=False)]),
     content=['Welcome to Hangman!',
              Image(url='title_screen.png', width=400, height=400),
              Button(text='New Game', url='/new_game'),
              Button(text='View Previous Games', url='/previous_games')]))

assert_equal(
 check_guess(State(name='Give Me 100% Pls', word='DOG', guessed_letters=['A', 'E'], wrong_guesses=2,
                   previous_games=[]), 'a'),
 Page(state=State(name='Give Me 100% Pls', word='DOG', guessed_letters=['A', 'E'], wrong_guesses=5, previous_games=[]),
     content=[Image(url='mad.png', width=400, height=400),
              'Larry over here is mad that you tried to break the game with your invalid guess.',
              "Seriously? A? We both know that's not a valid letter. Stop being stupid.",
              'Think about what you did and try again. You now have one guess left.',
              Button(text="I'm Sorry Larry", url='/game_page')]))

assert_equal(
 check_guess(State(name='I Love Python', word='ALGORITHM', guessed_letters=['E', 'O', 'R'], wrong_guesses=1,
                   previous_games=[GameResult(name='Give Me 100% Pls', word='DOG', guesses=5, won=True)]), 't'),
 Page(state=State(name='I Love Python',
                 word='ALGORITHM',
                 guessed_letters=['E', 'O', 'R', 'T'],
                 wrong_guesses=1,
                 previous_games=[GameResult(name='Give Me 100% Pls', word='DOG', guesses=5, won=True)]),
     content=['Guess a Letter!',
              Image(url='hangman1.png', width=400, height=400),
              '_ _ _ O R _ T _ _',
              TextBox(name='guess', kind='text', default_value=''),
              Button(text='Go', url='/check_guess'),
              'Guessed Letters: E, O, R, T',
              Button(text='Main Menu', url='/reset')]))

assert_equal(
 check_guess(State(name='I Love Python', word='ALGORITHM', guessed_letters=['O'], wrong_guesses=0, 
                   previous_games=[GameResult(name='Give Me 100% Pls', word='DOG', guesses=5, won=True)]), 'e'),
 Page(state=State(name='I Love Python',
                 word='ALGORITHM',
                 guessed_letters=['E', 'O'],
                 wrong_guesses=1,
                 previous_games=[GameResult(name='Give Me 100% Pls', word='DOG', guesses=5, won=True)]),
     content=['Guess a Letter!',
              Image(url='hangman1.png', width=400, height=400),
              '_ _ _ O _ _ _ _ _',
              TextBox(name='guess', kind='text', default_value=''),
              Button(text='Go', url='/check_guess'),
              'Guessed Letters: E, O',
              Button(text='Main Menu', url='/reset')]))

assert_equal(
 check_guess(State(name='I Love Python', word='ALGORITHM', guessed_letters=['C', 'E', 'M', 'O', 'R', 'S', 'T'],
                   wrong_guesses=3, previous_games=[GameResult(name='Give Me 100% Pls', word='DOG', guesses=5,
                                                               won=True)]), 'n'),
 Page(state=State(name='I Love Python',
                 word='ALGORITHM',
                 guessed_letters=['C', 'E', 'M', 'N', 'O', 'R', 'S', 'T'],
                 wrong_guesses=4,
                 previous_games=[GameResult(name='Give Me 100% Pls', word='DOG', guesses=5, won=True)]),
     content=['Guess a Letter!',
              Image(url='hangman4.png', width=400, height=400),
              '_ _ _ O R _ T _ M',
              TextBox(name='guess', kind='text', default_value=''),
              Button(text='Go', url='/check_guess'),
              'Guessed Letters: C, E, M, N, O, R, S, T',
              Button(text='Main Menu', url='/reset')]))

assert_equal(
 new_game(State(name='Give Me 100% Pls', word='', guessed_letters=[], wrong_guesses=0,
                previous_games=[GameResult(name='Give Me 100% Pls', word='DOG', guesses=5, won=True)])),
 Page(state=State(name='Give Me 100% Pls',
                 word='',
                 guessed_letters=[],
                 wrong_guesses=0,
                 previous_games=[GameResult(name='Give Me 100% Pls', word='DOG', guesses=5, won=True)]),
     content=['Please enter your name:',
              TextBox(name='name', kind='text', default_value='Give Me 100% Pls'),
              Button(text='Play!', url='/initialize_game')]))

assert_equal(
 check_guess(State(name='I Love Python', word='ALGORITHM', guessed_letters=[], wrong_guesses=0,
                   previous_games=[GameResult(name='Give Me 100% Pls', word='DOG', guesses=5, won=True)]), 'o'),
 Page(state=State(name='I Love Python',
                 word='ALGORITHM',
                 guessed_letters=['O'],
                 wrong_guesses=0,
                 previous_games=[GameResult(name='Give Me 100% Pls', word='DOG', guesses=5, won=True)]),
     content=['Guess a Letter!',
              Image(url='hangman0.png', width=400, height=400),
              '_ _ _ O _ _ _ _ _',
              TextBox(name='guess', kind='text', default_value=''),
              Button(text='Go', url='/check_guess'),
              'Guessed Letters: O',
              Button(text='Main Menu', url='/reset')]))

assert_equal(
 new_game(State(name='', word='', guessed_letters=[], wrong_guesses=0, previous_games=[])),
 Page(state=State(name='', word='', guessed_letters=[], wrong_guesses=0, previous_games=[]),
     content=['Please enter your name:',
              TextBox(name='name', kind='text', default_value=''),
              Button(text='Play!', url='/initialize_game')]))

assert_equal(
 reset(State(name='I Love Python', word='', guessed_letters=[], wrong_guesses=0,
             previous_games=[GameResult(name='Give Me 100% Pls', word='DOG', guesses=5, won=True),
                             GameResult(name='I Love Python', word='ALGORITHM', guesses=10, won=False)])),
 Page(state=State(name='I Love Python',
                 word='',
                 guessed_letters=[],
                 wrong_guesses=0,
                 previous_games=[GameResult(name='Give Me 100% Pls', word='DOG', guesses=5, won=True),
                                 GameResult(name='I Love Python', word='ALGORITHM', guesses=10, won=False)]),
     content=['Welcome to Hangman!',
              Image(url='title_screen.png', width=400, height=400),
              Button(text='New Game', url='/new_game'),
              Button(text='View Previous Games', url='/previous_games')]))

assert_equal(
 check_guess(State(name='I Love Python', word='ALGORITHM',
                   guessed_letters=['C', 'E', 'M', 'N', 'O', 'P', 'R', 'S', 'T'], wrong_guesses=5,
                   previous_games=[GameResult(name='Give Me 100% Pls', word='DOG', guesses=5, won=True)]), 'e'),
 Page(state=State(name='I Love Python',
                 word='ALGORITHM',
                 guessed_letters=['C', 'E', 'M', 'N', 'O', 'P', 'R', 'S', 'T'],
                 wrong_guesses=5,
                 previous_games=[GameResult(name='Give Me 100% Pls', word='DOG', guesses=5, won=True)]),
     content=[Image(url='mad.png', width=400, height=400),
              'Larry over here is mad that you tried to break the game with your invalid guess.',
              "Seriously? E? We both know that's not a valid letter. Stop being stupid.",
              'Think about what you did and try again. You now have one guess left.',
              Button(text="I'm Sorry Larry", url='/game_page')]))

assert_equal(
 check_guess(State(name='Give Me 100% Pls', word='DOG', guessed_letters=[], wrong_guesses=0, previous_games=[]), 'a'),
 Page(state=State(name='Give Me 100% Pls', word='DOG', guessed_letters=['A'], wrong_guesses=1, previous_games=[]),
     content=['Guess a Letter!',
              Image(url='hangman1.png', width=400, height=400),
              '_ _ _',
              TextBox(name='guess', kind='text', default_value=''),
              Button(text='Go', url='/check_guess'),
              'Guessed Letters: A',
              Button(text='Main Menu', url='/reset')]))

assert_equal(
 game_page(State(name='Give Me 100% Pls', word='DOG', guessed_letters=['A', 'E'], wrong_guesses=5, previous_games=[])),
 Page(state=State(name='Give Me 100% Pls', word='DOG', guessed_letters=['A', 'E'], wrong_guesses=5, previous_games=[]),
     content=['Guess a Letter!',
              Image(url='hangman5.png', width=400, height=400),
              '_ _ _',
              TextBox(name='guess', kind='text', default_value=''),
              Button(text='Go', url='/check_guess'),
              'Guessed Letters: A, E',
              Button(text='Main Menu', url='/reset')]))


# start the site server
hide_debug_information()
set_website_title("Epic Hangman")
set_website_framed(False)

start_server(State(
    name="",
    word="",
    guessed_letters=[],
    wrong_guesses=0,
    previous_games=[]
))
