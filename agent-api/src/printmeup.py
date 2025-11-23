from icecream import ic
from typing import TypeVar
import traceback
import sys
import time
import threading


ENDC = "0"
BOLD = "1"
ITALIC = "3"
UNDERLINE = "4"
BLINK = "5"
REVERSE = "7"
STRIKETHROUGH = "9"
DUNDERLINE = "21"
BG_BLACK = "40"
BG_RED = "41"
BG_GREEN = "42"
BG_YELLOW = "43"
BG_BLUE = "44"
BG_MAGENTA = "45"
BG_CYAN = "46"
BG_WHITE = "47"
HBLACK = "90"
HRED = "91"
HGREEN = "92"
HYELLOW = "93"
HBLUE = "94"
HMAGENTA = "95"
HCYAN = "96"
HWHITE = "97"

codes = [
    ENDC,
    BOLD,
    ITALIC,
    UNDERLINE,
    DUNDERLINE,
    BLINK,
    REVERSE,
    STRIKETHROUGH,
    BG_BLACK,
    BG_RED,
    BG_GREEN,
    BG_YELLOW,
    BG_BLUE,
    BG_MAGENTA,
    BG_CYAN,
    BG_WHITE,
    HBLACK,
    HRED,
    HGREEN,
    HYELLOW,
    HBLUE,
    HMAGENTA,
    HCYAN,
    HWHITE,
]

@staticmethod
def ec(codes: list[str]) -> str:
    """
    Returns a string with ANSI escape codes for the given color codes. empty list returns ENDC.

    Arguments:
        codes: A list of strings representing the color codes.
            can include color names like "HRED", "91", colors.HRED

    Examples:
        >>> cc([HRED, "1", "BG_YELLOW"])
        "\\033[91;1;43m"
    """
    l = len(codes)
    for index, code in enumerate(codes):
        if code not in codes:
            try:
                code = getattr(sys.modules[__name__], code, None)
                if code in codes:
                    codes[index] = code
                    continue
            except AttributeError:
                pass
            raise ValueError(f"Invalid color code: {code}")

    if l == 1:
        return f"\033[{codes[0]}m"

    if l > 1:
        return f"\033[{';'.join(codes)}m"

    return f"\033[{ENDC}m"

RAINBOW_COLORS = [
    "\033[91m",  # * Red
    "\033[93m",  # * Yellow
    "\033[92m",  # * Green
    "\033[96m",  # * Cyan
    "\033[94m",  # * Blue
    "\033[95m",  # * Magenta
]

def p(message: str, codes: list[str]) -> str:
    """
    paint a message 🖌️🎨

    Arguments:
        message: The message to be painted.

        codes: A list of strings representing the color codes.
            can include color names like "HRED", "91", colors.HRED

    """
    return f"{ec(codes)}{message}{ec([ENDC])}"

def print_all_possible_combinations():
    c = 0
    for i in range(1, 8):
        for j in range(7, 16):
            for k in range(15, 24):
                color1 = codes[i]
                color2 = codes[j]
                color3 = codes[k]
                print(
                    f"\033[{color1};{color2};{color3}m Color {color1}, {color2}, and {color3}\033[0m"
                )
                c += 1
    print(f"Total combinations: {c}")
        
def try_all_colors():
    """Prints all possible color combinations."""
    print(ec(codes))
    print_all_possible_combinations()
        
def cull_long_string(obj: dict | list | str) -> dict | list | str:
    """
    Recursively culls long strings in a dictionary or list.
    If a string is longer than 1000 characters, it replaces it with a placeholder.
    """
    if isinstance(obj, str):
        if len(obj) > 1000:
            return p(f"< A LONG STRING OF {len(obj)} 🤯 >", [HYELLOW])
        return obj
    if isinstance(obj, list):
        return [cull_long_string(item) for item in obj]
    if isinstance(obj, dict):
        return {k: cull_long_string(v) for k, v in obj.items()}
    return obj

    
def deb(message: str, end: str = "\n") -> str:
    """Prints a debug message."""
    print(f"{p('[DEBUG🐛]:', [BG_BLUE])} {p(message, [HBLUE])}", end=end)
    return message

def err(
    e: Exception | None = None, m: str | None = None, a: str | None = None
) -> Exception:
    """Prints an error message."""
    if not m:
        if e is not None:
            m = e.__repr__()
        else:
            m = "An error occurred."
    else:
        m = f"{m}: {e.__repr__()}"
    
    if not a:
        try:
            frame = traceback.extract_stack()[-3]
            a = f"{frame.filename}:{frame.lineno}"
        except Exception:
            a = None
    
    if not a:
        a = ""
    else:
        a = f"@{a}"
    print(f"{p(f'[ERROR😱{a}]:', [BG_RED])} {p(m, [HRED])}")
            
    if e:
        return e
    else:
        return ValueError(m)

def inf(message: str, end: str = "\n") -> str:
    """Prints an informational message."""
    print(f"{p('[INFO🤓]:', [BG_CYAN])} {p(message, [HCYAN])}", end=end)
    return message

def war(message: str, end: str = "\n") -> str:
    """Prints a warning message."""
    print(f"{p('[WARNING😳]:', [BG_YELLOW])} {p(message, [HYELLOW])}", end=end)
    return message

def suc(message: str, end: str = "\n") -> str:
    """Prints a success message."""
    print(f"{p('[SUCCESS🥹 ]:', [BG_GREEN])} {p(message, [HGREEN])}", end=end)
    return message

def rep(message: str, replier: str | None, end: str = "\n"):
    """Prints a message with a replier prefix."""
    if replier is None:
        replier = "beep boop"
    print(f"{p(replier + '🗣 🔥>', [HBLUE])} {message}", end=end)


def inp(user: str | None = None) -> str:
    """
    Used to get input from the user.
    """
    if user is None:
        user = "goober"
        
    print(f"{p(user + '🎤>', [HBLUE])} ", end="")
    return input()


def rin(prompt: str, replier: str | None = None, end: str = "\n") -> str:
    """Used to get input from the user with a specific replier prefix."""
    rep(prompt, replier, end=end)
    return inp()

T = TypeVar("T")

def ins(obj: T, message: str | None = None) -> T:
    print(p('[INSPECT🧐]:', [BG_MAGENTA]), end=" ")
    if message:
        print(p(message, [HMAGENTA]))
    else:
        print("")
    ic.configureOutput(prefix=obj.__class__.__name__ + " ")
    return obj

def try_all_methods():
    err(m="This is an error message.")
    inf("This is an info message.")
    war("This is a warning message.")
    deb("This is a debug message.")
    suc("This is a success message.")
    ins({"key": "value"}, "This is an inspection message.")
    rep("This is a reply message.", "Alice")
    inp("Bob")
    rin("This is a reply input message.")
        
if __name__ == "__main__":
    try_all_colors()
    try_all_methods()