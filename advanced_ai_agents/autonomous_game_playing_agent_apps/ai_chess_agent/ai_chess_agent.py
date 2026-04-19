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
        max_tokens=300,
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
        board_svg = chess.svg.board(
            st.session_state.board,
            size=450,
            lastmove=(
                st.session_state.board.peek()
                if st.session_state.board.move_stack
                else None
            ),
        )
        st.image(board_svg.encode(), use_container_width=False)

    with col2:
        st.subheader("Game Controls")

        if st.button("🔄 New Game", use_container_width=True):
            initialize_game()
            st.rerun()

        st.info(st.session_state.status_message)

        # Human move input
        if not st.session_state.game_over and st.session_state.board.turn == chess.WHITE:
            move_input = st.text_input(
                "Your move (UCI format, e.g. e2e4):",
                key="move_input",
                placeholder="e2e4",
            )

            if st.button("Make Move", use_container_width=True):
                try:
                    move = chess.Move.from_uci(move_input.strip())
                    if move in st.session_state.board.legal_moves:
                        st.session_state.board.push(move)
                        st.session_state.move_history.append(
                            f"You: {move_input.strip()}"
                        )

                        if st.session_state.board.is_game_over():
                            st.session_state.game_over = True
                            st.session_state.status_message = "Game over! You won!"
                        else:
                            # AI's turn
                            with st.spinner("AI is thinking..."):
                                ai_move, reasoning = get_ai_move(
                                    st.session_state.board, chess.BLACK
                                )
                            ai_chess_move = chess.Move.from_uci(ai_move)
                            st.session_state.board.push(ai_chess_move)
                            st.session_state.move_history.append(f"AI: {ai_move}")
                            st.session_state.status_message = (
                                f"AI played {ai_move}: {reasoning}"
                            )

                            if st.session_state.board.is_game_over():
                                st.session_state.game_over = True
                                st.session_state.status_message = "Game over! AI won!"
                        st.rerun()
                    else:
                        st.error("Illegal move! Try again.")
                except Exception as e:
                    st.error(f"Invalid move format: {e}")

        st.subheader("Move History")
        if st.session_state.move_history:
            for i, move in enumerate(reversed(st.session_state.move_history[-10:])):
                st.text(move)
        else:
            st.text("No moves yet")


if __name__ == "__main__":
    main()
