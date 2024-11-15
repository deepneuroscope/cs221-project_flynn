import chess
from typing import Optional
from agent import Agent, MiniMaxAgent, RandomAgent
from collections import defaultdict
from graphics import ChessGraphics
from multiprocessing import Pool, cpu_count

class ChessGame():
    def __init__(self, player1: Optional[Agent] = None, player2: Optional[Agent] = None, useGraphics: bool = True):
        self.player1 = player1
        self.player2 = player2
        self.board = chess.Board()
        self.graphics = ChessGraphics(board=self.board) if (useGraphics or player1 is None or player2 is None) else None
        if (self.player1 is not None):
            self.player1.initialize(board=self.board)
        if (self.player2 is not None):
            self.player2.initialize(board=self.board)

    def run(self):
        status = True
        winner = None
        while (status):
            if (self.graphics is not None):
                self.graphics.draw_game()
            if self.board.turn == chess.WHITE:
                if (self.player1 is not None):
                    self.board.push(self.player1.get_move())
                else:
                    status = self.graphics.capture_human_interaction()
            else:
                if (self.player2 is not None):
                    self.board.push(self.player2.get_move())
                else:
                    status = self.graphics.capture_human_interaction()
        
            if self.board.outcome() != None:
                print(self.board.outcome())
                status = False
                print(self.board)
                winner = self.board.outcome().winner
        if (winner == None):
            return None
        if (chess.WHITE == winner):
            return self.player1.name() if (self.player1 is not None) else "white"
        else:
            return self.player2.name() if (self.player2 is not None) else "black"

# ChessGame(player2=MiniMaxAgent(depth=2)).run()

# Simulate a single game and return the winner
def simulate_game(_):
    return ChessGame(player1=RandomAgent(), player2=MiniMaxAgent(depth=2), useGraphics=False).run()

if __name__ == "__main__":
    numGames = 50
    numWorkers = cpu_count()  # Adjust this to the number of CPU cores you want to use

    # Use multiprocessing.Manager to handle shared state (optional, if needed)
    with Pool(processes=numWorkers) as pool:
        # Run games in parallel
        results = pool.map(simulate_game, range(numGames))

    # Aggregate results
    winnerMap = defaultdict(int)
    for winner in results:
        winnerMap[winner] += 1

    # Print the results
    for winner, count in winnerMap.items():
        print(f"{winner} won {count}/{numGames}")