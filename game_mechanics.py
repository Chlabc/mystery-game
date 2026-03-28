"""
Game mechanics for the mystery game.
Handles suspect data, guilt status, and verdict checking.
"""

import random

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

# Create suspects
SUSPECTS = {}

def initialize_suspects():
    """Initialize 5 suspects with random job titles and guilt status."""
    # Randomly select one guilty suspect
    guilty_index = random.randint(1, 5)
    
    job_titles = random.sample(BIO_LAB_JOBS, 5)
    
    for i in range(1, 6):
        suspect_id = f"S{i}"
        SUSPECTS[suspect_id] = {
            "name": f"Suspect {i}",
            "job_title": job_titles[i - 1],
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
        print(f"{sid}: {info['name']} - {info['job_title']} ({status})")
    
    print("\nTesting verdicts:")
    for suspect_id in ["S1", "S2", "S3", "S4", "S5"]:
        is_correct, message = check_verdict(suspect_id)
        print(f"\n{suspect_id}: {message}")
