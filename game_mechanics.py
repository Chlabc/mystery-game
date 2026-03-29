"""
Game mechanics for the mystery game.
Handles suspect data, guilt status, verdict checking,
and AI-powered suspect interrogation conversations.
"""

import random
import os
import re
import threading
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# ── AI model to use across all Groq calls ──────────────────────────────────
GROQ_MODEL = "llama-3.3-70b-versatile"

# Fixed suspect roster — names and roles match the cutscene intro cards.
# Each entry: (name, job_title, personality_note)
_SUSPECT_ROSTER = [
    ("Dr. Evelyn Kallen",  "Microbiologist",          "under immense funding pressure, argumentative with management"),
    ("Dr. Marcus Reed",    "Bioinformatician",         "secretive by nature, was spotted near the containment area"),
    ("Dr. Lucia Chen",     "Senior Lab Technician",    "dedicated but lately erratic and visibly stressed"),
    ("Dr. Samuel Ortiz",   "Quality Control Analyst",  "under investigation for falsified data, history of colleague conflicts"),
    ("Dr. Penelope Grant", "Sterile Area Technician",  "meticulous worker but distracted by unresolved personal issues"),
]

# Initialize Groq AI client for alibi generation
def get_ai_client():
    """Create and return a Groq AI client."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("Warning: GROQ_API_KEY not found. Alibis will be generic.")
        return None
    return Groq(api_key=api_key)

def generate_alibi_with_ai(ai_client):
    """Generate a unique alibi using Groq AI."""
    if not ai_client:
        return f"Was at their workstation on {random.choice(['DNA analysis', 'protein research', 'microbial testing', 'equipment maintenance'])}"
    
    try:
        alibi_prompt = """You are an alibi generator for a mystery game set in a biolab during a biohazard breach.
Generate ONE SHORT, REALISTIC alibi (1-2 sentences) for a lab worker who claims they were doing something specific when the breach occurred.
The alibi should be plausible but leave room for investigation.

Examples: "I was collecting samples in the storage room", "I was on a call with a client in the east wing", "I was doing quality control checks on bioreactors"

Generate only the alibi text, nothing else."""
        
        response = ai_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": "You are a creative alibi generator. Keep responses concise and realistic."},
                {"role": "user", "content": alibi_prompt},
            ],
            max_tokens=100,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"AI Error: {e}. Using fallback alibi.")
        return f"Was at their workstation on {random.choice(['DNA analysis', 'protein research', 'microbial testing', 'equipment maintenance'])}"

# Create suspects
SUSPECTS = {}

def initialize_suspects():
    """Initialize the 5 named suspects with AI-generated alibis and randomised guilt."""
    # Pick one suspect at random to be the culprit each game
    guilty_index = random.randint(1, 5)

    # Initialize AI client for alibi generation
    ai_client = get_ai_client()

    # Generate one alibi per suspect using AI
    alibis = [generate_alibi_with_ai(ai_client) for _ in range(5)]

    for i, (name, job_title, _personality) in enumerate(_SUSPECT_ROSTER, start=1):
        suspect_id = f"S{i}"
        SUSPECTS[suspect_id] = {
            "name": name,
            "job_title": job_title,
            "alibi": alibis[i - 1],
            "guilty": (i == guilty_index),
        }

    return guilty_index


def get_suspect_info(suspect_id):
    """Get information about a suspect."""
    if suspect_id in SUSPECTS:
        return SUSPECTS[suspect_id]
    return None


def check_verdict(suspect_id):
    """
    Check if the player's verdict is correct.
    Returns: (is_correct, message)
    """
    suspect = get_suspect_info(suspect_id)

    if suspect is None:
        return False, f"Invalid suspect: {suspect_id}. Choose S1, S2, S3, S4, or S5."

    if suspect["guilty"]:
        return True, f"🎉 Congratulations! You found the guilty party!\n{suspect['name']} ({suspect['job_title']}) was indeed the culprit!"
    else:
        return False, f"❌ Oh no, you lost!\n{suspect['name']} is innocent.\nThe actual culprit was a different suspect."


def get_all_suspects_info():
    """Get info about all suspects (for debugging/setup)."""
    return SUSPECTS


# ── System prompt template for suspect interrogation ───────────────────────
# {name}, {job_title}, {personality}, {alibi}, and {guilt_instructions} are filled in
# per suspect so each character feels distinct.
SUSPECT_SYSTEM_PROMPT = """You are a character in a mystery-detective game.
You are being interrogated by a detective about a biohazard breach at the biolab where you work.

Your character:
- Name: {name}
- Job: {job_title}
- Known for: {personality}
- Your alibi: "{alibi}"
{guilt_instructions}

RULES:
- Stay in character at ALL times. Respond as this specific lab worker.
- Keep responses to 2-4 sentences. Be conversational and human.
- Let your known personality traits colour how you speak and react.
- You are stressed and defensive — being interrogated is uncomfortable, even if you're innocent.
- Refer to your alibi naturally; don't just robotically quote it.
- Do NOT break character or acknowledge that this is a game.
- Do NOT use any status tags or brackets in your response.
"""

# Guilt instructions shape subtly different behaviour based on innocence/guilt.
GUILTY_INSTRUCTIONS = """- You are GUILTY. You caused the breach and are hiding it.
- Defend yourself, but show subtle signs of nervousness when pressed on details.
- Your alibi has small inconsistencies — if the detective probes carefully you may slip up.
- Never directly confess, but don't lie perfectly either. Hesitate, deflect, change the subject.
- Let your personal backstory leak through under pressure."""

INNOCENT_INSTRUCTIONS = """- You are INNOCENT. You had nothing to do with the breach.
- Be cooperative but anxious — you want to clear your name.
- Your alibi is solid and consistent. You can recall details clearly.
- Show frustration or hurt feelings if accused too aggressively.
- Your personality and backstory make you a believable but innocent suspect."""


class SuspectInterrogation:
    """
    Manages an AI-powered interrogation conversation between the detective
    (player) and a single suspect. Keeps its own conversation history so
    the suspect remembers everything said earlier in the session.

    Usage:
        session = SuspectInterrogation("S1")
        response = session.ask("Where were you when the breach happened?")
        print(response)
    """

    def __init__(self, suspect_id: str):
        """
        Set up a new interrogation session for a given suspect.
        The conversation history starts fresh each time.
        """
        suspect = get_suspect_info(suspect_id)
        if suspect is None:
            raise ValueError(f"Unknown suspect: {suspect_id}")

        self.suspect_id = suspect_id
        self.suspect = suspect

        # Pick the right guilt instructions
        guilt_block = GUILTY_INSTRUCTIONS if suspect["guilty"] else INNOCENT_INSTRUCTIONS

        # Build the system prompt for this specific suspect.
        # _SUSPECT_ROSTER index is (suspect_id number - 1), e.g. S1 → index 0.
        roster_index = int(suspect_id[1]) - 1
        _name, _job, personality = _SUSPECT_ROSTER[roster_index]

        system_prompt = SUSPECT_SYSTEM_PROMPT.format(
            name=suspect["name"],
            job_title=suspect["job_title"],
            personality=personality,
            alibi=suspect["alibi"],
            guilt_instructions=guilt_block,
        )

        # conversation_history holds the full context sent to the AI each turn
        self.conversation_history = [
            {"role": "system", "content": system_prompt}
        ]

        # Set up the Groq client
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise EnvironmentError("GROQ_API_KEY is not set.")
        self._client = Groq(api_key=api_key)

    def ask(self, detective_message: str) -> str:
        """
        Send the detective's question/statement to the suspect and get
        the suspect's reply. Blocks until the API responds.

        Args:
            detective_message: What the player typed.

        Returns:
            The suspect's response as a plain string.
        """
        self.conversation_history.append(
            {"role": "user", "content": detective_message}
        )

        try:
            response = self._client.chat.completions.create(
                model=GROQ_MODEL,
                messages=self.conversation_history,
                max_tokens=200,
                temperature=0.75,
            )
            reply = response.choices[0].message.content.strip()
        except Exception as e:
            reply = f"I... I don't know what to say right now. ({e})"

        # Save the reply so the AI remembers it next turn
        self.conversation_history.append(
            {"role": "assistant", "content": reply}
        )

        return reply

    def ask_async(self, detective_message: str, callback):
        """
        Non-blocking version of ask(). Calls callback(suspect_id, reply) on a
        background thread — safe to use inside a pygame loop.
        """
        def _run():
            reply = self.ask(detective_message)
            callback(self.suspect_id, reply)

        threading.Thread(target=_run, daemon=True).start()

    def get_opening_statement(self) -> str:
        """
        Generate the suspect's first line when the detective sits down,
        before the player has asked anything.
        """
        opener_prompt = (
            "(The detective has just entered the interrogation room and sat down "
            "across from you. Greet them and briefly state how you feel about being here.)"
        )
        # Sent as a one-off; not added to permanent history as a user message
        temp_history = self.conversation_history + [
            {"role": "user", "content": opener_prompt}
        ]
        try:
            response = self._client.chat.completions.create(
                model=GROQ_MODEL,
                messages=temp_history,
                max_tokens=150,
                temperature=0.75,
            )
            reply = response.choices[0].message.content.strip()
        except Exception as e:
            reply = f"I wasn't expecting this. ({e})"

        # Save it so follow-up questions have context
        self.conversation_history.append(
            {"role": "assistant", "content": reply}
        )
        return reply

    def get_opening_statement_async(self, callback):
        """Non-blocking version of get_opening_statement(). Calls callback(suspect_id, reply)."""
        def _run():
            reply = self.get_opening_statement()
            callback(self.suspect_id, reply)

        threading.Thread(target=_run, daemon=True).start()

    @property
    def name(self) -> str:
        """Convenience access to the suspect's display name."""
        return self.suspect["name"]


# ── Multi-suspect routing ───────────────────────────────────────────────────

# Regex that matches @S1 … @S5 anywhere in the player's message
_AT_PATTERN = re.compile(r"@(S[1-5])", re.IGNORECASE)


class InterrogationRoom:
    """
    Holds one persistent SuspectInterrogation session per suspect and
    routes the detective's messages based on @mentions.

    Two modes
    ---------
    Targeted  — message contains @S1, @S2, @S3, @S4, or @S5
                Only the named suspect(s) reply.
                Multiple tags (e.g. "@S1 @S3 ...") are supported.

    Broadcast — no @tag in the message
                All five suspects reply (responses arrive in parallel
                via the async methods).

    Usage (blocking / terminal)
    ---------------------------
        room = InterrogationRoom()
        results = room.dispatch("Where were you?")
        for sid, reply in results:
            print(sid, ":", reply)

    Usage (non-blocking / pygame)
    ------------------------------
        room.dispatch_async(player_input, callback=on_reply)
        # on_reply(suspect_id, reply_text) is called once per responding suspect
    """

    ALL_IDS = ["S1", "S2", "S3", "S4", "S5"]

    def __init__(self):
        # One persistent session per suspect — history is kept across questions
        self.sessions: dict[str, SuspectInterrogation] = {
            sid: SuspectInterrogation(sid) for sid in self.ALL_IDS
        }

    # ── helpers ──────────────────────────────────────────────────────────────

    def _targets(self, message: str) -> list[str]:
        """
        Return the list of suspect IDs to question.
        If the message has @mentions → only those suspects.
        Otherwise → all suspects.
        """
        mentioned = [m.upper() for m in _AT_PATTERN.findall(message)]
        # Deduplicate while preserving order
        seen = set()
        unique = [m for m in mentioned if not (m in seen or seen.add(m))]
        return unique if unique else self.ALL_IDS

    def _strip_tags(self, message: str) -> str:
        """Remove @S1-style tags from the message before sending to the AI."""
        return _AT_PATTERN.sub("", message).strip()

    # ── blocking API (good for terminals / simple scripts) ───────────────────

    def dispatch(self, message: str) -> list[tuple[str, str]]:
        """
        Route a detective message and collect replies.

        Returns a list of (suspect_id, reply) tuples, one per responding
        suspect, in the order S1 → S5.
        Runs all API calls in parallel threads and waits for all to finish.
        """
        targets = self._targets(message)
        clean_msg = self._strip_tags(message)

        results: dict[str, str] = {}
        lock = threading.Lock()
        done_event = threading.Event()
        remaining = [len(targets)]  # mutable counter

        def on_reply(sid, reply):
            with lock:
                results[sid] = reply
                remaining[0] -= 1
                if remaining[0] == 0:
                    done_event.set()

        for sid in targets:
            self.sessions[sid].ask_async(clean_msg, on_reply)

        done_event.wait()  # block until every targeted suspect has replied

        # Return in S1..S5 order, only the ones we queried
        return [(sid, results[sid]) for sid in self.ALL_IDS if sid in results]

    def broadcast(self, message: str) -> list[tuple[str, str]]:
        """Convenience: always question ALL suspects, regardless of @tags."""
        clean_msg = self._strip_tags(message)
        return self.dispatch(clean_msg)  # no @tags → auto-broadcasts

    # ── non-blocking API (good for pygame loops) ─────────────────────────────

    def dispatch_async(self, message: str, callback):
        """
        Non-blocking version of dispatch().
        callback(suspect_id, reply) is called once for each suspect who replies,
        on a background thread — safe to use from a pygame event handler.
        """
        targets = self._targets(message)
        clean_msg = self._strip_tags(message)

        for sid in targets:
            self.sessions[sid].ask_async(clean_msg, callback)

    def broadcast_async(self, message: str, callback):
        """Always question all suspects asynchronously."""
        clean_msg = self._strip_tags(message)
        for sid in self.ALL_IDS:
            self.sessions[sid].ask_async(clean_msg, callback)

    # ── opening statements ───────────────────────────────────────────────────

    def open_all(self) -> list[tuple[str, str]]:
        """
        Get every suspect's opening statement (blocking, parallel).
        Returns [(sid, statement), ...] in order.
        """
        results: dict[str, str] = {}
        lock = threading.Lock()
        done_event = threading.Event()
        remaining = [len(self.ALL_IDS)]

        def on_open(sid, reply):
            with lock:
                results[sid] = reply
                remaining[0] -= 1
                if remaining[0] == 0:
                    done_event.set()

        for session in self.sessions.values():
            session.get_opening_statement_async(on_open)

        done_event.wait()
        return [(sid, results[sid]) for sid in self.ALL_IDS]

    def open_all_async(self, callback):
        """
        Kick off opening statements for all suspects non-blocking.
        callback(suspect_id, statement) fires once per suspect.
        """
        for session in self.sessions.values():
            session.get_opening_statement_async(callback)


# ── Terminal demo ───────────────────────────────────────────────────────────

def run_terminal_interrogation():
    """
    Interactive terminal session that demonstrates both modes.

    Type normally to ask all suspects at once (broadcast).
    Use @S1, @S2, etc. to target specific suspects.
    Type 'quit' or 'exit' to end.
    """
    print("\n" + "=" * 62)
    print("  LAB BREAKOUT — Interrogation Room")
    print("=" * 62)
    print("  Ask all suspects:        just type your question")
    print("  Target a suspect:        @S1 why did you leave early?")
    print("  Target multiple:         @S2 @S4 where were you exactly?")
    print("  End session:             quit / exit")
    print("=" * 62 + "\n")

    room = InterrogationRoom()

    print("[Collecting opening statements from all suspects…]\n")
    openings = room.open_all()
    for sid, stmt in openings:
        name = room.sessions[sid].name
        print(f"  {sid} — {name}: {stmt}\n")

    print("-" * 62)

    while True:
        try:
            raw = input("Detective: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n[Interrogation ended.]")
            break

        if not raw:
            continue
        if raw.lower() in ("quit", "exit"):
            print("[You leave the interrogation room.]")
            break

        # Show who we're asking
        targets = room._targets(raw)
        if len(targets) == len(InterrogationRoom.ALL_IDS):
            print(f"  [Asking all suspects]\n")
        else:
            names = ", ".join(
                f"{sid} ({room.sessions[sid].name})" for sid in targets
            )
            print(f"  [Asking: {names}]\n")

        results = room.dispatch(raw)
        for sid, reply in results:
            name = room.sessions[sid].name
            print(f"  {sid} — {name}: {reply}\n")
        print("-" * 62)


if __name__ == "__main__":
    # Initialize suspects first, then start the interrogation demo
    initialize_suspects()
    print("Suspects initialized:")
    for sid, info in SUSPECTS.items():
        status = "GUILTY" if info["guilty"] else "innocent"
        print(f"  {sid}: {info['name']} — {info['job_title']} ({status})")
        print(f"       Alibi: {info['alibi']}")
    print()

    run_terminal_interrogation()