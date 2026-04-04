import socket
import threading
import json
import random
import time
import os

# Grab the word files from the data folder
WORDS_FILE = os.path.join(os.path.dirname(__file__), '../data/words.txt')
VALID_FILE = os.path.join(os.path.dirname(__file__), '../data/valid.txt')
# Set up game constants and player identities
HOST = '127.0.0.1'
PORT = 5050
MAX_GUESSES = 6
guesses_made = 0
guess_history = []
SYMBOLS = ["▲", "■", "●", "★"]
COLORS = ["#FF5555", "#55FF55", "#5555FF", "#FFFF55"]
available_identities = [{"symbol": s, "color": c} for s in SYMBOLS for c in COLORS]
random.shuffle(available_identities)
BACKUP_WORDS = ["CRANE", "TRAIN", "BRAIN", "PLANE", "PLANT", "SHARK", "SMART", "SMILE", "SWORD", "TABLE"]
player_identities = {}
players = []
# Set up locks for thread safety
clients_lock = threading.Lock()
game_lock = threading.Lock()

# Open words files and load them into TARGET_WORDS and VALID_WORDS
try:
    with open(WORDS_FILE, 'r') as f:
        TARGET_WORDS = [line.strip().upper() for line in f if len(line.strip()) == 5]
    if not TARGET_WORDS:
        print("No words loaded from file, using backup words")
        TARGET_WORDS = BACKUP_WORDS
except Exception as e:
    print(f"Could not load {WORDS_FILE}: {e}")
    TARGET_WORDS = BACKUP_WORDS

try:
    with open(VALID_FILE, 'r') as f:
        VALID_WORDS = {line.strip().upper() for line in f if len(line.strip()) == 5}
except Exception as e:
    print(f"Could not load {VALID_FILE}: {e}")
    VALID_WORDS = set(TARGET_WORDS)

VALID_WORDS.update(TARGET_WORDS)
# Pick an initial word
current_word = random.choice(TARGET_WORDS)

# A function to broadcast a message to all connected users, while removing disconected users
def broadcast(msg_dict):
    data = json.dumps(msg_dict) + '\n'
    bdata = data.encode('utf-8')
    with clients_lock:
        to_remove = []
        for c in players:
            try:
                c.sendall(bdata)
            except Exception:
                to_remove.append(c)
        for c in to_remove:
            players.remove(c)

# A function to broadcast the current player list to all users
def broadcast_players():
    with clients_lock:
        players = list(player_identities.values())
    broadcast({"type": "PLAYERS_UPDATE", "players": players})

# A function to evaluate the player guesses, and return feedback in the form of "correct", "present", or "absent" for each letter position
def evaluate_guess(guess, target):
    feedback = ["absent"] * 5
    target_letters = list(target)
    
    for i in range(5):
        if guess[i] == target[i]:
            feedback[i] = "correct"
            target_letters[i] = None
            
    for i in range(5):
        if feedback[i] == "correct":
            continue

        if guess[i] in target_letters:
            feedback[i] = "present"
            target_letters[target_letters.index(guess[i])] = None
            
    return feedback

# A function to reset the game state after a round ends
def reset_round():
    # Set a delay so that players can see the outcome before it ends
    time.sleep(4)
    global current_word, guesses_made, guess_history
    with game_lock:
        current_word = random.choice(TARGET_WORDS)
        guesses_made = 0
        guess_history.clear()
    print(f"New round started. The word is {current_word}")
    broadcast({"type": "NEW_ROUND"})

# A function to handle the new player connections, assign them an identity, and send them the current game state
def process_connect(conn):
    with clients_lock:
        if not available_identities:
            conn.sendall((json.dumps({"type": "ERROR", "message": "Server full"}) + '\n').encode('utf-8'))
            return False
        identity = available_identities.pop()
        player_identities[conn] = identity
        
    conn.sendall((json.dumps({"type": "WELCOME", "identity": identity}) + '\n').encode('utf-8'))
    broadcast_players()
    with game_lock:
        for past_feedback in guess_history:
            conn.sendall((json.dumps(past_feedback) + '\n').encode('utf-8'))
    return True

# A function to process plaayer guesses, validate them, update the game state, and broadcast feedback to all players
def process_guess(conn, guess):
    guess = guess.upper()
    
    # If the guess isnt a valid word then send an error messageto the player
    if guess not in VALID_WORDS:
        error_msg = json.dumps({"type": "ERROR", "message": "Not in word list"}) + '\n'
        conn.sendall(error_msg.encode('utf-8'))
        return
        
    with game_lock:
        global guesses_made
        if guesses_made >= MAX_GUESSES:
            return
        
        # Evaluate the guess and send the result to be displayed for all players
        feedback = evaluate_guess(guess, current_word)
        feedback_payload = {"type": "FEEDBACK", "guess": guess, "feedback": feedback, "identity": player_identities.get(conn)}
        guess_history.append(feedback_payload)
        broadcast(feedback_payload)
        guesses_made += 1
        solved = all(f == "correct" for f in feedback)
        
        # Check for a win condition or a round over
        if solved or guesses_made >= MAX_GUESSES:
            broadcast({"type": "GAME_OVER", "answer": current_word})
            print(f"Round over. Solved: {solved}")
            threading.Thread(target=reset_round, daemon=True).start()

def handle_client(conn, addr):
    print(f"New user {addr} connected.")
    try:
        # Continuously receive data from the client
        while True:
            data = conn.recv(1024).decode('utf-8')
            if not data:
                break
                
            # Process each message
            for chunk in data.strip().split('\n'):
                if not chunk:
                    continue
                msg = json.loads(chunk)
                
                if msg["type"] == "CONNECT":
                    # If process_connect fails then end the connection
                    if not process_connect(conn):
                        return
                        
                elif msg["type"] == "GUESS":
                    process_guess(conn, msg["guess"])
          
    except Exception as e:
        print(f"Error occurred with {addr}: {e}")
    # When a client disconnects, free their identy and remove them from the player list, then update other players
    finally:
        identity_released = False
        # verify that the player actually had an identity first, then remove it
        with clients_lock:
            if conn in player_identities:
                identity = player_identities.pop(conn)
                available_identities.append(identity)
                identity_released = True
            if conn in players:
                players.remove(conn)
        conn.close()
        print(f"User {addr} disconnected.")
        # If successfully removed, then update other players
        if identity_released:
            broadcast_players()

# Main server loop to accept incoming connections and create threads for each client
def start_server():
    # Initialize an IPv4 (AF_INET) TCP (SOCK_STREAM) socket
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    server.bind((HOST, PORT))
    server.listen()
    print(f"Starting Groudle: Server is listening on {HOST}:{PORT}")
    print(f"The current word is {current_word}")
    
    try:
        while True:
            # Block and wait for client to connect, then start a new thread for them
            conn, addr = server.accept()
            with clients_lock:
                players.append(conn)
            threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()
    except KeyboardInterrupt:
        print("\nServer closing")
    finally:
        server.close()

if __name__ == "__main__":
    start_server()