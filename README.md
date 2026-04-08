# **CMPT 371 A3 Socket Programming `Cooperative Wordle Game (Groudle)`**

**Course:** CMPT 371 \- Data Communications & Networking  
**Instructor:** Mirza Zaeem Baig  
**Semester:** Spring 2026  
<span style="color: purple;">***RUBRIC NOTE: As per submission guidelines, only one group member will submit the link to this repository on Canvas.***

## **Group Members**

| Name | Student ID | Email |
| --- | --- | --- |
| Christopher Shannon | 301540245 | csa155@sfu.ca |
| Mark Danskin | 301604373 | mdd16@sfu.ca |

## **1\. Project Overview & Description**

This project is a cooperative multiplayer version of the popular Wordle game using Python's Socket API (TCP). It allows up to 16 players to all play the game simultaneously, making their own guesses for the same word, with identification symbols used to show which users made which guess. The server handles the game logic, the word lists, the guesses made so far, and win conditions. The client sends guesses to the server and receives immediate feedback both for its own guesses and other players connected to the server. The game will automatically reset after a short timeout when 6 guesses have been made, or the word was guessed correctly.

## **2\. System Limitations & Edge Cases**

As required by the project specifications, we have identified and handled (or defined) the following limitations and potential issues within our application scope:

* **Handling Multiple Clients Concurrently:** 
  * <span style="color: green;">*Solution:*</span> We utilized Python's threading module. Each connected client is assigned a dedicated listener thread. We use a thread lock (`game_lock`) to synchronize access to the global game state, ensuring that guesses from different clients are processed sequentially without race conditions.
  * <span style="color: red;">*Limitation:*</span> The lobby is capped at exactly 16 players. If a 17th player trys to join, the server sends an `ERROR` to them and closes the socket. But the original players can still play.
* **TCP Stream Buffering:** 
  * <span style="color: green;">*Solution:*</span> Since TCP could allow multiple JSON messages to be joined together if sent rapidly or delivered together. We appened a newline to all JSON payloads and splitting the buffer on both sides to process json objects one by one.
* **Input Validation & Verification:** 
  * <span style="color: red;">*Limitation / Solution:*</span> The client automatically caps inputs to 5 alphabetical characters. However, to prevent a bypass of this bu the user, the server validates every guess against the valid words list. So if a client submits a gibberish string, the server responds directly to the client with an `"ERROR"`.
  

## **3\. Video Demo**

<span style="color: purple;">***RUBRIC NOTE: Include a clickable link.***</span>  
Our 2-minute video demonstration covering connection establishment, data exchange, real-time gameplay, and process termination can be viewed below:  
[**▶️ Watch Project Demo on YouTube**](https://youtu.be/SHgyUUcdTqc)

## **4\. Prerequisites (Fresh Environment)**

To run this project, you need:

* **Python 3.10** or higher.  
* No external pip installations are required (uses standard socket, threading, json, sys libraries).  
* (Optional) VS Code or Terminal.

<span style="color: purple;">***RUBRIC NOTE: No external libraries are required. Therefore, a requirements.txt file is not strictly necessary for dependency installation, though one might be included for environment completeness.***</span>

## **4\. Step-by-Step Run Guide**

### **Step 1: Start the Server**

Open your terminal and navigate to the project folder, and then into the src folder. The server binds to 127.0.0.1 on port 5050\.  
```bash
python server.py  
# Console output: "[STARTING] Server is listening on 127.0.0.1:5050"
```

### **Step 2: Connect Player 1 (X)**

Open a **new** terminal window (keep the server running). Run the client script to start the first client.  
```bash
python client.py  
# The game window will now open
```

### **Step 3: Connect Player 2 (O)**

Open a **third** terminal window. Run the client script again to start the second client.  
```bash
python client.py  
# The game window will now open
```

### **Step 4: Gameplay**

1. One or more players join the game, and their player identity in the form of a colored symbol will be given to them.
2. Players can enter words as their guess, and guesses will be accepted by the server in the order they are sent, with player symbols highlighting who made what guess.
3. Invalid words will send clients a message telling them that the word is not in the word list.
4. When letters are correctly guessed, but the location is wrong, they will be yellow. If the location is correct then they will be green.
5. After a word is guessed correctly or if all 6 attempts are used up, the game will reset and can be played again.

## **5\. Technical Protocol Details (JSON over TCP)**

We designed a custom application-layer protocol for data exchange using JSON over TCP. Every message requires `\n` at the end as a boundary.

* **Message Format:** `{"type": <string>, ...other_properties}`  
* **Handshake Phase:**
  * Client sends: `{"type": "CONNECT"}`  
  * Server maps identity and responds: `{"type": "WELCOME", "identity": {"symbol": "▲", "color": "#FF5555"}}`  
  * Server sends a list of active players: `{"type": "PLAYERS_UPDATE", "players": [{"symbol": "▲", "color": "#FF5555"}]}`
  * Server sends current game word history: `{"type": "FEEDBACK", "guess": "CRANE", "feedback": [...], "identity": ...}`
* **Gameplay Phase:**  
  * Client sends guess to the server: `{"type": "GUESS", "guess": "APPLE"}`  
  * Server broadcasts outcome of the guess to all connected users: `{"type": "FEEDBACK", "guess": "APPLE", "feedback": ["correct", "absent", "present", "absent", "absent"], "identity": {"symbol": "▲", "color": "#FF5555"}}`
* **Control Actions:**  
  * Server rejects invalid guess directly: `{"type": "ERROR", "message": "Not in word list"}`
  * Server announces resolution: `{"type": "GAME_OVER", "answer": "SMART"}`
  * Server restarts the game: `{"type": "NEW_ROUND"}`


## **6\. Academic Integrity & References**

* **Code Origin:**  
  * The socket boilerplate was adapted from the course tutorial "TCP Echo Server". The core multithreaded game logic, protocol, and state management were written by the group.
  * client.py side code  started out as the tic tac toe game before being modified.
  * The existing `README.md` template was modified with our projects details instead of writing a `README.md` from scratch
* **GenAI Usage:**  
  * Claude was used to generate the client side gui (anything using the tkinter)
  * Claude was used to explain error messages when they occurred during the process of creating the server logic.
  * Claude was used to help explain the server logic and commands, and how to use locks properly in this application.
  * Github Copilot (Gemini) was used to help explaining sections 2 and 5 of the `README.md` succinctly.
* **References:**  
  * [Wordle game words downloaded from here](https://gist.github.com/cfreshman/a03ef2cba789d8cf00c08f767e0fad7b)
  * [Valid words for wordle downloaded from here](https://gist.github.com/dracos/dd0668f281e685bad51479e5acaadb93)

