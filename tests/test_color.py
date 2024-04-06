from northy.color import colored

def test_colored():
    # Test all colors
    for color in ["red", "green", "yellow", "blue", "magenta", "cyan", "white"]:
        assert colored("Hello", color)
    
    # Test default color
    colored('Hello')
