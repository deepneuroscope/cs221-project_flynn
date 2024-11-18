import chess
from functools import cmp_to_key
import random
from typing import Callable, Dict, List

from piece_square_tables import piece_square_table_score, piece_square_table_move_score
from pawn_shield_storm import eval_pawn_storm

piece_indices = {
    'p': 0, # Black pawn
    'n': 1, # Black knight
    'b': 2, # Black bishop
    'r': 3, # Black rook
    'q': 4, # Black queen
    'k': 5,  # Black king
    'P': 6,  # White pawn
    'N': 7,  # White knight
    'B': 8,  # White bishop
    'R': 9,  # White rook
    'Q': 10,  # White queen
    'K': 11,  # White king
}

index_pieces = ['p', 'n', 'b', 'r', 'q', 'k', 'P', 'N', 'B', 'R', 'Q', 'K']

scoring= {
    'p': -1, # Black pawn
    'n': -3, # Black knight
    'b': -3, # Black bishop (should be slightly more valuable than knight ideally for better evaluation)
    'r': -5, # Black rook
    'q': -9, # Black queen
    'k': 0,  # Black king
    'P': 1,  # White pawn
    'N': 3,  # White knight
    'B': 3,  # White bishop (should be slightly more valuable than knight ideally for better evaluation)  
    'R': 5,  # White rook
    'Q': 9,  # White queen
    'K': 0,  # White king
}

def eval_piece_count(piece_count):
    score = 0
    for i in range(len(piece_count)):
        score += piece_count[i] * scoring[index_pieces[i]]
    return score

def get_piece_index(piece: chess.Piece):
    return piece_indices[piece.symbol()]

def get_captured_piece(board: chess.Board, move: chess.Move):
    captured_piece = board.piece_at(move.to_square)
    if (captured_piece is not None):
        return captured_piece.symbol()
    
    #en passant
    idx = 0
    if (move.from_square > move.to_square): # black captures white piece
        if (move.from_square - 7 == move.to_square): # piece is to the right
            idx = move.from_square + 1
        else: # piece is to the left
            idx = move.from_square - 1
    else: # white captures black piece
        if (move.from_square + 7 == move.to_square): # piece is to the left
            idx = move.from_square - 1
        else: # piece is to the right
            idx = move.from_square + 1
    return str(board.piece_at(idx))

def dotProduct(d1: Dict, d2: Dict) -> float:
    """
    The dot product of two vectors represented as dictionaries. This function
    goes over all the keys in d2, and for each key, multiplies the corresponding
    values in d1 and d2 and adds the result to a running sum. If the key is not
    in d1, it is treated as having value 0.

    @param dict d1: a feature vector represented by a mapping from a feature (string) to a weight (float).
    @param dict d2: same as d1
    @return float: the dot product between d1 and d2
    """
    if len(d1) < len(d2):
        return dotProduct(d2, d1)
    else:
        return sum(d1.get(f, 0) * v for f, v in list(d2.items()))

# initialize and return a piece count dictionary
def initialize_piece_count(board: chess.Board) -> List[int]:
    piece_count = [0 for _ in range(12)]
    for piece in board.piece_map().values():
        piece_count[get_piece_index(piece)] += 1
    return piece_count

million = 1000000
winning_capture_bias = 8 * million
promote_bias = 6 * million
killer_bias = 4 * million
losing_capture_bias = 2 * million
regular_bias = 0


def can_move_to_square(board, square):
    # Ensure square is within the valid range (0-63)
    if not (0 <= square < 64):
        raise ValueError("Invalid square number. Must be between 0 and 63.")

    target_square = chess.square(square % 8, square // 8)  # Convert to square representation
    
    # Get the player's color (we'll check for the current player)
    color = board.turn

    valid_squares = []
    # Loop through all pieces on the board
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece is not None and piece.color == color:
            valid_squares.append(square)

    # Check if the piece can legally move to the target square
    pieces_that_can_move_to_square = []
    for move in board.legal_moves:
        if move.from_square in valid_squares and move.to_square == target_square:
            pieces_that_can_move_to_square.append(board.piece_at(move.from_square).symbol())

    return pieces_that_can_move_to_square

def score_move(board: chess.Board, piece_count: List[int], move: chess.Move):
    score = 0

    move_piece = board.piece_at(move.from_square)
    captured_piece = None

    # make move
    if (board.is_capture(move)):
        captured_piece = get_captured_piece(board, move)
        piece_count[piece_indices[captured_piece]] -= 1
    board.push(move)

    pieces_that_can_move_to_square = can_move_to_square(board, move.to_square)
    if (len(pieces_that_can_move_to_square) > 0):
        score -= 25

    if ("P" in pieces_that_can_move_to_square or "p" in pieces_that_can_move_to_square):
        score -= 25
    
    # undo move
    board.pop()
    if captured_piece is not None:
        piece_count[piece_indices[captured_piece]] += 1

    if (board.is_capture(move)):
        capture_point_differential = scoring[captured_piece] - scoring[move_piece.symbol()]
        opponentCanRecapture = len(pieces_that_can_move_to_square) > 0
        score += capture_point_differential
        if (not opponentCanRecapture):
            score += winning_capture_bias
        elif(capture_point_differential >= 0):
            score += winning_capture_bias
        else:
            score += losing_capture_bias
            
    elif (move_piece.symbol() == 'p' or move_piece.symbol() == 'P'): # pawn promotion
        if (move.to_square):
            score += promote_bias
    # else:
        # todo implement killer move
        # bool isKiller = !inQSearch && ply < maxKillerMovePly && killerMoves[ply].Match(move);
        # score += isKiller ? killer_bias : regular_bias;
        # score += History[board.MoveColourIndex, move.StartSquare, move.TargetSquare];

    score += piece_square_table_move_score(board, piece_count, move)

    return score

class Agent():
    def __init__(self):
        self.piece_count = None
        self.board = None
    
    def initialize(self, board: chess.Board):
        self.piece_count = initialize_piece_count(board)
        self.board = board

    def name(self) -> str:
        raise Exception("Not yet implemented")

    def get_move(self):
        raise Exception("Not yet implemented")
    
class RandomAgent(Agent):

    def name(self) -> str:
        return "random_agent"

    def get_move(self):
        return random.choice(list(self.board.legal_moves))

class MiniMaxAgent(Agent):
    def __init__(self, depth: int):
        super().__init__()
        self.depth = depth
        self.weights =  {
            "piece_count": 1.0,
            "pawn_storm": 0,
            "piece_square": 0,
        }

    def featureExtractor(self, piece_count: List[int], board: chess.Board):
        return {
            "piece_count": eval_piece_count(self.piece_count),
            "pawn_storm": eval_pawn_storm(board) if self.weights["pawn_storm"] > 0.0 else 0,
            "piece_square": piece_square_table_score(board, piece_count) if self.weights["piece_square"] > 0.0 else 0
        }

    # simple evaluation function
    def eval_board(self, board: chess.Board, piece_count: List[int]):
        return dotProduct(self.featureExtractor(piece_count, board), self.weights)

    def min_maxN(
            self,
            board: chess.Board,
            piece_count: List[int],
            depth: int,
            eval_fn: Callable[[chess.Board, List[int]], float],
            alpha: float,
            beta: float):
        if (board.is_stalemate() or board.is_insufficient_material()):
            return (0, None)
        if (board.is_checkmate()):
            score = float('inf') if (board.outcome().winner == chess.WHITE) else float('-inf')
            return (score, None)
        if (depth == 0):
            return (eval_fn(board, piece_count), None)
        
        moves = list(board.legal_moves)
        scores = []

        for move in moves:
            # if the move is a capture, decrement the count of the captured piece
            captured_piece = None
            if board.is_capture(move):
                captured_piece = get_captured_piece(board, move)
                piece_count[piece_indices[captured_piece]] -= 1

            board.push(move)

            # recursive call delegating to the other player
            score, _ = self.min_maxN(
                board=board,
                piece_count=piece_count,
                depth=depth - 1,
                eval_fn=eval_fn,
                alpha=alpha,
                beta=beta)

            # reset board and piece count
            if captured_piece is not None:
                piece_count[piece_indices[captured_piece]] += 1
            board.pop()

            if (board.turn == chess.WHITE): # max
                if (score >= beta): #prune
                    return (score, move)
                if (score > alpha):
                    alpha = score
            else: #min
                if (score <= alpha): #prune
                    return (score, move)
                if (score < beta):
                    beta = score
            scores.append(score)

        bestScore = max(scores) if board.turn == chess.WHITE else min(scores)
        return (bestScore, moves[scores.index(bestScore)])

    def name(self) -> str:
        return "minimax_agent"

    def get_move(self):
        _, move = self.min_maxN(
            board=self.board,
            piece_count=self.piece_count,
            depth=self.depth*2,
            eval_fn=self.eval_board,
            alpha=float('-inf'),
            beta=float('inf'))
        return move

class MinimaxAgentWithPieceSquareTables(MiniMaxAgent):
    def __init__(self, depth: int):
        super().__init__(depth)
        self.weights["piece_square"] = 1

    def name(self) -> str:
        return super().name() + "_with_piece_square_tables"

class OptimizedMiniMaxAgent(MiniMaxAgent):

    def __init__(self, depth: int):
        super().__init__(depth)
        self.max_extensions = 16
        self.search_cancelled = False
    
    def cancel_search(self):
        self.search_cancelled = True

    def min_maxN(
            self,
            board: chess.Board,
            piece_count: List[int],
            depth: int,
            eval_fn: Callable[[chess.Board, List[int]], float],
            score_fn: Callable[[chess.Board, List[int], chess.Move], float],
            alpha: float,
            beta: float,
            extensions: int):
        if (board.is_stalemate() or board.is_insufficient_material()):
            return (0, None)
        if (board.is_checkmate()):
            score = float('inf') if (board.outcome().winner == chess.WHITE) else float('-inf')
            return (score, None)
        if (depth == 0):
            evaluation, _ = self.quiescence_search(
                board=board,
                piece_count=piece_count,
                eval_fn=eval_fn,
                score_fn=score_fn,
                alpha=alpha,
                beta=beta)
            return (evaluation, None)
        
        moves = list(board.legal_moves)
        scores = []

        for move in moves:
            # if the move is a capture, decrement the count of the captured piece
            captured_piece = None
            if board.is_capture(move):
                captured_piece = get_captured_piece(board, move)
                piece_count[piece_indices[captured_piece]] -= 1

            board.push(move)

            # extend the search if the the opposing king is in check
            extension = 1 if (extensions < self.max_extensions and board.is_check()) else 0
            # recursive call delegating to the other player
            score, _ = self.min_maxN(
                board=board,
                piece_count=piece_count,
                depth=(depth - 1 + extension),
                eval_fn=eval_fn,
                score_fn=score_fn,
                alpha=alpha,
                beta=beta,
                extensions=extensions + 1)

            # reset board and piece count
            if captured_piece is not None:
                piece_count[piece_indices[captured_piece]] += 1
            board.pop()

            if (board.turn == chess.WHITE): # max
                if (score >= beta): #prune
                    return (score, move)
                if (score > alpha):
                    alpha = score
            else: #min
                if (score <= alpha): #prune
                    return (score, move)
                if (score < beta):
                    beta = score
            scores.append(score)

        bestScore = max(scores) if board.turn == chess.WHITE else min(scores)
        return (bestScore, moves[scores.index(bestScore)])

    # Search capture moves until a 'quiet' position is reached.
    def quiescence_search(
            self,
            board: chess.Board,
            piece_count: List[int],
            eval_fn: Callable[[chess.Board, List[int]], float],
            score_fn: Callable[[chess.Board, List[int], chess.Move], float],
            alpha: float,
            beta: float):
        if (self.search_cancelled):
            return 0
        
        evaluation = eval_fn(board, piece_count)
        if (evaluation >= beta):
            return (evaluation, None)
        if (evaluation > alpha):
            alpha = evaluation

        capture_moves = [move for move in board.legal_moves if board.is_capture(move)]
        sorted(capture_moves, key=cmp_to_key(lambda item1, item2: score_fn(board, piece_count, item1) - score_fn(board, piece_count, item2)))
        bestMove = None
        for move in capture_moves:
            captured_piece = get_captured_piece(board, move)
            piece_count[piece_indices[captured_piece]] -= 1

            board.push(move)

            evaluation, _ = self.quiescence_search(
                board=board,
                piece_count=piece_count,
                eval_fn=eval_fn,
                score_fn=score_fn,
                alpha= 0-beta,
                beta= 0-alpha)
            evaluation = 0-evaluation

            # reset board and piece count
            if captured_piece is not None:
                piece_count[piece_indices[captured_piece]] += 1
            board.pop()

            if (evaluation >= beta):
                return (evaluation, move)
            if (evaluation > alpha):
                alpha = evaluation
                bestMove = move

        return (alpha, bestMove)
    
    def name(self) -> str:
        return "optimized_minimax_agent"

    def get_move(self):
        _, move = self.min_maxN(
            board=self.board,
            piece_count=self.piece_count,
            depth=self.depth*2,
            eval_fn=self.eval_board,
            score_fn=score_move,
            alpha=float('-inf'),
            beta=float('inf'),
            extensions=0)
        return move
