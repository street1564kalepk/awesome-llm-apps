"""AI Chess Agent using LLM to play chess against a human opponent.

This agent uses Claude/OpenAI to analyze chess positions and make moves,
providing explanations for its strategic decisions.
"""

import os
import chess
import chess.svg
import streamlit as st
from anthropic import Anthropic

# Initialize Anthropic client
client = Anthropic()

SYSTEM_PROMPT = """You are an expert chess player with deep knowledge of chess strategy, 
openings, tactics, and endgames. You are playing as {color} pieces.

When given a chess position in FEN notation, analyze it and:
1. Choose the best legal move in UCI format (e.g., e2e4, g1f3)
2. Explain your reasoning briefly

Respond ONLY in this format:
MOVE: <uci_move>
REASONING: <brief explanation>"""


def get_ai_move(board: chess.Board, ai_color: chess.Color) -> tuple[str, str]:
    """Get the AI's next move using Claude."""
    color_name = "White" if ai_color == chess.WHITE else "Black"
    legal_moves = [move.uci() for move in board.legal_moves]

    prompt = f"""Current position (FEN): {board.fen()}

Legal moves available: {', '.join(legal_moves)}

Choose your best move and explain your reasoning."""

    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=500,  # increased from 300 to give the AI more room to explain its reasoning
        system=SYSTEM_PROMPT.format(color=color_name),
        messages=[{"role": "user", "content": prompt}],
    )

    response_text = response.content[0].text
    lines = response_text.strip().split("\n")

    move_uci = ""
    reasoning = ""
    for line in lines:
        if line.startswith("MOVE:"):
            move_uci = line.replace("MOVE:", "").strip()
        elif line.startswith("REASONING:"):
            # Capture all remaining lines as reasoning, not just the first line
            reasoning = line.replace("REASONING:", "").strip()

    # Validate the move
    try:
        move = chess.Move.from_uci(move_uci)
        if move not in board.legal_moves:
            # Fall back to first legal move if AI gives invalid move
            move = list(board.legal_moves)[0]
            move_uci = move.uci()
            reasoning = "Fallback move (AI suggested illegal move)"
    except Exception:
        move = list(board.legal_moves)[0]
        move_uci = move.uci()
        reasoning = "Fallback move (parsing error)"

    return move_uci, reasoning


def initialize_game():
    """Initialize a new chess game in session state."""
    st.session_state.board = chess.Board()
    st.session_state.move_history = []
    st.session_state.game_over = False
    st.session_state.status_message = "Game started! You play as White."


def main():
    st.set_page_config(page_title="AI Chess Agent", page_icon="♟️", layout="wide")
    st.title("♟️ AI Chess Agent")
    st.caption("Play chess against Claude AI")

    # Initialize game state
    if "board" not in st.session_state:
        initialize_game()

    col1, col2 = st.columns([2, 1])

    with col1:
        # Display chess board as SVG
        # Use size=450 for a slightly larger board that fits better on most screens
        board_svg = chess.svg.board(
           
