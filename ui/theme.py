## Every colour, size and font in the UI traces back to this file. Nothing downstream
## should hardcode a hex value or a pixel measurement — pull it from here instead, so the
## whole look can be retuned in one place.
##
## Values are lifted directly from the "Tic Tac Toe UI v2" design.

from pathlib import Path

## ---------- WINDOW
WIDTH = 1300
HEIGHT = 900
FPS = 60
CAPTION = 'Tic Tac Toe — Arcade Edition'


## ---------- PALETTE
# the three stops of the background sky, top to bottom
BG_TOP = (0x14, 0x08, 0x2E)
BG_MID = (0x1B, 0x0A, 0x3C)
BG_BOTTOM = (0x2B, 0x11, 0x57)

PANEL = (0x24, 0x12, 0x49)      # cards and dialogs, usually blitted at 85% alpha
CELL = (0x22, 0x10, 0x46)       # a board square
INPUT_BG = (0x17, 0x09, 0x33)   # text fields and the score pill
BORDER = (0x3D, 0x2A, 0x6D)     # the default 1px outline on everything

# the two players, and the accents built from them
X_ORANGE = (0xFF, 0x9F, 0x43)
O_CYAN = (0x3D, 0xD6, 0xFF)
GOLD = (0xFF, 0xD1, 0x66)       # win line, scores, the "selected" state
PINK = (0xFF, 0x4D, 0x6D)       # danger, and the far end of the primary gradient
GREEN = (0x3E, 0xF0, 0x8A)      # easy difficulty only

# text, brightest to dimmest
TEXT = (0xF4, 0xEF, 0xFF)
TEXT_SOFT = (0xC9, 0xBB, 0xF0)
TEXT_MUTED = (0xA2, 0x93, 0xD1)
TEXT_DIM = (0x8B, 0x7B, 0xB8)

# dark inks, for text sitting *on* a bright accent
INK = (0x1B, 0x0A, 0x3C)
INK_DEEP = (0x07, 0x12, 0x33)

# the colour the glows are tinted with — warmer than X_ORANGE on purpose
EMBER = (0xFF, 0x6B, 0x35)

OVERLAY = (0x06, 0x02, 0x14, 199)   # rgba(6,2,20,.78) behind modals
CELL_BORDER = (*O_CYAN, 56)         # rgba(61,214,255,.22)
PANEL_ALPHA = 217                   # the .85 that cards are drawn at


## ---------- GRADIENTS
# each is a list of (position 0..1, colour) stops
SKY = [(0.0, BG_TOP), (0.55, BG_MID), (1.0, BG_BOTTOM)]
SKY_LOW = [(0.0, BG_TOP), (0.65, BG_MID), (1.0, BG_BOTTOM)]     # board screens sit the mid stop lower
SUN = [(0.0, GOLD), (0.55, (0xFF, 0x8B, 0x3D)), (1.0, PINK)]
PRIMARY = [(0.0, X_ORANGE), (1.0, PINK)]                        # buttons, X's turn banner
ELECTRIC = [(0.0, O_CYAN), (1.0, (0x2B, 0x7F, 0xFF))]           # O's turn banner
TITLE = [(0.15, GOLD), (0.55, (0xFF, 0x8B, 0x3D)), (0.95, PINK)]


## ---------- FONTS
FONT_DIR = Path(__file__).parent / 'assets' / 'fonts'

DISPLAY = 'Righteous-Regular'    # titles, buttons, scores — the arcade voice
BODY = {
    400: 'Rubik-Regular',
    500: 'Rubik-Medium',
    600: 'Rubik-SemiBold',
    700: 'Rubik-Bold',
}
ICON = 'Phosphor-Regular'
ICON_FILL = 'Phosphor-Fill'


## ---------- GEOMETRY
# board: 420 outer, 12 padding, 12 gaps -> (420 - 24 - 24) / 3 = 124 per cell
BOARD_SIZE = 420
BOARD_PAD = 12
BOARD_GAP = 12
CELL_SIZE = (BOARD_SIZE - 2 * BOARD_PAD - 2 * BOARD_GAP) // 3
CELL_RADIUS = 14
BOARD_RADIUS = 20

MARK_SIZE = 66          # the X/O drawn inside a cell
MARK_X_BAR = 16         # thickness of each arm of the X
MARK_O_RING = 15        # thickness of the O's ring

# the board row: 190 card + 34 gap + 420 board + 34 gap + 190 card = 868, centred in 900
PLAYER_CARD_W = 190
BOARD_ROW_GAP = 34

MODE_CARD_W = 290       # main menu
DIFFICULTY_CARD_W = 236
NAME_CARD_W = 310
INPUT_H = 50

DIALOG_WIN_W = 410
DIALOG_PAUSE_W = 360
DIALOG_PAD = 36

RADIUS_LG = 20
RADIUS_MD = 16
RADIUS_SM = 14
RADIUS_XS = 10
RADIUS_PILL = 999

ICON_BTN_MENU = 48      # the round buttons on menu screens
ICON_BTN_GAME = 44      # slightly smaller in-game

HOVER_LIFT = 4          # how far a card rises when hovered


## ---------- TIMING (seconds)
MARK_POP = 0.20         # scale 0 -> 1.1 -> 1 when a mark lands
WIN_SWEEP = 0.30        # the gold line drawing itself across the winning cells
DIALOG_POP = 0.22
BACKDROP_FADE = 0.15
BLINK_SLOW = 1.6        # PRESS START
BLINK_CARET = 1.1
PULSE_DOT = 1.6
PULSE_TURN = 1.2
AGENT_THINK = 0.5       # pause before an agent commits, so its move doesn't snap in


## ---------- RULES
WINS_NEEDED = 3         # "First to three wins takes the match"
