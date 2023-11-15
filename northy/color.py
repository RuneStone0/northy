# colorama is supported across all platforms, and will color terminal text
# unline termcolor, which only works on Linux and Mac
from colorama import Fore, Back, Style, init

# Initialize Colorama
init(autoreset=True)

def colored(text, color, bgcolor=Back.BLACK, style=Style.NORMAL):
    if color == "red":
        color = Fore.RED
    elif color == "green":
        color = Fore.GREEN
    elif color == "yellow":
        color = Fore.YELLOW
    elif color == "blue":
        color = Fore.BLUE
    elif color == "magenta":
        color = Fore.MAGENTA
    elif color == "cyan":
        color = Fore.CYAN
    elif color == "white":
        color = Fore.WHITE
    else:
        color = Fore.WHITE

    colored_text = f"{style}{color}{bgcolor}{text}{Style.RESET_ALL}"
    return colored_text
