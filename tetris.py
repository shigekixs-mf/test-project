"""Tetris game implemented with pygame."""

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


def draw_sidebar(surface: pygame.Surface, score: int, level: int, lines: int, next_piece: Piece, font: pygame.font.Font) -> None:
    x0 = COLS * CELL + 20

    # Score
    lbl = font.render("SCORE", True, WHITE)
    surface.blit(lbl, (x0, 20))
    val = font.render(str(score), True, WHITE)
    surface.blit(val, (x0, 50))

    # Level
    lbl = font.render("LEVEL", True, WHITE)
    surface.blit(lbl, (x0, 100))
    val = font.render(str(level), True, WHITE)
    surface.blit(val, (x0, 130))

    # Lines
    lbl = font.render("LINES", True, WHITE)
    surface.blit(lbl, (x0, 180))
    val = font.render(str(lines), True, WHITE)
    surface.blit(val, (x0, 210))

    # Next piece
    lbl = font.render("NEXT", True, WHITE)
    surface.blit(lbl, (x0, 280))

    preview_cells = SHAPES[next_piece.name][0]
    for dr, dc in preview_cells:
        draw_block(surface, dr, dc, PIECE_COLORS[next_piece.name], x_offset=x0 + 10 - (0 * CELL) + dc * 0)
        # Redraw with correct offset
        px = x0 + 10 + dc * CELL
        py = 320 + dr * CELL
        color = PIECE_COLORS[next_piece.name]
        pygame.draw.rect(surface, color, (px, py, CELL, CELL))
        lighter = tuple(min(c + 50, 255) for c in color)
        pygame.draw.line(surface, lighter, (px, py), (px + CELL - 1, py))
        pygame.draw.line(surface, lighter, (px, py), (px, py + CELL - 1))
        darker = tuple(max(c - 60, 0) for c in color)
        pygame.draw.line(surface, darker, (px + CELL - 1, py), (px + CELL - 1, py + CELL - 1))
        pygame.draw.line(surface, darker, (px, py + CELL - 1), (px + CELL - 1, py + CELL - 1))

    # Controls hint
    hint_font = pygame.font.SysFont("monospace", 14)
    controls = [
        "CONTROLS:",
        "← →  Move",
        "↑    Rotate",
        "↓    Soft drop",
        "Space Hard drop",
        "P    Pause",
        "R    Restart",
    ]
    for i, line in enumerate(controls):
        txt = hint_font.render(line, True, DARK_GRAY)
        surface.blit(txt, (x0, 450 + i * 20))


def draw_game_over(surface: pygame.Surface, font: pygame.font.Font) -> None:
    overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 150))
    surface.blit(overlay, (0, 0))

    big = pygame.font.SysFont("monospace", 48, bold=True)
    txt = big.render("GAME OVER", True, WHITE)
    rect = txt.get_rect(center=(COLS * CELL // 2, SCREEN_H // 2 - 30))
    surface.blit(txt, rect)

    small = font.render("Press R to restart", True, WHITE)
    rect2 = small.get_rect(center=(COLS * CELL // 2, SCREEN_H // 2 + 30))
    surface.blit(small, rect2)


def draw_pause(surface: pygame.Surface, font: pygame.font.Font) -> None:
    overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 150))
    surface.blit(overlay, (0, 0))

    big = pygame.font.SysFont("monospace", 48, bold=True)
    txt = big.render("PAUSED", True, WHITE)
    rect = txt.get_rect(center=(COLS * CELL // 2, SCREEN_H // 2))
    surface.blit(txt, rect)


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
    font = pygame.font.SysFont("monospace", 22, bold=True)

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
        draw_sidebar(screen, game.score, game.level, game.lines, game.next, font)

        if game.game_over:
            draw_game_over(screen, font)
        elif game.paused:
            draw_pause(screen, font)

        pygame.display.flip()


if __name__ == "__main__":
    main()
