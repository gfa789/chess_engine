import numpy as np
from chess_game import ChessGame, Piece, Pawn, Rook, Knight, Bishop, Queen, King
import pygame  

pieces = {
    'rook': Rook, 
    'knight': Knight, 
    'bishop': Bishop, 
    'queen': Queen, 
    'king' : King,
    'pawn': Pawn,
}

class ChessAI:
    def __init__(self):
        self.q_table = {}  # This will store the Q-values for state-action pairs
        self.learning_rate = 0.1
        self.discount_factor = 0.9
        self.exploration_rate = 0.1

    def get_state_representation(self, game):
        state = []
        for row in range(8):
            for col in range(8):
                piece = game.board[row][col]
                if piece is None:
                    continue
                else:
                    # Use lowercase for black pieces, uppercase for white pieces
                    state.append(piece)
        # Add current turn to the state

        # Convert list to tuple so it's hashable
        return tuple(state)

    def get_possible_actions(self, game: ChessGame):
        # TODO: Implement a function to get all possible moves in the current game state
        # This should return a list of (start_pos, end_pos) tuples for all legal moves
        state = self.get_state_representation(game)
        results = []
        for p in state:
            for move in p.get_valid_moves(game.board):
                results.append((p.position, move))
        return results

    def choose_action(self, game, state):
        if np.random.random() < self.exploration_rate:
            # Explore: choose a random action
            actions = self.get_possible_actions(game)
            rand = np.random.randint(0, len(actions))
            print(actions[rand])
            return actions[rand]
        else:
            # Exploit: choose the best action based on Q-values
            # TODO: Implement logic to select the action with the highest Q-value
            pass

    def update_q_value(self, state, action, next_state, reward):
        # TODO: Implement the Q-learning update rule
        # Q(s,a) = Q(s,a) + learning_rate * (reward + discount_factor * max(Q(s',a')) - Q(s,a))
        pass

    def get_reward(self, game):
        # TODO: Implement a reward function
        # This could be based on material advantage, board control, or game outcome
        pass

def train_ai(num_episodes):
    ai = ChessAI()

    for episode in range(num_episodes):
        game = ChessGame()
        state = ai.get_state_representation(game)

        while not game.game_over:
            action = ai.choose_action(game, state)
            # TODO: Apply the chosen action to the game
            
            next_state = ai.get_state_representation(game)
            reward = ai.get_reward(game)

            ai.update_q_value(state, action, next_state, reward)

            state = next_state

        print(f"Episode {episode + 1}/{num_episodes} completed")

    return ai

def play_against_ai(ai):
    
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT + 50))
    pygame.display.set_caption("Chess: Human vs AI")
    clock = pygame.time.Clock()

    game = ChessGame('white')  # Human player is always white for simplicity
    selected_piece = None
    drag_pos = None

    while not game.game_over:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return

            if game.turn == 'white':  # Human player's turn
                if event.type == pygame.MOUSEBUTTONDOWN:
                    x, y = event.pos
                    if y < BOARD_SIZE:  # Click is on the board
                        col, row = x // SQ_SIZE, y // SQ_SIZE
                        piece = game.board[row][col]
                        if piece and piece.color == 'white':
                            selected_piece = piece
                            drag_pos = (x, y)

                elif event.type == pygame.MOUSEMOTION:
                    if selected_piece:
                        drag_pos = event.pos

                elif event.type == pygame.MOUSEBUTTONUP:
                    if selected_piece:
                        x, y = event.pos
                        if y < BOARD_SIZE:  # Release is on the board
                            end_col, end_row = x // SQ_SIZE, y // SQ_SIZE
                            start_row, start_col = selected_piece.position
                            move = ((start_row, start_col), (end_row, end_col))
                            if move in game.get_valid_moves(selected_piece):
                                game.move_piece(selected_piece, (end_row, end_col))
                        selected_piece = None
                        drag_pos = None

        if game.turn == 'black' and not game.game_over:  # AI's turn
            state = ai.get_state_representation(game)
            action = ai.choose_action(game, state)
            start_pos, end_pos = action
            piece = game.board[start_pos[0]][start_pos[1]]
            game.move_piece(piece, end_pos)

        # Draw the game state
        screen.fill(LIGHT_SQUARE)
        game.draw_board(screen)

        # Draw dragged piece
        if selected_piece and drag_pos:
            x, y = drag_pos
            screen.blit(selected_piece.image, (x - SQ_SIZE // 2, y - SQ_SIZE // 2))

        # Draw game over message if applicable
        if game.game_over:
            font = pygame.font.Font(None, 36)
            text = font.render(game.game_result, True, BLACK)
            text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT + 25))
            screen.blit(text, text_rect)

        pygame.display.flip()
        clock.tick(60)

    # Game over, wait for user to close the window
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return

if __name__ == "__main__":
    trained_ai = train_ai(num_episodes=1000)
    play_against_ai(trained_ai)