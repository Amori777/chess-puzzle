# ---------------------------------------------------------
# Project: Chess Puzzle
# Made by: 3mr | 3mrLogic
# ---------------------------------------------------------

from flask import Flask, render_template, jsonify, request
import chess
import random
import base64

app = Flask(__name__)

def generate_mate_in_one():
    found = False
    while not found:
        # Start with a clean slate (blank board)
        board = chess.Board(None)
        
        # Coin toss to see who's playing today: White or Black
        board.turn = random.choice([chess.WHITE, chess.BLACK])
        
        # Dropping the kings in random spots. Rule #1: Don't forget the kings.
        board.set_piece_at(random.choice(list(chess.SQUARES)), chess.Piece(chess.KING, chess.WHITE))
        board.set_piece_at(random.choice(list(chess.SQUARES)), chess.Piece(chess.KING, chess.BLACK))
        
        # Chaos mode: adding some random firepower (pieces) to make it look like a real game
        for _ in range(random.randint(8, 14)):
            sq = random.choice(list(chess.SQUARES))
            if not board.piece_at(sq):
                # Choosing between N, B, R, Q and picking a side
                board.set_piece_at(sq, chess.Piece(random.choice([2,3,4,5]), random.choice([True, False])))
        
        # Making sure the board isn't broken or already in check
        if board.is_valid() and not board.is_check():
            actual_mates = []
            
            # Hunting for that one winning move
            for m in board.legal_moves:
                board.push(m)
                if board.is_checkmate(): 
                    actual_mates.append(m.uci())
                board.pop() # Back to reality
            
            # We only care about puzzles with a single unique solution
            if len(actual_mates) == 1:
                return board.fen(), actual_mates[0]

@app.route('/')
def index():
    # Just serve the main page and let the frontend do its magic
    return render_template('index.html')

@app.route('/generate')
def generate():
    # Fresh puzzle coming up! Also encoding it to base64 so it's easy to share via URL
    fen, move = generate_mate_in_one()
    serial = base64.b64encode(fen.encode()).decode()
    return jsonify({'fen': fen, 'serial': serial, 'move': move})

@app.route('/load')
def load():
    # Grab the puzzle ID from the URL params
    serial = request.args.get('serial')
    if not serial:
        return jsonify({'error': 'No serial provided'}), 400
    try:
        # Quick fix: sometimes URLs swap '+' with spaces, which breaks base64
        serial = serial.strip().replace(' ', '+')
        
        # Adding back the '=' padding if it's missing, just to keep the decoder happy
        padding = len(serial) % 4
        if padding:
            serial += '=' * (4 - padding)
            
        # Turning that weird string back into a playable chess board
        fen = base64.b64decode(serial.encode()).decode()
        board = chess.Board(fen)
        
        # Re-check the solution just in case
        actual_mates = []
        for m in board.legal_moves:
             board.push(m)
             if board.is_checkmate(): 
                 actual_mates.append(m.uci())
             board.pop()
             
        return jsonify({
            'fen': fen, 
            'serial': request.args.get('serial'), 
            'move': actual_mates[0] if actual_mates else None,
            'credits': 'Made by 3mr | 3mrLogic'
        })
    except Exception as e:
        # Log it so I can debug this mess later
        print(f"Error loading serial: {e}")
        return jsonify({'error': f'Invalid Serial: {str(e)}'}), 400

if __name__ == '__main__':
    # Run the app. Debug=True is a lifesaver during dev.
    app.run(debug=True)