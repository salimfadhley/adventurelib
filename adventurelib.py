import re
import inspect
import readline
from functools import partial
from itertools import zip_longest

commands = []

__all__ = (
    'when',
    'when_move',
    'start',
    'Room'
)


class InvalidCommand(Exception):
    """A command is not defined correctly."""


class Placeholder:
    """Match a word in a command string."""
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return self.name.upper()


class Room:
    """A generic room object that can be used by game code."""

    _directions = {}

    @staticmethod
    def add_direction(forward, reverse):
        """Add a direction."""
        for dir in (forward, reverse):
            if not dir.islower():
                raise InvalidCommand(
                    'Invalid direction %r: directions must be all lowercase.'
                )
            if dir in Room._directions:
                raise KeyError('%r is already a direction!' % dir)
        Room._directions[forward] = reverse
        Room._directions[reverse] = forward

    def __init__(self, description):
        self.description = description.strip()

    def __str__(self):
        return self.description

    def exit(self, direction):
        """Get the exit of a room in a given direction.

        Return None if the room has no exit in a direction.

        """
        if direction not in self._directions:
            raise KeyError('%r is not a direction' % direction)
        return getattr(self, direction, None)

    def exits(self):
        """Get a list of directions to exit the room."""
        return sorted(d for d in self._directions if hasattr(self, d))

    def __setattr__(self, name, value):
        if isinstance(value, Room):
            if name not in self._directions:
                raise InvalidDirection(
                    '%r is not a direction you have declared.\n\n' +
                    'Try calling Room.add_direction(%r, <opposite>) ' % name +
                    ' where <opposite> is the return direction.'
                )
            reverse = self._directions[name]
            object.__setattr__(self, name, value)
            object.__setattr__(value, reverse, self)
        else:
            object.__setattr__(self, name, value)

Room.add_direction('north', 'south')
Room.add_direction('east', 'west')


def _register(command, func):
    """Register func as a handler for the given command."""
    words = command.split()
    match = []
    argnames = []
    for w in words:
        if not w.isalpha():
            raise InvalidCommand(
                'Invalid command %r' % command +
                'Commands may consist of letters only.'
            )
        if w.isupper():
            arg = w.lower()
            argnames.append(arg)
            match.append(Placeholder(arg))
        elif w.islower():
            match.append(w)
        else:
            raise InvalidCommand(
                'Invalid command %r' % command +
                '\n\nWords in commands must either be in lowercase or ' +
                'capitals, not a mix.'
            )

    sig = inspect.signature(func)
    func_argnames = list(sig.parameters)
    if func_argnames != argnames:
        raise InvalidCommand(
            'The function %s%s has the wrong signature for %r' % (
                func.__name__, sig, command
            ) + '\n\n' + 'The function arguments should be named (%s)' % (
                ', '.join(argnames)
            )
        )

    commands.append((tuple(match), func))


def prompt():
    """Called to get the prompt text."""
    return '> '


def no_command_matches(command):
    """Called when a command is not understood."""
    print("I don't understand '%s'." % command)


def when(command):
    """Decorator for command functions."""
    def dec(func):
        _register(command, func)
        return func
    return dec


def when_move(func=None):
    """Register a function to be called for move operations.

    This will register the function for all currently defined directions.

    The function should be of the form::

        def move(direction):

    and will be called with the direction that should be moved.

    """
    def dec(func):
        for d in Room._directions:
            commands.append(((d,), partial(func, d)))
        return func
    if func:
        return dec(func)
    else:
        return dec


def help():
    """Print a list of the commands you can give."""
    print('Here is a list of the commands you can give:')
    for match, func in sorted(commands):
        print(' '.join(str(t) for t in match))


def start(help=True):
    """Run the game."""
    if help:
        # Ugly, but we want to keep the arguments consistent
        help = globals()['help']
        commands.insert(0, (('help',), help))
        commands.insert(0, (('?',), help))
    while True:
        cmd = input(prompt())
        ws = tuple(cmd.lower().split())
        for match, func in commands:
            args = {}
            for cword, word in zip_longest(match, ws):
                if word is None:
                    break
                if isinstance(cword, Placeholder):
                    args[cword.name] = word
                elif cword != word:
                    break
            else:
                func(**args)
                break
        else:
            no_command_matches(cmd)
        print()


