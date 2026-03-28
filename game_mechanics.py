"""
Game mechanics for the mystery game.
Handles suspect data, guilt status, and verdict checking.
"""

import random
import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# Bio lab job titles
BIO_LAB_JOBS = [
    "Microbiologist",
    "Lab Technician",
    "Biochemist",
    "Research Assistant",
    "Quality Control Analyst",
    "Sample Analyst",
    "Molecular Biologist",
    "Senior Lab Technician",
    "Bioinformatician",
    "Sterile Area Technician",
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
            model="llama-3.3-70b-versatile",
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
    """Initialize 5 suspects with random job titles, AI-generated alibis, and guilt status."""
    # Randomly select one guilty suspect
    guilty_index = random.randint(1, 5)
    
    job_titles = random.sample(BIO_LAB_JOBS, 5)
    
    # Initialize AI client for alibi generation
    ai_client = get_ai_client()
    
    # Generate alibis using AI
    alibis = [generate_alibi_with_ai(ai_client) for _ in range(5)]
    
    for i in range(1, 6):
        suspect_id = f"S{i}"
        SUSPECTS[suspect_id] = {
            "name": f"Suspect {i}",
            "job_title": job_titles[i - 1],
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
        guilty_suspect = next(s for s in SUSPECTS.values() if s["guilty"])
        return False, f"❌ Oh no, you lost!\n{suspect['name']} is innocent.\nThe actual culprit was a different suspect."


def get_all_suspects_info():
    """Get info about all suspects (for debugging/setup)."""
    return SUSPECTS


if __name__ == "__main__":
    # Test the system
    initialize_suspects()
    print("Suspects initialized:")
    for sid, info in SUSPECTS.items():
        status = "GUILTY" if info["guilty"] else "innocent"
        print(f"{sid}: {info['name']} - {info['job_title']} - Alibi: {info['alibi']} ({status})")
    
    print("\nTesting verdicts:")
    for suspect_id in ["S1", "S2", "S3", "S4", "S5"]:
        is_correct, message = check_verdict(suspect_id)
        print(f"\n{suspect_id}: {message}")

print("\nAll suspect info (for debugging):")
for sid, info in SUSPECTS.items():
    print(f"{sid}: {info['name']} - {info['job_title']} - {info['alibi']} ({'GUILTY' if info['guilty'] else 'innocent'})")