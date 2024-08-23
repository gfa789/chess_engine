import pygame
import sys
import os
from abc import ABC, abstractmethod
from collections import Counter

# Initialize Pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 480, 500
BOARD_SIZE = 480
DIMENSION = 8
SQ_SIZE = BOARD_SIZE // DIMENSION

# Colors
LIGHT_SQUARE = (240, 217, 181)  # Light brown
DARK_SQUARE = (181, 136, 99)    # Dark brown
HIGHLIGHT = (247, 247, 105)     # Light yellow for highlighting
MOVE_INDICATOR = (186, 202, 68)  # Green for valid move indicators
CHECK_INDICATOR = (255, 0, 0)   # Red for check indicator
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

class Piece(ABC):
    def __init__(self, color, position):
        self.color = color
        self.position = position
        self.image = None
        self.rect = None
        self.load_image()

    @abstractmethod
    def get_valid_moves(self, board):
        pass

    def load_image(self):
        piece_name = self.__class__.__name__.lower()
        filename = f"{self.color}-{piece_name}.png"
        path = os.path.join("pieces", filename)
        self.image = pygame.image.load(path)
        self.image = pygame.transform.scale(self.image, (SQ_SIZE, SQ_SIZE))
        self.rect = self.image.get_rect()
        self.update_rect()

    def update_rect(self):
        self.rect.topleft = (self.position[1] * SQ_SIZE, self.position[0] * SQ_SIZE)

class Pawn(Piece):
    def __init__(self, color, position):
        super().__init__(color, position)
        self.has_moved = False
        self.en_passant_vulnerable = False

    def get_valid_moves(self, board):
        row, col = self.position
        moves = []
        direction = -1 if self.color == 'white' else 1
        
        # Move forward
        if 0 <= row + direction < 8 and board[row + direction][col] is None:
            moves.append((row + direction, col))
            # Double move from starting position
            if not self.has_moved and board[row + 2*direction][col] is None:
                moves.append((row + 2*direction, col))
        
        # Capture diagonally
        for dcol in [-1, 1]:
            if 0 <= row + direction < 8 and 0 <= col + dcol < 8:
                if board[row + direction][col + dcol] is not None:
                    if board[row + direction][col + dcol].color != self.color:
                        moves.append((row + direction, col + dcol))
                
                # En passant
                elif (row == 3 and self.color == 'white') or (row == 4 and self.color == 'black'):
                    if isinstance(board[row][col + dcol], Pawn) and board[row][col + dcol].en_passant_vulnerable:
                        moves.append((row + direction, col + dcol))
        
        return moves

class Rook(Piece):
    def get_valid_moves(self, board):
        return self._get_straight_moves(board)

    def _get_straight_moves(self, board):
        moves = []
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        for dr, dc in directions:
            for i in range(1, 8):
                row, col = self.position[0] + i*dr, self.position[1] + i*dc
                if 0 <= row < 8 and 0 <= col < 8:
                    if board[row][col] is None:
                        moves.append((row, col))
                    elif board[row][col].color != self.color:
                        moves.append((row, col))
                        break
                    else:
                        break
                else:
                    break
        return moves

class Knight(Piece):
    def get_valid_moves(self, board):
        moves = []
        knight_moves = [(-2, -1), (-2, 1), (-1, -2), (-1, 2),
                        (1, -2), (1, 2), (2, -1), (2, 1)]
        for dr, dc in knight_moves:
            row, col = self.position[0] + dr, self.position[1] + dc
            if 0 <= row < 8 and 0 <= col < 8:
                if board[row][col] is None or board[row][col].color != self.color:
                    moves.append((row, col))
        return moves

class Bishop(Piece):
    def get_valid_moves(self, board):
        return self._get_diagonal_moves(board)

    def _get_diagonal_moves(self, board):
        moves = []
        directions = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
        for dr, dc in directions:
            for i in range(1, 8):
                row, col = self.position[0] + i*dr, self.position[1] + i*dc
                if 0 <= row < 8 and 0 <= col < 8:
                    if board[row][col] is None:
                        moves.append((row, col))
                    elif board[row][col].color != self.color:
                        moves.append((row, col))
                        break
                    else:
                        break
                else:
                    break
        return moves

class Queen(Piece):
    def get_valid_moves(self, board):
        return self._get_straight_moves(board) + self._get_diagonal_moves(board)

    def _get_straight_moves(self, board):
        return Rook(self.color, self.position)._get_straight_moves(board)

    def _get_diagonal_moves(self, board):
        return Bishop(self.color, self.position)._get_diagonal_moves(board)

class King(Piece):
    def get_valid_moves(self, board):
        moves = []
        king_moves = [(0, 1), (1, 0), (0, -1), (-1, 0),
                      (1, 1), (1, -1), (-1, 1), (-1, -1)]
        for dr, dc in king_moves:
            row, col = self.position[0] + dr, self.position[1] + dc
            if 0 <= row < 8 and 0 <= col < 8:
                if board[row][col] is None or board[row][col].color != self.color:
                    moves.append((row, col))
        return moves

class ChessGame:
    def __init__(self, player_color='white'):
        self.board = [[None for _ in range(8)] for _ in range(8)]
        self._initialize_pieces()
        self.turn = 'white'
        self.selected_piece = None
        self.dragging = False
        self.valid_moves = []
        self.player_color = player_color
        self.board_flipped = player_color == 'black'
        self.in_check = {'white': False, 'black': False}
        self.game_over = False
        self.game_result = None
        self.position_history = []
        self.last_move = None
        self.promotion_pawn = None

    def _initialize_pieces(self):
        # Initialize pawns
        for col in range(8):
            self.board[1][col] = Pawn('black', (1, col))
            self.board[6][col] = Pawn('white', (6, col))

        # Initialize other pieces
        piece_order = [Rook, Knight, Bishop, Queen, King, Bishop, Knight, Rook]
        for col, piece_class in enumerate(piece_order):
            self.board[0][col] = piece_class('black', (0, col))
            self.board[7][col] = piece_class('white', (7, col))

    def draw_board(self, screen):
        for row in range(DIMENSION):
            for col in range(DIMENSION):
                color = LIGHT_SQUARE if (row + col) % 2 != 0 else DARK_SQUARE
                if self.board_flipped:
                    pygame.draw.rect(screen, color, ((7-col) * SQ_SIZE, (7-row) * SQ_SIZE, SQ_SIZE, SQ_SIZE))
                else:
                    pygame.draw.rect(screen, color, (col * SQ_SIZE, row * SQ_SIZE, SQ_SIZE, SQ_SIZE))
                
                piece = self.board[row][col]
                if piece:
                    screen_pos = self.get_screen_position((row, col))
                    screen.blit(piece.image, screen_pos)
                    
                    # Highlight king if in check
                    if isinstance(piece, King) and self.in_check[piece.color]:
                        pygame.draw.rect(screen, CHECK_INDICATOR, (*screen_pos, SQ_SIZE, SQ_SIZE), 3)

        # Draw valid move indicators
        for move in self.valid_moves:
            screen_pos = self.get_screen_position(move)
            pygame.draw.circle(screen, MOVE_INDICATOR, 
                               (screen_pos[0] + SQ_SIZE // 2, screen_pos[1] + SQ_SIZE // 2), 
                               SQ_SIZE // 8)

        # Draw the selected piece last (on top)
        if self.selected_piece and self.dragging:
            screen.blit(self.selected_piece.image, self.selected_piece.rect)

    def get_screen_position(self, board_position):
        row, col = board_position
        if self.board_flipped:
            return ((7-col) * SQ_SIZE, (7-row) * SQ_SIZE)
        else:
            return (col * SQ_SIZE, row * SQ_SIZE)

    def get_board_position(self, screen_position):
        x, y = screen_position
        if self.board_flipped:
            return (7 - (y // SQ_SIZE), 7 - (x // SQ_SIZE))
        else:
            return (y // SQ_SIZE, x // SQ_SIZE)

    def select_piece(self, pos):
        if pos[1] >= BOARD_SIZE:  # Check if click is below the board
            return
        row, col = self.get_board_position(pos)
        piece = self.board[row][col]
        if piece and piece.color == self.turn:
            self.selected_piece = piece
            self.valid_moves = self.get_legal_moves(piece)
            self.dragging = True
            # Update the rect of the selected piece for dragging
            self.selected_piece.rect.center = pos
        else:
            self.selected_piece = None
            self.valid_moves = []

    def move_piece(self, end_pos):
        if end_pos[1] >= BOARD_SIZE:  # Check if release is below the board
            return False
        end_row, end_col = self.get_board_position(end_pos)
        start_row, start_col = self.selected_piece.position

        if (end_row, end_col) in self.valid_moves:
            # Handle en passant capture
            if isinstance(self.selected_piece, Pawn) and end_col != start_col and self.board[end_row][end_col] is None:
                self.board[start_row][end_col] = None  # Remove the captured pawn

            # Make the move
            self.board[end_row][end_col] = self.selected_piece
            self.board[start_row][start_col] = None
            self.selected_piece.position = (end_row, end_col)
            self.selected_piece.update_rect()

            # Handle pawn promotion
            if isinstance(self.selected_piece, Pawn) and (end_row == 0 or end_row == 7):
                self.promotion_pawn = self.selected_piece
                return True

            # Update pawn status
            if isinstance(self.selected_piece, Pawn):
                self.selected_piece.has_moved = True
                # Set en passant vulnerability
                if abs(start_row - end_row) == 2:
                    self.selected_piece.en_passant_vulnerable = True
                else:
                    self.selected_piece.en_passant_vulnerable = False

            # Reset en passant vulnerability for all other pawns of the same color
            for row in self.board:
                for piece in row:
                    if isinstance(piece, Pawn) and piece.color == self.selected_piece.color and piece != self.selected_piece:
                        piece.en_passant_vulnerable = False

            # Update game state
            self.last_move = (start_row, start_col, end_row, end_col)
            self.turn = 'black' if self.turn == 'white' else 'white'
            self.update_check_status()
            self.update_game_over()
            self.update_position_history()

            return True
        else:
            # If the move is not valid, return the piece to its original position
            self.selected_piece.update_rect()
            return False

    def promote_pawn(self, piece_class):
        row, col = self.promotion_pawn.position
        color = self.promotion_pawn.color
        self.board[row][col] = piece_class(color, (row, col))
        self.promotion_pawn = None

        # Update game state after promotion
        self.update_check_status()
        self.update_game_over()
        self.update_position_history()

    def resign(self):
        self.game_over = True
        self.game_result = f"{'Black' if self.turn == 'white' else 'White'} wins by resignation!"

    def get_legal_moves(self, piece):
        potential_moves = piece.get_valid_moves(self.board)
        legal_moves = []
        for move in potential_moves:
            if not self.move_causes_check(piece, move):
                legal_moves.append(move)
        return legal_moves

    def move_causes_check(self, piece, move):
        # Create a deep copy of the board
        temp_board = [row[:] for row in self.board]
        start_row, start_col = piece.position
        end_row, end_col = move

        # Make the move on the temporary board
        temp_board[end_row][end_col] = piece
        temp_board[start_row][start_col] = None

        # Check if the king is in check after the move
        king_position = self.find_king(piece.color, temp_board)
        return self.is_square_under_attack(king_position, piece.color, temp_board)

    def find_king(self, color, board):
        for row in range(8):
            for col in range(8):
                if isinstance(board[row][col], King) and board[row][col].color == color:
                    return (row, col)
        return None  # This should never happen in a valid chess game
    

    def is_square_under_attack(self, square, color, board):
        for row in range(8):
            for col in range(8):
                piece = board[row][col]
                if piece and piece.color != color:
                    if square in piece.get_valid_moves(board):
                        return True
        return False

    def update_check_status(self):
        self.in_check['white'] = self.is_in_check('white')
        self.in_check['black'] = self.is_in_check('black')

    def is_in_check(self, color):
        king_position = self.find_king(color, self.board)
        return self.is_square_under_attack(king_position, color, self.board)

    def update_game_over(self):
        if self.is_checkmate(self.turn):
            self.game_over = True
            self.game_result = f"{'Black' if self.turn == 'white' else 'White'} wins by checkmate!"
        elif self.is_stalemate(self.turn):
            self.game_over = True
            self.game_result = "Draw by stalemate!"
        elif self.is_draw_by_repetition():
            self.game_over = True
            self.game_result = "Draw by repetition!"

    def is_checkmate(self, color):
        if not self.in_check[color]:
            return False
        return self.has_no_legal_moves(color)

    def is_stalemate(self, color):
        if self.in_check[color]:
            return False
        return self.has_no_legal_moves(color)

    def has_no_legal_moves(self, color):
        for row in range(8):
            for col in range(8):
                piece = self.board[row][col]
                if piece and piece.color == color:
                    if self.get_legal_moves(piece):
                        return False
        return True

    def update_position_history(self):
        position = self.get_current_position()
        self.position_history.append(position)

    def get_current_position(self):
        return tuple(tuple(row) for row in self.board)

    def is_draw_by_repetition(self):
        if len(self.position_history) < 8:  # Need at least 8 moves for a 3-fold repetition
            return False
        position_counts = Counter(self.position_history)
        return any(count >= 3 for count in position_counts.values())

    def handle_click(self, pos):
        if not self.game_over:
            if not self.selected_piece:
                self.select_piece(pos)
            else:
                if self.move_piece(pos):
                    self.selected_piece = None
                    self.valid_moves = []
                else:
                    self.select_piece(pos)

    def handle_drag(self, pos):
        if self.selected_piece and self.dragging and not self.game_over:
            self.selected_piece.rect.center = pos

    def handle_release(self, pos):
        if self.selected_piece and self.dragging and not self.game_over:
            self.move_piece(pos)
            self.selected_piece = None
            self.valid_moves = []
            self.dragging = False

    def flip_board(self):
        self.board_flipped = not self.board_flipped


def draw_button(screen, text, position, size):
    font = pygame.font.Font(None, 30)
    text_render = font.render(text, True, BLACK)
    button_rect = pygame.Rect(position, size)
    pygame.draw.rect(screen, WHITE, button_rect)
    pygame.draw.rect(screen, BLACK, button_rect, 2)
    text_rect = text_render.get_rect(center=button_rect.center)
    screen.blit(text_render, text_rect)
    return button_rect

def main():
    screen = pygame.display.set_mode((WIDTH, HEIGHT + 50))  # Extra height for buttons
    pygame.display.set_caption("Chess Game")
    clock = pygame.time.Clock()
    
    def show_start_screen():
        while True:
            screen.fill(WHITE)
            title_font = pygame.font.Font(None, 50)
            title_text = title_font.render("Chess Game", True, BLACK)
            screen.blit(title_text, (WIDTH//2 - title_text.get_width()//2, 50))
            
            white_button = draw_button(screen, "Play as White", (WIDTH//4 - 75, HEIGHT//2), (150, 50))
            black_button = draw_button(screen, "Play as Black", (3*WIDTH//4 - 75, HEIGHT//2), (150, 50))
            
            pygame.display.flip()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if white_button.collidepoint(event.pos):
                        return 'white'
                    elif black_button.collidepoint(event.pos):
                        return 'black'

    player_color = show_start_screen()
    game = ChessGame(player_color)

    while True:
        flip_button = draw_button(screen, "Flip Board", (10, HEIGHT + 10), (120, 30))
        resign_button = draw_button(screen, "Resign", (140, HEIGHT + 10), (120, 30))
        restart_button = draw_button(screen, "Restart", (270, HEIGHT + 10), (120, 30))

        promotion_buttons = None

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if flip_button.collidepoint(event.pos):
                    game.flip_board()
                elif resign_button.collidepoint(event.pos):
                    game.resign()
                elif restart_button.collidepoint(event.pos):
                    player_color = show_start_screen()
                    game = ChessGame(player_color)
                elif promotion_buttons:
                    for piece, button in promotion_buttons.items():
                        if button.collidepoint(event.pos):
                            game.promote_pawn(piece)
                            promotion_buttons = None
                            break
                else:
                    game.handle_click(event.pos)
            elif event.type == pygame.MOUSEMOTION:
                game.handle_drag(event.pos)
            elif event.type == pygame.MOUSEBUTTONUP:
                game.handle_release(event.pos)

        screen.fill(LIGHT_SQUARE)
        game.draw_board(screen)
        flip_button = draw_button(screen, "Flip Board", (10, HEIGHT + 10), (120, 30))
        resign_button = draw_button(screen, "Resign", (140, HEIGHT + 10), (120, 30))
        restart_button = draw_button(screen, "Restart", (270, HEIGHT + 10), (120, 30))

        if game.promotion_pawn:
            promotion_pieces = [Queen, Rook, Bishop, Knight]
            promotion_buttons = {}
            for i, piece in enumerate(promotion_pieces):
                button = draw_button(screen, piece.__name__, (i * (WIDTH//4) + WIDTH//8 - 40, HEIGHT//2 - 25), (80, 50))
                promotion_buttons[piece] = button

        if game.game_over:
            font = pygame.font.Font(None, 36)
            text = font.render(game.game_result, True, BLACK)
            text_rect = text.get_rect(center=(WIDTH//2, HEIGHT + 25))
            screen.blit(text, text_rect)

        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main()