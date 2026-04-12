from typing import TypeVar
import logging
import os
import traceback

app_name = os.getenv("APP_NAME", "app")
log_level = os.getenv("LOG_LEVEL", "DEBUG").upper()
#* DEBUG(includes INSPECT) > INFO(includes SUCCESS) > WARNING > ERROR > CRITICAL
log_dir = os.getenv("LOG_DIR", "logs")

ic_en = False

log_level_n = 5
if log_level == "DEBUG":
    try:
        from icecream import ic # type: ignore
    except ImportError:
        ic_en = False
        pass
elif log_level == "INFO":
    log_level_n = 4
elif log_level == "WARNING":
    log_level_n = 3
elif log_level == "ERROR":
    log_level_n = 2
elif log_level == "CRITICAL":
    log_level_n = 1

    

os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    level=getattr(logging, log_level, logging.DEBUG),
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(f"{log_dir}/{app_name}.log", encoding="utf-8"),
    ]
)

logger = logging.getLogger(app_name)

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

def cull_long_string(obj: dict | list | str) -> dict | list | str:
    """
    Recursively culls long strings in a dictionary or list.
    If a string is longer than 1000 characters, it replaces it with a placeholder.
    """
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
    if log_level_n > 4:
        s = f"{colors.p('[DEBUG🐛]:', [colors.BG_BLUE])} {colors.p(message, [colors.HBLUE])}"
        print(s, end=end)
        logger.debug(message)
    return message

def err(
    e: Exception | None = None, m: str | None = None, a: str | None = None
) -> Exception:
    """Prints an error message."""
    if log_level_n > 1:
        if not m:
            if e is not None:
                m = e.__repr__()
            else:
                m = "An error occurred."
        a = f"@{a}" if a else ""
        print(f"{colors.p(f'[ERROR😱{a}]:', [colors.BG_RED])} {colors.p(m, [colors.HRED])}")
        
        #* Print traceback to console if exception exists
        if e:
            tb_lines = traceback.format_exception(type(e), e, e.__traceback__)
            for line in tb_lines:
                print(colors.p(line.rstrip(), [colors.HRED]))
        
        logger.error(f"{m}{' ' + a if a else ''}", exc_info=e)
    if e:
        return e
    else:
        return ValueError(m)
    
def crt(e: Exception | None = None, m: str | None = None, a: str | None = None) -> Exception:
    """Prints a critical error message."""
    if log_level_n > 0:
        if not m:
            if e is not None:
                m = e.__repr__()
            else:
                m = "A critical error occurred."
        a = f"@{a}" if a else ""
        print(f"{colors.p(f'[CRITICAL💀{a}]:', [colors.BG_RED, colors.BLINK])} {colors.p(m, [colors.HRED, colors.BOLD])}")
        
        #* Print traceback to console if exception exists
        if e:
            tb_lines = traceback.format_exception(type(e), e, e.__traceback__)
            for line in tb_lines:
                print(colors.p(line.rstrip(), [colors.HRED, colors.BOLD]))
        
        logger.critical(f"{m}{' ' + a if a else ''}", exc_info=e)
    if e:
        return e
    else:
        return RuntimeError(m)


def inf(message: str, end: str = "\n") -> str:
    """Prints an informational message."""
    if log_level_n > 3:
        s = f"{colors.p('[INFO🤓]:', [colors.BG_CYAN])} {colors.p(message, [colors.HCYAN])}"
        print(s, end=end)
        logger.info(message)
    return message


def war(message: str, end: str = "\n") -> str:
    """Prints a warning message."""
    if log_level_n > 2:
        s = f"{colors.p('[WARNING😳]:', [colors.BG_YELLOW])} {colors.p(message, [colors.HYELLOW])}"
        print(s, end=end)
        logger.warning(message)
    return message


def suc(message: str, end: str = "\n") -> str:
    """Prints a success message."""
    if log_level_n > 3:
        s = f"{colors.p('[SUCCESS🥹 ]:', [colors.BG_GREEN])} {colors.p(message, [colors.HGREEN])}"
        print(s, end=end)
        logger.info(f"SUCCESS: {message}")
    return message


T = TypeVar("T")


def ins(obj: T, message: str | None = None) -> T:
    if log_level_n > 4:
        try:
            print(colors.p('[INSPECT🧐]:', [colors.BG_MAGENTA]), end=" ")
            if message:
                print(colors.p(message, [colors.HMAGENTA]))
            else:
                print("")
            if ic_en:
                ic.configureOutput(prefix=obj.__class__.__name__ + " ") # type: ignore
                if isinstance(obj, (dict, list, str)):
                    ic(cull_long_string(obj)) # type: ignore
                else:
                    ic(obj) # type: ignore
            else:
                print(colors.p(str(obj), [colors.HMAGENTA]))
            log_msg = f"INSPECT: {message or obj.__class__.__name__}: {str(obj)[:200]}"
            logger.debug(log_msg)
        except NameError as e:
            err(e=e, m="ins called, ic is enabled but ic is not imported.")
    
    return obj

def rep(message: str, replier: str | None, end: str = "\n"):
    """Prints a message with a replier prefix."""
    if replier is None:
        replier = "beep boop"
    print(f"{colors.p(replier + '🗣🔥 >', [colors.HBLUE])} {message}", end=end)


def inp(user: str | None = None) -> str:
    """
    Used to get input from the user.

    """
    if user is None:
        user = "goober"
    return input(f"{colors.p(user + '🎤 >', [colors.HBLUE])} ")


def rin(prompt: str, replier: str | None = None, end: str = "\n") -> str:
    """Used to get input from the user with a specific replier prefix."""
    rep(prompt, replier, end=end)
    return inp()

def try_all_colors():
    """Prints all possible color combinations."""
    print(colors.c(colors.codes))
    colors.print_all_possible_combinations()


def try_all_methods():
    err(e=ValueError("this is a value error"),m="This is an error message.")
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