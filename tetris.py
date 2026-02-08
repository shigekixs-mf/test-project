"""Tetris game implemented with pygame.

Uses a custom bitmap font renderer so that pygame.font is NOT required.
This avoids compatibility issues with Python 3.14+ where pygame.font
may fail to import.
"""

import random
import sys

import pygame

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CELL = 30  # px per cell
COLS = 10
ROWS = 20
SIDEBAR_W = 200

SCREEN_W = CELL * COLS + SIDEBAR_W
SCREEN_H = CELL * ROWS

FPS = 60

# Colours (R, G, B)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (40, 40, 40)
DARK_GRAY = (80, 80, 80)
BG_COLOR = (20, 20, 30)
GRID_COLOR = (40, 40, 50)

PIECE_COLORS = {
    "I": (0, 240, 240),
    "O": (240, 240, 0),
    "T": (160, 0, 240),
    "S": (0, 240, 0),
    "Z": (240, 0, 0),
    "J": (0, 0, 240),
    "L": (240, 160, 0),
}

# Each piece: list of rotations, each rotation is a list of (row, col) offsets
SHAPES = {
    "I": [
        [(0, 0), (0, 1), (0, 2), (0, 3)],
        [(0, 0), (1, 0), (2, 0), (3, 0)],
    ],
    "O": [
        [(0, 0), (0, 1), (1, 0), (1, 1)],
    ],
    "T": [
        [(0, 0), (0, 1), (0, 2), (1, 1)],
        [(0, 0), (1, 0), (2, 0), (1, 1)],
        [(1, 0), (1, 1), (1, 2), (0, 1)],
        [(0, 0), (1, 0), (2, 0), (1, -1)],
    ],
    "S": [
        [(0, 1), (0, 2), (1, 0), (1, 1)],
        [(0, 0), (1, 0), (1, 1), (2, 1)],
    ],
    "Z": [
        [(0, 0), (0, 1), (1, 1), (1, 2)],
        [(0, 1), (1, 0), (1, 1), (2, 0)],
    ],
    "J": [
        [(0, 0), (1, 0), (1, 1), (1, 2)],
        [(0, 0), (0, 1), (1, 0), (2, 0)],
        [(0, 0), (0, 1), (0, 2), (1, 2)],
        [(0, 0), (1, 0), (2, 0), (2, -1)],
    ],
    "L": [
        [(0, 2), (1, 0), (1, 1), (1, 2)],
        [(0, 0), (1, 0), (2, 0), (2, 1)],
        [(0, 0), (0, 1), (0, 2), (1, 0)],
        [(0, 0), (0, 1), (1, 1), (2, 1)],
    ],
}

PIECE_NAMES = list(SHAPES.keys())

# Scoring (original Nintendo-style)
LINE_SCORES = {0: 0, 1: 100, 2: 300, 3: 500, 4: 800}


# ---------------------------------------------------------------------------
# Bitmap font — each glyph is a 5-wide x 7-tall pixel pattern
# ---------------------------------------------------------------------------

_GLYPHS: dict[str, list[str]] = {
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "B": ["11110", "10001", "10001", "11110", "10001", "10001", "11110"],
    "C": ["01110", "10001", "10000", "10000", "10000", "10001", "01110"],
    "D": ["11110", "10001", "10001", "10001", "10001", "10001", "11110"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    "F": ["11111", "10000", "10000", "11110", "10000", "10000", "10000"],
    "G": ["01110", "10001", "10000", "10111", "10001", "10001", "01110"],
    "H": ["10001", "10001", "10001", "11111", "10001", "10001", "10001"],
    "I": ["01110", "00100", "00100", "00100", "00100", "00100", "01110"],
    "J": ["00111", "00010", "00010", "00010", "10010", "10010", "01100"],
    "K": ["10001", "10010", "10100", "11000", "10100", "10010", "10001"],
    "L": ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
    "M": ["10001", "11011", "10101", "10101", "10001", "10001", "10001"],
    "N": ["10001", "11001", "10101", "10011", "10001", "10001", "10001"],
    "O": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    "P": ["11110", "10001", "10001", "11110", "10000", "10000", "10000"],
    "Q": ["01110", "10001", "10001", "10001", "10101", "10010", "01101"],
    "R": ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    "S": ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
    "T": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    "U": ["10001", "10001", "10001", "10001", "10001", "10001", "01110"],
    "V": ["10001", "10001", "10001", "10001", "10001", "01010", "00100"],
    "W": ["10001", "10001", "10001", "10101", "10101", "11011", "10001"],
    "X": ["10001", "10001", "01010", "00100", "01010", "10001", "10001"],
    "Y": ["10001", "10001", "01010", "00100", "00100", "00100", "00100"],
    "Z": ["11111", "00001", "00010", "00100", "01000", "10000", "11111"],
    "0": ["01110", "10011", "10101", "10101", "10101", "11001", "01110"],
    "1": ["00100", "01100", "00100", "00100", "00100", "00100", "01110"],
    "2": ["01110", "10001", "00001", "00110", "01000", "10000", "11111"],
    "3": ["01110", "10001", "00001", "00110", "00001", "10001", "01110"],
    "4": ["00010", "00110", "01010", "10010", "11111", "00010", "00010"],
    "5": ["11111", "10000", "11110", "00001", "00001", "10001", "01110"],
    "6": ["00110", "01000", "10000", "11110", "10001", "10001", "01110"],
    "7": ["11111", "00001", "00010", "00100", "01000", "01000", "01000"],
    "8": ["01110", "10001", "10001", "01110", "10001", "10001", "01110"],
    "9": ["01110", "10001", "10001", "01111", "00001", "00010", "01100"],
    " ": ["00000", "00000", "00000", "00000", "00000", "00000", "00000"],
    ":": ["00000", "00100", "00100", "00000", "00100", "00100", "00000"],
    "-": ["00000", "00000", "00000", "11111", "00000", "00000", "00000"],
    ".": ["00000", "00000", "00000", "00000", "00000", "01100", "01100"],
    ",": ["00000", "00000", "00000", "00000", "00000", "00100", "01000"],
}


def _draw_text(
    surface: pygame.Surface,
    text: str,
    x: int,
    y: int,
    color: tuple[int, int, int],
    scale: int = 2,
) -> None:
    """Render *text* at (x, y) using the bitmap font with given pixel scale."""
    cursor_x = x
    for ch in text.upper():
        glyph = _GLYPHS.get(ch)
        if glyph is None:
            cursor_x += 6 * scale  # treat unknown as space
            continue
        for row_idx, row_bits in enumerate(glyph):
            for col_idx, bit in enumerate(row_bits):
                if bit == "1":
                    px = cursor_x + col_idx * scale
                    py = y + row_idx * scale
                    pygame.draw.rect(surface, color, (px, py, scale, scale))
        cursor_x += 6 * scale  # 5 px wide + 1 px gap


def _text_width(text: str, scale: int = 2) -> int:
    return len(text) * 6 * scale


# ---------------------------------------------------------------------------
# Helper classes
# ---------------------------------------------------------------------------


class Piece:
    """A falling tetromino."""

    def __init__(self, name: str):
        self.name = name
        self.rotations = SHAPES[name]
        self.rot_index = 0
        self.color = PIECE_COLORS[name]
        # Start centred at top
        self.row = 0
        self.col = COLS // 2 - 1

    @property
    def cells(self) -> list[tuple[int, int]]:
        """Return absolute (row, col) positions of each block."""
        return [
            (self.row + dr, self.col + dc)
            for dr, dc in self.rotations[self.rot_index]
        ]

    def rotated_cells(self, direction: int = 1) -> list[tuple[int, int]]:
        """Return cells after rotation without mutating state."""
        idx = (self.rot_index + direction) % len(self.rotations)
        return [
            (self.row + dr, self.col + dc)
            for dr, dc in self.rotations[idx]
        ]

    def rotate(self, direction: int = 1) -> None:
        self.rot_index = (self.rot_index + direction) % len(self.rotations)


# ---------------------------------------------------------------------------
# Board helpers
# ---------------------------------------------------------------------------


def empty_board() -> list[list[str | None]]:
    return [[None] * COLS for _ in range(ROWS)]


def is_valid(board: list[list[str | None]], cells: list[tuple[int, int]]) -> bool:
    for r, c in cells:
        if r < 0 or r >= ROWS or c < 0 or c >= COLS:
            return False
        if board[r][c] is not None:
            return False
    return True


def lock_piece(board: list[list[str | None]], piece: Piece) -> None:
    for r, c in piece.cells:
        if 0 <= r < ROWS and 0 <= c < COLS:
            board[r][c] = piece.name


def clear_lines(board: list[list[str | None]]) -> int:
    cleared = 0
    r = ROWS - 1
    while r >= 0:
        if all(cell is not None for cell in board[r]):
            del board[r]
            board.insert(0, [None] * COLS)
            cleared += 1
        else:
            r -= 1
    return cleared


# ---------------------------------------------------------------------------
# Drawing
# ---------------------------------------------------------------------------


def draw_block(surface: pygame.Surface, row: int, col: int, color: tuple, x_offset: int = 0) -> None:
    """Draw a single block with a slight 3D-ish bevel."""
    x = col * CELL + x_offset
    y = row * CELL
    pygame.draw.rect(surface, color, (x, y, CELL, CELL))
    # Highlight
    lighter = tuple(min(c + 50, 255) for c in color)
    pygame.draw.line(surface, lighter, (x, y), (x + CELL - 1, y))
    pygame.draw.line(surface, lighter, (x, y), (x, y + CELL - 1))
    # Shadow
    darker = tuple(max(c - 60, 0) for c in color)
    pygame.draw.line(surface, darker, (x + CELL - 1, y), (x + CELL - 1, y + CELL - 1))
    pygame.draw.line(surface, darker, (x, y + CELL - 1), (x + CELL - 1, y + CELL - 1))


def _draw_block_abs(surface: pygame.Surface, px: int, py: int, color: tuple) -> None:
    """Draw a single block at absolute pixel position."""
    pygame.draw.rect(surface, color, (px, py, CELL, CELL))
    lighter = tuple(min(c + 50, 255) for c in color)
    pygame.draw.line(surface, lighter, (px, py), (px + CELL - 1, py))
    pygame.draw.line(surface, lighter, (px, py), (px, py + CELL - 1))
    darker = tuple(max(c - 60, 0) for c in color)
    pygame.draw.line(surface, darker, (px + CELL - 1, py), (px + CELL - 1, py + CELL - 1))
    pygame.draw.line(surface, darker, (px, py + CELL - 1), (px + CELL - 1, py + CELL - 1))


def draw_board(surface: pygame.Surface, board: list[list[str | None]]) -> None:
    for r in range(ROWS):
        for c in range(COLS):
            name = board[r][c]
            if name:
                draw_block(surface, r, c, PIECE_COLORS[name])

    # Grid lines
    for r in range(ROWS + 1):
        pygame.draw.line(surface, GRID_COLOR, (0, r * CELL), (COLS * CELL, r * CELL))
    for c in range(COLS + 1):
        pygame.draw.line(surface, GRID_COLOR, (c * CELL, 0), (c * CELL, ROWS * CELL))


def draw_piece(surface: pygame.Surface, piece: Piece) -> None:
    for r, c in piece.cells:
        if r >= 0:
            draw_block(surface, r, c, piece.color)


def draw_ghost(surface: pygame.Surface, board: list[list[str | None]], piece: Piece) -> None:
    """Draw a translucent ghost showing where the piece will land."""
    ghost = Piece(piece.name)
    ghost.rot_index = piece.rot_index
    ghost.row = piece.row
    ghost.col = piece.col
    while is_valid(board, [(r + 1, c) for r, c in ghost.cells]):
        ghost.row += 1
    if ghost.row == piece.row:
        return
    ghost_color = tuple(c // 4 for c in piece.color)
    for r, c in ghost.cells:
        if r >= 0:
            x = c * CELL
            y = r * CELL
            pygame.draw.rect(surface, ghost_color, (x + 1, y + 1, CELL - 2, CELL - 2), 1)


def draw_sidebar(surface: pygame.Surface, score: int, level: int, lines: int, next_piece: Piece) -> None:
    x0 = COLS * CELL + 20

    # Score
    _draw_text(surface, "SCORE", x0, 20, WHITE, scale=2)
    _draw_text(surface, str(score), x0, 40, WHITE, scale=2)

    # Level
    _draw_text(surface, "LEVEL", x0, 80, WHITE, scale=2)
    _draw_text(surface, str(level), x0, 100, WHITE, scale=2)

    # Lines
    _draw_text(surface, "LINES", x0, 140, WHITE, scale=2)
    _draw_text(surface, str(lines), x0, 160, WHITE, scale=2)

    # Next piece
    _draw_text(surface, "NEXT", x0, 220, WHITE, scale=2)

    preview_cells = SHAPES[next_piece.name][0]
    color = PIECE_COLORS[next_piece.name]
    for dr, dc in preview_cells:
        px = x0 + 10 + dc * CELL
        py = 250 + dr * CELL
        _draw_block_abs(surface, px, py, color)

    # Controls hint (smaller scale)
    controls = [
        "CONTROLS:",
        "  MOVE",
        "  ROTATE",
        "  SOFT DROP",
        "SPACE HARD DROP",
        "P PAUSE",
        "R RESTART",
    ]
    for i, line in enumerate(controls):
        _draw_text(surface, line, x0, 400 + i * 18, DARK_GRAY, scale=1)


def draw_game_over(surface: pygame.Surface) -> None:
    overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 150))
    surface.blit(overlay, (0, 0))

    text = "GAME OVER"
    tw = _text_width(text, scale=4)
    _draw_text(surface, text, COLS * CELL // 2 - tw // 2, SCREEN_H // 2 - 40, WHITE, scale=4)

    text2 = "PRESS R TO RESTART"
    tw2 = _text_width(text2, scale=2)
    _draw_text(surface, text2, COLS * CELL // 2 - tw2 // 2, SCREEN_H // 2 + 20, WHITE, scale=2)


def draw_pause(surface: pygame.Surface) -> None:
    overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 150))
    surface.blit(overlay, (0, 0))

    text = "PAUSED"
    tw = _text_width(text, scale=4)
    _draw_text(surface, text, COLS * CELL // 2 - tw // 2, SCREEN_H // 2 - 14, WHITE, scale=4)


# ---------------------------------------------------------------------------
# Game
# ---------------------------------------------------------------------------


class Game:
    def __init__(self) -> None:
        self.board = empty_board()
        self.score = 0
        self.lines = 0
        self.level = 1
        self.bag: list[str] = []
        self.current = self._new_piece()
        self.next = self._new_piece()
        self.game_over = False
        self.paused = False

        # Timing
        self.drop_interval = self._calc_interval()
        self.drop_timer = 0
        self.move_delay = 170  # ms before auto-repeat starts
        self.move_repeat = 50  # ms between repeats
        self.move_timer = 0
        self.move_dir = 0

    def _refill_bag(self) -> None:
        self.bag = PIECE_NAMES[:]
        random.shuffle(self.bag)

    def _new_piece(self) -> Piece:
        if not self.bag:
            self._refill_bag()
        return Piece(self.bag.pop())

    def _calc_interval(self) -> int:
        """Frames-per-drop converted to ms, faster at higher levels."""
        return max(100, 800 - (self.level - 1) * 70)

    def spawn_next(self) -> None:
        self.current = self.next
        self.next = self._new_piece()
        if not is_valid(self.board, self.current.cells):
            self.game_over = True

    def move(self, dr: int, dc: int) -> bool:
        new_cells = [(r + dr, c + dc) for r, c in self.current.cells]
        if is_valid(self.board, new_cells):
            self.current.row += dr
            self.current.col += dc
            return True
        return False

    def rotate(self, direction: int = 1) -> None:
        new_cells = self.current.rotated_cells(direction)
        if is_valid(self.board, new_cells):
            self.current.rotate(direction)
            return
        # Wall kick: try shifting left/right by 1 or 2
        for offset in [1, -1, 2, -2]:
            kicked = [(r, c + offset) for r, c in new_cells]
            if is_valid(self.board, kicked):
                self.current.rotate(direction)
                self.current.col += offset
                return

    def hard_drop(self) -> None:
        while self.move(1, 0):
            self.score += 2
        self._lock_and_clear()

    def soft_drop(self) -> bool:
        if self.move(1, 0):
            self.score += 1
            return True
        return False

    def _lock_and_clear(self) -> None:
        lock_piece(self.board, self.current)
        cleared = clear_lines(self.board)
        self.lines += cleared
        self.score += LINE_SCORES.get(cleared, 0) * self.level
        self.level = self.lines // 10 + 1
        self.drop_interval = self._calc_interval()
        self.spawn_next()

    def tick(self, dt: int) -> None:
        """Called every frame with dt in ms."""
        if self.game_over or self.paused:
            return

        self.drop_timer += dt
        if self.drop_timer >= self.drop_interval:
            self.drop_timer = 0
            if not self.move(1, 0):
                self._lock_and_clear()

    def restart(self) -> None:
        self.__init__()


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------


def main() -> None:
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("Tetris")
    clock = pygame.time.Clock()

    game = Game()

    # Key repeat state
    held_keys: dict[int, int] = {}  # key -> elapsed ms

    while True:
        dt = clock.tick(FPS)

        # --- Events ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    game.restart()
                    held_keys.clear()
                    continue
                if game.game_over:
                    continue
                if event.key == pygame.K_p:
                    game.paused = not game.paused
                    continue
                if game.paused:
                    continue

                if event.key == pygame.K_LEFT:
                    game.move(0, -1)
                    held_keys[pygame.K_LEFT] = 0
                elif event.key == pygame.K_RIGHT:
                    game.move(0, 1)
                    held_keys[pygame.K_RIGHT] = 0
                elif event.key == pygame.K_DOWN:
                    game.soft_drop()
                    held_keys[pygame.K_DOWN] = 0
                elif event.key == pygame.K_UP:
                    game.rotate()
                elif event.key == pygame.K_SPACE:
                    game.hard_drop()

            if event.type == pygame.KEYUP:
                held_keys.pop(event.key, None)

        # --- Auto-repeat for held keys ---
        if not game.game_over and not game.paused:
            for key in [pygame.K_LEFT, pygame.K_RIGHT, pygame.K_DOWN]:
                if key in held_keys:
                    held_keys[key] += dt
                    if held_keys[key] >= game.move_delay:
                        repeat_elapsed = held_keys[key] - game.move_delay
                        if repeat_elapsed % game.move_repeat < dt:
                            if key == pygame.K_LEFT:
                                game.move(0, -1)
                            elif key == pygame.K_RIGHT:
                                game.move(0, 1)
                            elif key == pygame.K_DOWN:
                                game.soft_drop()

        # --- Update ---
        game.tick(dt)

        # --- Draw ---
        screen.fill(BG_COLOR)
        draw_board(screen, game.board)
        if not game.game_over:
            draw_ghost(screen, game.board, game.current)
            draw_piece(screen, game.current)
        draw_sidebar(screen, game.score, game.level, game.lines, game.next)

        if game.game_over:
            draw_game_over(screen)
        elif game.paused:
            draw_pause(screen)

        pygame.display.flip()


if __name__ == "__main__":
    main()
