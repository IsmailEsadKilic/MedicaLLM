from icecream import ic
from typing import TypeVar
import traceback
import sys
import time
import threading

class printmeup:

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
            >>> printmeup.cc([printmeup.HRED, "1", "BG_YELLOW"])
            "\\033[91;1;43m"
        """
        l = len(codes)
        for index, code in enumerate(codes):
            if code not in printmeup.codes:
                try:
                    code = getattr(printmeup, code, None)
                    if code in printmeup.codes:
                        codes[index] = code
                        continue
                except AttributeError:
                    pass
                raise ValueError(f"Invalid color code: {code}")

        if l == 1:
            return f"\033[{codes[0]}m"

        if l > 1:
            return f"\033[{';'.join(codes)}m"

        return f"\033[{printmeup.ENDC}m"

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
        return f"{printmeup.ec(codes)}{message}{printmeup.ec([printmeup.ENDC])}"

    @staticmethod
    def print_all_possible_combinations():
        c = 0
        for i in range(1, 8):
            for j in range(7, 16):
                for k in range(15, 24):
                    color1 = printmeup.codes[i]
                    color2 = printmeup.codes[j]
                    color3 = printmeup.codes[k]
                    print(
                        f"\033[{color1};{color2};{color3}m Color {color1}, {color2}, and {color3}\033[0m"
                    )
                    c += 1
        print(f"Total combinations: {c}")
        
    @staticmethod
    def try_all_colors():
        """Prints all possible color combinations."""
        print(printmeup.ec(printmeup.codes))
        printmeup.print_all_possible_combinations()
        
    @staticmethod
    def cull_long_string(obj: dict | list | str) -> dict | list | str:
        """
        Recursively culls long strings in a dictionary or list.
        If a string is longer than 1000 characters, it replaces it with a placeholder.
        """
        if isinstance(obj, str):
            if len(obj) > 1000:
                return printmeup.p(f"< A LONG STRING OF {len(obj)} 🤯 >", [printmeup.HYELLOW])
            return obj
        if isinstance(obj, list):
            return [printmeup.cull_long_string(item) for item in obj]
        if isinstance(obj, dict):
            return {k: printmeup.cull_long_string(v) for k, v in obj.items()}
        return obj
    
    buffer: str = ""
    
    def pr(self, message: str, end: str = "\n"):
        """Prints a message to stdout."""
        if end == "\n" or "\n" in message:
            if self.animated_text_thread_ll:
                self.animated_text_thread_ll.stop()
                self.buffer=message+end
                return
        
        print(message, end=end)
      
    def deb(self, message: str, end: str = "\n") -> str:
        """Prints a debug message."""
        self.pr(f"{printmeup.p('[DEBUG🐛]:', [printmeup.BG_BLUE])} {printmeup.p(message, [printmeup.HBLUE])}", end=end)
        return message

    def err(
        self,
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
        self.pr(f"{printmeup.p(f'[ERROR😱{a}]:', [printmeup.BG_RED])} {printmeup.p(m, [printmeup.HRED])}")
                
        if e:
            return e
        else:
            return ValueError(m)

    def inf(self, message: str, end: str = "\n") -> str:
        """Prints an informational message."""
        self.pr(f"{printmeup.p('[INFO🤓]:', [printmeup.BG_CYAN])} {printmeup.p(message, [printmeup.HCYAN])}", end=end)
        return message

    def war(self, message: str, end: str = "\n") -> str:
        """Prints a warning message."""
        self.pr(f"{printmeup.p('[WARNING😳]:', [printmeup.BG_YELLOW])} {printmeup.p(message, [printmeup.HYELLOW])}", end=end)
        return message

    def suc(self, message: str, end: str = "\n") -> str:
        """Prints a success message."""
        self.pr(f"{printmeup.p('[SUCCESS🥹 ]:', [printmeup.BG_GREEN])} {printmeup.p(message, [printmeup.HGREEN])}", end=end)
        return message

    def rep(self, message: str, replier: str | None, end: str = "\n"):
        """Prints a message with a replier prefix."""
        if replier is None:
            replier = "beep boop"
        self.pr(f"{printmeup.p(replier + '🗣 🔥>', [printmeup.HBLUE])} {message}", end=end)


    def inp(self, user: str | None = None) -> str:
        """
        Used to get input from the user.
        """
        if user is None:
            user = "goober"
            
        self.pr(f"{printmeup.p(user + '🎤>', [printmeup.HBLUE])} ", end="")
        return input()
    
    
    def rin(self, prompt: str, replier: str | None = None, end: str = "\n") -> str:
        """Used to get input from the user with a specific replier prefix."""
        self.rep(prompt, replier, end=end)
        return self.inp()
    
    T = TypeVar("T")

    def ins(self, obj: T, message: str | None = None) -> T:
        print(printmeup.p('[INSPECT🧐]:', [printmeup.BG_MAGENTA]), end=" ")
        if message:
            print(printmeup.p(message, [printmeup.HMAGENTA]))
        else:
            print("")
        ic.configureOutput(prefix=obj.__class__.__name__ + " ")
        return obj
    
    def try_all_methods(self):
        self.err(m="This is an error message.")
        self.inf("This is an info message.")
        self.war("This is a warning message.")
        self.deb("This is a debug message.")
        self.suc("This is a success message.")
        self.ins({"key": "value"}, "This is an inspection message.")
        self.rep("This is a reply message.", "Alice")
        self.inp("Bob")
        self.rin("This is a reply input message.")

    
    @staticmethod
    def cb(count: int) -> str:
        """cursor back"""
        return f"\033[{count}D"
    
    @staticmethod
    def cf(count: int) -> str:
        """cursor forward"""
        return f"\033[{count}C"
    
    @staticmethod
    def cu(count: int) -> str:
        """cursor up"""
        return f"\033[{count}A"
    
    @staticmethod
    def cd(count: int) -> str:
        """cursor down"""
        return f"\033[{count}B"
    
    class animated_text_thread:
        run: bool = True
        thread: threading.Thread
        
        def stop(self):
            self.run = False
            print()

    animated_text_thread_ll: animated_text_thread| None = None
    # * last line
        
    def animated_print_rainbow(self, text: str):
        """Prints animated rainbow text in the terminal."""
        
        if self.animated_text_thread_ll:
            self.animated_text_thread_ll.stop()
            
        thread = self.animated_text_thread()
        self.animated_text_thread_ll = thread
        
        color_count = len(self.RAINBOW_COLORS)
        
        def animate():
            index = 0
            
            while thread.run:
                output = ""
                for char in text:
                    color = self.RAINBOW_COLORS[index % color_count]
                    output += f"{color}{char}"
                    index += 1
                
                output += self.ec([self.ENDC])
                print(f"\r{output}", end="", flush=True)
                time.sleep(0.2)
                index = (index + 1) % color_count
                                                
        thread.thread = threading.Thread(target=animate, daemon=True)
        thread.thread.start()
        
    def animated_print_rainbow_interp(self, text: str):
        """Prints animated rainbow text in the terminal. Only text inside {} brackets is animated."""
        
        if self.animated_text_thread_ll:
            self.animated_text_thread_ll.stop()
            
        thread = self.animated_text_thread()
        self.animated_text_thread_ll = thread
                    
        color_count = len(self.RAINBOW_COLORS)
        
        parts = []
        current = ""
        in_brackets = False
        
        for char in text:
            if char == '{':
                if current:
                    parts.append(('static', current))
                    current = ""
                in_brackets = True
            elif char == '}':
                if current:
                    parts.append(('animated', current))
                    current = ""
                in_brackets = False
            else:
                current += char
        
        if current:
            parts.append(('static' if not in_brackets else 'animated', current))
        
        def animate():
            index = 0

            while thread.run:
                output = ""
                animated_char_index = 0
                
                for part_type, part_text in parts:
                    if part_type == 'static':
                        output += self.ec([self.ENDC]) + part_text
                    else:  # animated
                        for char in part_text:
                            color = self.RAINBOW_COLORS[(index + animated_char_index) % color_count]
                            output += f"{color}{char}"
                            animated_char_index += 1
                
                output += self.ec([self.ENDC])
                if not thread.run:
                    thread.thread.join()
                print(f"\r{output}", end="", flush=True)
                time.sleep(0.2)
                index = (index + 1) % color_count
                                    
        thread.thread = threading.Thread(target=animate, daemon=True)
        thread.thread.start()

    def animated_print_loading(self, text: str):
        """Prints animated loading text in the terminal."""
        
        thread = self.animated_text_thread()
        
        loading_chars = ['|', '/', '-', '\\']
        loading_char_count = len(loading_chars)
        
        def animate():
            index = 0
            
            while thread.run:
                output = f"{text} {loading_chars[index % loading_char_count]}"
                print(f"\r{output}", end="", flush=True)
                time.sleep(0.2)
                index += 1
            
            print()
            print(self.buffer, end="")
                        
        thread.thread = threading.Thread(target=animate, daemon=True)
        thread.thread.start()
        self.animated_text_thread_ll = thread   
        
if __name__ == "__main__":
    pm = printmeup()
    pm.pr("a")
    pm.pr("b")
    pm.animated_print_rainbow_interp("Hello, {world!} Skibidi {bop yes yes yes yes \n yes yes yes yes} asd")
    time.sleep(5)

    pm.animated_print_rainbow("cin")
    time.sleep(5)  # Let the animation run for 5 seconds
    pm.pr("asda\nsd", end="")
    pm.pr("c")
    time.sleep(2)
    pm.animated_print_loading("Loading")
    time.sleep(2)
    # pm.try_all_colors()
    # pm.try_all_methods()