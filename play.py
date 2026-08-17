## Entry point for the graphical game.
##
##     uv run play.py
##
## main.py is still the terminal-side harness for batch-testing agents against each other;
## this is the one you play.

from ui.app import App
from ui.screens.menu import MenuScreen


def main():
    app = App()
    app.push(MenuScreen(app))
    app.run()


if __name__ == '__main__':
    main()
