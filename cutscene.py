"""
Cutscene system for displaying sequential story scenes with typewriter text effect.

Features:
- Loads images (cutscene1.png - cutscene5.png)
- Types text letter-by-letter at configurable speed
- Pauses 5 seconds between scenes
- Shows "Next" button on final scene
"""

import pygame
import sys
from game_mechanics import initialize_suspects, check_verdict

# --- Initialization ---
pygame.init()

# --- Configuration ---
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GOLD = (212, 175, 55)
TEXTBOX_ALPHA = 200

# Typewriter settings
CHARS_PER_SECOND = 60  # Adjust this to control typing speed (higher = faster)
PAUSE_BETWEEN_SCENES = 5000  # milliseconds (5 seconds)

# Scene data: (image_file, text_content)
SCENES = [
    ("image1.jpg", "Wikipedia is hosted by the Wikimedia Foundation, a non-profit organization that also hosts a range of other projects. You can support our work with a donation."),
    ("image2.jpg", "sampletext2"),
    ("image3.jpg", "sampletext3"),
    ("image4.jpg", "sampletext4"),
    ("image5.jpg", "sampletext5"),
]

# --- Setup Display ---
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Cutscene")
clock = pygame.time.Clock()

# --- Fonts ---
font_text = pygame.font.SysFont("georgia", 24)
font_button = pygame.font.SysFont("arial", 20, bold=True)


def load_image(filename):
    """Load an image and scale it to screen size. Return fallback if not found."""
    try:
        img = pygame.image.load(filename)
        img = pygame.transform.scale(img, (SCREEN_WIDTH, SCREEN_HEIGHT))
        return img
    except pygame.error:
        print(f"Warning: Could not load {filename}. Using fallback color.")
        fallback = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        fallback.fill((30, 30, 30))
        return fallback


def draw_textbox_with_text(text, alpha=TEXTBOX_ALPHA):
    """
    Draw a textbox in the bottom third with word-wrapped text.
    Text is vertically centered in the box.
    """
    textbox_height = SCREEN_HEIGHT // 3
    textbox_rect = pygame.Rect(20, SCREEN_HEIGHT - textbox_height - 20, SCREEN_WIDTH - 40, textbox_height - 20)
    
    # Draw semi-transparent background
    textbox_surf = pygame.Surface((textbox_rect.width, textbox_rect.height))
    textbox_surf.set_alpha(alpha)
    textbox_surf.fill(BLACK)
    screen.blit(textbox_surf, (textbox_rect.x, textbox_rect.y))
    
    # Draw border
    pygame.draw.rect(screen, GOLD, textbox_rect, 3)
    
    # Word-wrap by character position, not word boundary
    words = text.split(" ")
    lines = []
    current_line = ""
    word_index = 0
    
    for i, word in enumerate(words):
        space = " " if i > 0 else ""
        test_line = current_line + space + word
        
        if font_text.size(test_line)[0] < textbox_rect.width - 40:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    
    if current_line:
        lines.append(current_line)
    
    # Draw lines with vertical centering
    total_height = len(lines) * font_text.get_linesize()
    y_offset = textbox_rect.y + (textbox_rect.height - total_height) // 2
    
    for line in lines:
        text_surf = font_text.render(line.strip(), True, WHITE)
        text_rect = text_surf.get_rect(x=textbox_rect.x + 20, y=y_offset)
        screen.blit(text_surf, text_rect)
        y_offset += font_text.get_linesize()
    
    return textbox_rect


def draw_next_button():
    """Draw the 'Next' button in the bottom-right corner. Returns button rect."""
    button_width = 120
    button_height = 50
    button_x = SCREEN_WIDTH - button_width - 30
    button_y = SCREEN_HEIGHT - button_height - 30
    button_rect = pygame.Rect(button_x, button_y, button_width, button_height)
    
    # Draw button background
    pygame.draw.rect(screen, BLACK, button_rect)
    pygame.draw.rect(screen, GOLD, button_rect, 3)
    
    # Draw button text
    button_text = font_button.render("Next", True, WHITE)
    text_rect = button_text.get_rect(center=button_rect.center)
    screen.blit(button_text, text_rect)
    
    return button_rect


def run_cutscene():
    """Main cutscene loop."""
    scene_index = 0
    chars_displayed = 0
    text_fully_shown = False
    time_text_finished = 0
    text_timer = 0.0  # Accumulates time for typewriter effect
    pause_timer = 0.0  # Accumulates pause time between scenes
    
    running = True
    
    while running and scene_index < len(SCENES):
        delta_time = clock.tick(FPS) / 1000.0  # seconds
        mouse_pos = pygame.mouse.get_pos()
        
        # Load current scene
        image_file, text_content = SCENES[scene_index]
        background = load_image(image_file)
        
        # --- Event Handling ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            # On last scene, check if "Next" button was clicked
            if scene_index == len(SCENES) - 1 and text_fully_shown:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    next_button_rect = draw_next_button()
                    if next_button_rect.collidepoint(mouse_pos):
                        # Transition to interrogation scene
                        run_interrogation()
                        return  # Exit cutscene after interrogation ends
        
        # --- Update Typewriter Effect ---
        if not text_fully_shown:
            text_timer += delta_time
            # Calculate characters to display based on accumulated time
            chars_to_show = int(text_timer * CHARS_PER_SECOND)
            chars_displayed = min(chars_to_show, len(text_content))
            
            if chars_displayed >= len(text_content):
                text_fully_shown = True
                pause_timer = 0.0
        
        # --- Check if should advance to next scene ---
        if text_fully_shown:
            pause_timer += delta_time
            
            # Auto-advance after pause (except on last scene)
            if scene_index < len(SCENES) - 1 and pause_timer >= (PAUSE_BETWEEN_SCENES / 1000.0):
                scene_index += 1
                chars_displayed = 0
                text_fully_shown = False
                text_timer = 0.0
                pause_timer = 0.0
        
        # --- Rendering ---
        screen.blit(background, (0, 0))
        
        # Draw textbox with partial or full text
        displayed_text = text_content[:chars_displayed]
        draw_textbox_with_text(displayed_text)
        
        # Draw "Next" button on final scene when text is complete
        if scene_index == len(SCENES) - 1 and text_fully_shown:
            next_button_rect = draw_next_button()
            # Hover effect
            if next_button_rect.collidepoint(mouse_pos):
                pygame.draw.rect(screen, WHITE, next_button_rect, 3)
        
        pygame.display.flip()
    
    # Don't quit pygame here - let interrogation continue


# --- Interrogation/Dialogue System ---
# Dialogue data: list of (speaker, text)
DIALOGUE = [
    ("Suspect1", "I'm innocent"),
    ("Suspect2", "That's not the truth"),
    ("Suspect1", "I swear it"),
    ("Suspect2", "We'll see about that"),
]


def run_interrogation():
    """Interrogation scene with command-prompt style dialogue and player input."""
    global screen, clock
    
    pygame.display.set_caption("Interrogation")
    
    # Initialize suspects and game
    initialize_suspects()
    
    # Load background
    background = load_image("mainimage.jpg")
    
    dialogue_index = 0
    player_input = ""
    dialogue_history = []  # List of (speaker, text) tuples displayed
    game_over = False
    verdict_result = None
    verdict_timer = 0.0
    interrogation_timer = 0.0  # Timer for 5 minute interrogation
    INTERROGATION_TIME = 300.0  # 5 minutes in seconds
    
    running = True
    
    while running:
        delta_time = clock.tick(FPS) / 1000.0
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if event.type == pygame.KEYDOWN and not game_over:
                if event.key == pygame.K_RETURN:
                    # Player hit enter
                    if player_input.strip():
                        user_input = player_input.strip().upper()
                        dialogue_history.append(("Player", player_input))
                        
                        # Check if input is a verdict (S1-S5)
                        if user_input in ["S1", "S2", "S3", "S4", "S5"]:
                            # Check the verdict
                            is_correct, message = check_verdict(user_input)
                            dialogue_history.append(("System", message))
                            game_over = True
                            verdict_result = (is_correct, message)
                            verdict_timer = 0.0
                        else:
                            # Regular dialogue
                            if dialogue_index < len(DIALOGUE):
                                speaker, text = DIALOGUE[dialogue_index]
                                dialogue_history.append((speaker, text))
                                dialogue_index += 1
                        
                        player_input = ""
                
                elif event.key == pygame.K_BACKSPACE:
                    player_input = player_input[:-1]
                
                else:
                    # Add character to player input
                    if len(player_input) < 100:  # Max 100 chars per line
                        player_input += event.unicode
        
        # Track time for verdict display
        if game_over:
            verdict_timer += delta_time
        
        # Track interrogation timer
        if not game_over:
            interrogation_timer += delta_time
            
            # Check if time is up
            if interrogation_timer >= INTERROGATION_TIME:
                dialogue_history.append(("System", "⏰ Time's up! You ran out of time to solve the case."))
                game_over = True
                verdict_result = (False, "Time's up!")
                verdict_timer = 0.0
        
        # --- Rendering ---
        screen.blit(background, (0, 0))
        
        # Draw dialogue box
        dialogue_box_height = SCREEN_HEIGHT // 2
        dialogue_box_rect = pygame.Rect(20, SCREEN_HEIGHT - dialogue_box_height - 20, SCREEN_WIDTH - 40, dialogue_box_height - 20)
        
        # Draw semi-transparent background
        dialogue_surf = pygame.Surface((dialogue_box_rect.width, dialogue_box_rect.height))
        dialogue_surf.set_alpha(TEXTBOX_ALPHA)
        dialogue_surf.fill(BLACK)
        screen.blit(dialogue_surf, (dialogue_box_rect.x, dialogue_box_rect.y))
        pygame.draw.rect(screen, GOLD, dialogue_box_rect, 3)
        
        # Render dialogue history
        font_dialogue = pygame.font.SysFont("courier", 18)
        line_height = font_dialogue.get_linesize()
        y_offset = dialogue_box_rect.y + 10
        
        # Display past dialogue
        for speaker, text in dialogue_history:
            prefix = f"> {speaker}: "
            dialogue_line = prefix + text
            text_surf = font_dialogue.render(dialogue_line, True, WHITE)
            screen.blit(text_surf, (dialogue_box_rect.x + 10, y_offset))
            y_offset += line_height
        
        # Display current player input prompt (only if game not over)
        if not game_over:
            player_prompt = "> Player: " + player_input
            player_prompt_surf = font_dialogue.render(player_prompt, True, WHITE)
            screen.blit(player_prompt_surf, (dialogue_box_rect.x + 10, y_offset))
        
        # Draw timer in top right corner
        remaining_time = max(0, INTERROGATION_TIME - interrogation_timer)
        minutes = int(remaining_time) // 60
        seconds = int(remaining_time) % 60
        timer_text = f"{minutes:02d}:{seconds:02d}"
        
        font_timer = pygame.font.SysFont("courier", 32, bold=True)
        timer_color = GOLD if remaining_time > 30 else (255, 100, 100) if remaining_time > 0 else (255, 0, 0)
        timer_surf = font_timer.render(timer_text, True, timer_color)
        timer_rect = timer_surf.get_rect()
        timer_rect.topright = (SCREEN_WIDTH - 20, 20)
        screen.blit(timer_surf, timer_rect)
        
        # If game over, show exit message after 3 seconds
        if game_over and verdict_timer > 3.0:
            running = False
        
        pygame.display.flip()
    
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    run_cutscene()