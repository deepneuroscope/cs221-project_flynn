import chess
from copy import deepcopy
from typing import Optional
from agent import Agent, MiniMaxAgent, RandomAgent, MinimaxAgentWithPieceSquareTables
from collections import defaultdict
from graphics import ChessGraphics
from multiprocessing import Pool, cpu_count
import random
from typing import List, Tuple
from util import read_positions
from tqdm import tqdm

class ChessGame():
    def __init__(self, player1: Optional[Agent] = None, player2: Optional[Agent] = None, useGraphics: bool = True, startingFen: Optional[str] = None):
        self.player1 = player1
        self.player2 = player2
        self.board = chess.Board()
        if (startingFen):
            self.board.set_fen(startingFen)
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
                # print(self.board.outcome())
                status = False
                # print(self.board)
                winner = self.board.outcome().winner
        if (winner == None):
            return None
        if (chess.WHITE == winner):
            return self.player1.name() if (self.player1 is not None) else "white"
        else:
            return self.player2.name() if (self.player2 is not None) else "black"

# Simulate a single game and return the winner
def simulate_game(data):
    opening,fen,player1,player2 = data
    result = ChessGame(
        player1=player1,
        player2=player2,
        useGraphics=False,
        startingFen=fen).run()
    return (opening, result, player1)

def aggregate(positions: List[Tuple[str, str]]):
    opening_map = defaultdict(lambda: list())
    for opening, fen in positions:
        opening_map[opening].append(fen)
    return opening_map

if __name__ == "__main__":
    num_games = 256
    num_chunks = 4
    assert num_games % num_chunks == 0
    num_games //= num_chunks
    numWorkers = cpu_count()  # Adjust this to the number of CPU cores you want to use
    print(numWorkers)
    
    agent1 = RandomAgent("RandAgent1")
    agent2 = RandomAgent("RandAgent2")
    # agent1 = MinimaxAgentWithPieceSquareTables("psquaretables", depth=2)
    # agent2 = MiniMaxAgent("mma", depth=2)
    
    chunks = random.sample(range(1, 21), num_chunks)
    positions_to_play = []
    for chunk in chunks:
        positions = read_positions(f"positions/unprocessed/chunk_{chunk}.txt")
        opening_map = aggregate(positions)
        unique_opening_positions = []
        for opening in opening_map:
            fen = random.choice(opening_map[opening])
            unique_opening_positions.append((opening, fen, agent1, agent2))

        # changed this so that each opening is played twice, once with each agent as white
        player1_as_white = random.sample(unique_opening_positions, num_games)
        player2_as_white = deepcopy(player1_as_white)
        for i in range(num_games):
            player2_as_white[i] = (player2_as_white[i][0], player2_as_white[i][1], player2_as_white[i][3], player2_as_white[i][2])
        
        positions_to_play.extend(player1_as_white)
        positions_to_play.extend(player2_as_white)

    # Run games in parallel with a progress bar and running tally
    total_games = len(positions_to_play)
    games_played = 0
    winnerMap = defaultdict(lambda : {"WHITE": 0, "BLACK": 0})

    with Pool(processes=numWorkers) as pool:
        with tqdm(total=total_games, desc=f"Simulating {total_games} games") as pbar:
            for opening, winner, player1 in pool.imap_unordered(simulate_game, positions_to_play):
                # Update running tally
                games_played += 1

                if winner == player1.name():
                    winnerMap[winner]["WHITE"] += 1    
                elif winner is not None:
                    winnerMap[winner]["BLACK"] += 1
                if winner is None:
                    if player1.name() == agent1.name():
                        winnerMap[None]["WHITE"] += 1
                    else:
                        winnerMap[None]["BLACK"] += 1

                # Display running tally in tqdm's description
                a1_wins_w = winnerMap[agent1.name()]["WHITE"]
                a1_losses_w = winnerMap[agent2.name()]["WHITE"]
                a1_ties_w = winnerMap[None]["WHITE"]
                a1_wins_b = winnerMap[agent1.name()]["BLACK"]
                a1_losses_b = winnerMap[agent2.name()]["BLACK"]
                a1_ties_b = winnerMap[None]["BLACK"]
                
                pbar.set_postfix_str(f"Agent 1 as white: {a1_wins_w}-{a1_losses_w}-{a1_ties_w}, Agent 1 as black: {a1_wins_b}-{a1_losses_b}-{a1_ties_b}")
                pbar.update(1)

    # Final results
    for winner, count in winnerMap.items():
        if winner is None:
            print(f"Agents tied {count}/{total_games}")
        else:
            print(f"{winner} won {count}/{total_games}")
