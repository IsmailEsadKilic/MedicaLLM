from icecream import ic
from typing import TypeVar
import traceback
import logging

class colors:
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
    def c(codes: list[str]) -> str:
        """
        Returns a string with ANSI escape codes for the given color codes. empty list returns ENDC.

        Arguments:
            codes: A list of strings representing the color codes.
                can include color names like "HRED", "91", colors.HRED

        Examples:
            >>> colors.c([colors.HRED, "1", "BG_YELLOW"])
            "\\033[91;1;43m"
        """
        l = len(codes)
        for index, code in enumerate(codes):
            if code not in colors.codes:
                try:
                    code = getattr(colors, code, None)
                    if code in colors.codes:
                        codes[index] = code
                        continue
                except AttributeError:
                    pass
                raise ValueError(f"Invalid color code: {code}")

        if l == 1:
            return f"\033[{codes[0]}m"

        if l > 1:
            return f"\033[{';'.join(codes)}m"

        return f"\033[{colors.ENDC}m"

    RAINBOW_COLORS = [
        "\033[91m",  # * Red
        "\033[93m",  # * Yellow
        "\033[92m",  # * Green
        "\033[96m",  # * Cyan
        "\033[94m",  # * Blue
        "\033[95m",  # * Magenta
    ]

    @staticmethod
    def p(message: str, codes: list[str]) -> str:
        """
        paint a message 🖌️🎨

        Arguments:
            message: The message to be painted.

            codes: A list of strings representing the color codes.
                can include color names like "HRED", "91", colors.HRED

        """
        return f"{colors.c(codes)}{message}{colors.c([colors.ENDC])}"

    @staticmethod
    def print_all_possible_combinations():
        c = 0
        for i in range(1, 8):
            for j in range(7, 16):
                for k in range(15, 24):
                    color1 = colors.codes[i]
                    color2 = colors.codes[j]
                    color3 = colors.codes[k]
                    print(
                        f"\033[{color1};{color2};{color3}m Color {color1}, {color2}, and {color3}\033[0m"
                    )
                    c += 1
        print(f"Total combinations: {c}")


def try_format(obj_str: str) -> str:
    """
    Formats a flat, nested Python class-like string (e.g., Response()) for readability.
    Similar to JSON pretty-printing.
    will not put a newline before or after the first and last characters.
    """
    obj_str = obj_str.strip()
    indent = 2
    out = []
    level = 0
    i = 0
    n = len(obj_str)
    in_str = False
    str_char = ""
    while i < n:
        c = obj_str[i]
        if in_str:
            out.append(c)
            if c == str_char:
                # * Check for escaped quote
                if i == 0 or obj_str[i - 1] != "\\":
                    in_str = False
            i += 1
            continue
        if c in ('"', "'"):
            in_str = True
            str_char = c
            out.append(c)
            i += 1
            continue
        if c == "(" or c == "[" or c == "{":
            out.append(c)
            level += 1
            out.append("\n" + " " * (level * indent))
            i += 1
        elif c == ")" or c == "]" or c == "}":
            level -= 1
            out.append("\n" + " " * (level * indent) + c)
            i += 1
        elif c == ",":
            out.append(",\n" + " " * (level * indent))
            i += 1
            # * Skip possible space after comma
            while i < n and obj_str[i] == " ":
                i += 1
        else:
            out.append(c)
            i += 1
    return "".join(out)


def cull_long_string(obj: dict | list | str) -> dict | list | str:
    """
    Recursively culls long strings in a dictionary or list.
    If a string is longer than 1000 characters, it replaces it with a placeholder.
    """
    return obj # FIXME
    if isinstance(obj, str):
        if len(obj) > 1000:
            return colors.p(f"< A LONG STRING OF {len(obj)} 🤯 >", [colors.HYELLOW])
        return obj
    if isinstance(obj, list):
        return [cull_long_string(item) for item in obj]
    if isinstance(obj, dict):
        return {k: cull_long_string(v) for k, v in obj.items()}
    return obj
    
def deb(message: str, end: str = "\n") -> str:
    """Prints a debug message."""
    s = f"{colors.p('[DEBUG🐛]:', [colors.BG_BLUE])} {colors.p(message, [colors.HBLUE])}"
    print(s, end=end)
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
    s = f"{colors.p(f'[ERROR😱{a}]:', [colors.BG_RED])} {colors.p(m, [colors.HRED])}"
    
    print(s)
    
    if e:
        return e
    else:
        return ValueError(m)


def inf(message: str, end: str = "\n") -> str:
    """Prints an informational message."""
    s = f"{colors.p('[INFO🤓]:', [colors.BG_CYAN])} {colors.p(message, [colors.HCYAN])}"
    print(s, end=end)
    return message


def war(message: str, end: str = "\n") -> str:
    """Prints a warning message."""
    s = f"{colors.p('[WARNING😳]:', [colors.BG_YELLOW])} {colors.p(message, [colors.HYELLOW])}"
    print(s, end=end)
    return message


def suc(message: str, end: str = "\n") -> str:
    """Prints a success message."""
    s = f"{colors.p('[SUCCESS🥹 ]:', [colors.BG_GREEN])} {colors.p(message, [colors.HGREEN])}"
    print(s, end=end)
    return message


T = TypeVar("T")


def ins(obj: T, message: str | None = None) -> T:
    print(colors.p('[INSPECT🧐]:', [colors.BG_MAGENTA]), end=" ")
    if message:
        print(colors.p(message, [colors.HMAGENTA]))
    else:
        print("")
    ic.configureOutput(prefix=obj.__class__.__name__ + " ")
    # ic(cull_long_string(obj)) # FIXME
    print(colors.p(try_format(repr(obj)), [colors.HMAGENTA]))
    return obj

def rep(message: str, replier: str | None, end: str = "\n"):
    """Prints a message with a replier prefix."""
    if replier is None:
        replier = "beep boop"
    print(f"{colors.p(replier + '🗣🔥 >', [colors.HBLUE])} {message}", end=end)


def inp(user: str | None = None, empty_input_fn: bool = False) -> str:
    """
    Used to get input from the user.

    """
    if user is None:
        user = "goober"
    # * for some reason, input cant print /033 sometimes
    if not empty_input_fn:
        return input(f"{colors.p(user + '🎤 >', [colors.HBLUE])} ")

    # * doing this breaks the input typing
    print(f"{colors.p(user + '🎤 >', [colors.HBLUE])} ", end="")
    return input()


def rin(prompt: str, replier: str | None = None, end: str = "\n") -> str:
    """Used to get input from the user with a specific replier prefix."""
    rep(prompt, replier, end=end)
    return inp()


def try_all_colors():
    """Prints all possible color combinations."""
    print(colors.c(colors.codes))
    colors.print_all_possible_combinations()


def try_all_methods():
    err(m="This is an error message.")
    inf("This is an info message.")
    war("This is a warning message.")
    suc("This is a success message.")
    ins({"key": "value"}, "This is an inspection message.")
    rep("This is a reply message.", "Alice")
    inp("Bob")
    rin("This is a reply input message.")


if __name__ == "__main__":
    try_all_colors()
    try_all_methods()