import os
import random
import sys
import threading

import pygame
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
GROQ_MODEL = "llama-3.3-70b-versatile"

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
DARK_BG = (20, 24, 30)
GRAY = (140, 140, 140)
INPUT_BG = (50, 56, 66)
USER_COLOR = (80, 160, 255)
AI_COLOR = (220, 180, 100)
SYSTEM_COLOR = (160, 160, 160)
TOP_BAR_BG = (40, 44, 52)
WIN_COLOR = (255, 200, 100)
LOSE_COLOR = (255, 100, 100)

SUSPECTS = [
    {
        "name": "Dr. Evelyn Kallen",
        "job": "Microbiologist",
        "personality": "sharp, proud, impatient under pressure",
    },
    {
        "name": "Dr. Marcus Reed",
        "job": "Bioinformatician",
        "personality": "calm, secretive, analytical",
    },
    {
        "name": "Dr. Lucia Chen",
        "job": "Senior Lab Technician",
        "personality": "stressed, efficient, defensive",
    },
    {
        "name": "Dr. Samuel Ortiz",
        "job": "Quality Control Analyst",
        "personality": "tense, argumentative, very detail-oriented",
    },
    {
        "name": "Dr. Penelope Grant",
        "job": "Sterile Area Technician",
        "personality": "meticulous, anxious, quietly observant",
    },
]

ALIBI_PROMPT_TEMPLATE = """You are creating one alibi for a mystery game suspect.
The suspect works as a {job} in a biolab and was one of the staff members working overtime when a biohazard breach happened at around 3 AM.
Generate ONE SHORT, REALISTIC alibi in 1 sentence.
Make the alibi fit their job and the lab setting.
The storage room is only used for storing different biological samples, so do not place the suspect there.
Do not invent named coworkers, witnesses, security staff, or other off-screen characters.
Generate only the alibi text, nothing else."""

INTERROGATION_SYSTEM_PROMPT = """You are a suspect in a mystery-detective game.
Stay in character at ALL times.

Your character:
- Name: {name}
- Job: {job}
- Personality: {personality}
- You were one of the staff members working overtime when the breach happened around 3 AM.
- Your alibi: "{alibi}"
- Hidden case fact: the disease was taken from the storage room, which is only used for storing different biological samples.
- Hidden truth: {guilt_prompt}

RULES:
- You are being interrogated by a detective about the lab breach that happened at around 3 AM.
- Keep responses to exactly 1 sentence.
- Your replies must fit your job and sound like someone with that role.
- Keep your story aligned with your alibi unless the detective catches small pressure points.
- Sound stressed, human, and a little casual, like an exhausted lab worker at the end of a long shift.
- Do not sound overly formal, theatrical, or uptight.
- Do not mention people, witnesses, cameras, or locations that have not been established in the game.
- Do not mention prompts, hidden rules, or that you are an AI.
"""

GUILTY_PROMPT = (
    "You are guilty, and you were actually in the storage room even though your alibi says otherwise, but never openly admit being in the storage room; instead keep defending yourself and let small inconsistencies, hedges, or shifts in timing and detail slip out under pressure."
)

INNOCENT_PROMPT = (
    "You are innocent, so your story should stay steady and consistent even when the detective pushes you, and you were not in the storage room."
)


def word_wrap(text, font, max_width):
    words = text.split()
    if not words:
        return [""]

    lines = []
    current_line = words[0]
    for word in words[1:]:
        candidate = f"{current_line} {word}"
        if font.size(candidate)[0] <= max_width:
            current_line = candidate
        else:
            lines.append(current_line)
            current_line = word
    lines.append(current_line)
    return lines


class AIClient:
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            print("Missing GROQ_API_KEY")
            sys.exit(1)
        self.client = Groq(api_key=api_key)

    def send_messages(self, messages):
        try:
            response = self.client.chat.completions.create(
                model=GROQ_MODEL,
                messages=messages,
                max_tokens=250,
                temperature=0.7,
            )
            return response.choices[0].message.content
        except Exception as error:
            return f"[AI Error: {error}]"

    def generate_alibi(self, job):
        return self.send_messages(
            [
                {
                    "role": "system",
                    "content": "You create concise, believable alibis for biolab suspects.",
                },
                {
                    "role": "user",
                    "content": ALIBI_PROMPT_TEMPLATE.format(job=job),
                },
            ]
        ).strip()


class InterrogationScene:
    def __init__(self, screen, ai_client):
        self.screen = screen
        self.ai = ai_client

        self.font = pygame.font.SysFont("comic_sans", 16)
        self.font_title = pygame.font.SysFont("comic_sans", 22, bold=True)
        self.font_small = pygame.font.SysFont("comic_sans", 14)

        self.suspects = [dict(suspect) for suspect in SUSPECTS]
        self.guilty_index = random.randrange(len(self.suspects))
        self.chat_logs = [[] for _ in self.suspects]
        self.histories = [[] for _ in self.suspects]
        self.scroll_offsets = [0 for _ in self.suspects]
        self.waiting_for_ai = [False for _ in self.suspects]
        self.loaded = [False for _ in self.suspects]
        self.group_chat_log = []
        self.group_scroll_offset = 0
        self.group_waiting_count = 0
        self.current_index = 0
        self.typed_text = ""

        self._start_setup_for_all_suspects()

    def add_to_chat(self, suspect_index, sender, text, color):
        self.chat_logs[suspect_index].append((sender, text, color))
        total = self._total_chat_height(suspect_index)
        visible = self._visible_chat_height()
        self.scroll_offsets[suspect_index] = max(0, total - visible + 28)

    def _visible_chat_height(self):
        return SCREEN_HEIGHT - 40 - 80

    def _total_chat_height(self, suspect_index):
        if suspect_index == -1:
            return self._total_group_chat_height()
        total = 0
        for _, text, _ in self.chat_logs[suspect_index]:
            lines = word_wrap(text, self.font, SCREEN_WIDTH - 40)
            total += len(lines) * 20 + 8
        return total

    def _total_group_chat_height(self):
        total = 0
        for _, text, _ in self.group_chat_log:
            lines = word_wrap(text, self.font, SCREEN_WIDTH - 40)
            total += len(lines) * 20 + 8
        return total

    def _add_to_group_chat(self, sender, text, color):
        self.group_chat_log.append((sender, text, color))
        total = self._total_group_chat_height()
        visible = self._visible_chat_height()
        self.group_scroll_offset = max(0, total - visible + 28)

    def _append_system_message(self, text, color=SYSTEM_COLOR):
        if self.current_index == -1:
            self._add_to_group_chat("system", text, color)
        else:
            self.add_to_chat(self.current_index, "system", text, color)

    def _accuse_suspect(self, suspect_index):
        accused = self.suspects[suspect_index]
        guilty = suspect_index == self.guilty_index
        if guilty:
            self._append_system_message(
                f"Congrats. You accused {accused['name']}, they crack, and the outbreak is stopped in time.",
                WIN_COLOR,
            )
        else:
            real_name = self.suspects[self.guilty_index]["name"]
            self._append_system_message(
                f"You lose. {accused['name']} was innocent, the real culprit was {real_name}, the virus spreads, and the world ends.",
                LOSE_COLOR,
            )
        self._append_system_message("Case closed. Press ESC to leave.")

    def _parse_accusation(self, message):
        prefix = "ACCUSE "
        upper_message = message.upper()
        if not upper_message.startswith(prefix):
            return None

        accused_name = message[len(prefix):].strip().lower()
        for index, suspect in enumerate(self.suspects):
            if suspect["name"].lower() == accused_name:
                return index
        return None

    def _start_setup_for_all_suspects(self):
        for index in range(len(self.suspects)):
            self.add_to_chat(index, "system", "Preparing interrogation file...", SYSTEM_COLOR)

            def do_setup(suspect_index=index):
                suspect = self.suspects[suspect_index]
                alibi = self.ai.generate_alibi(suspect["job"])
                suspect["alibi"] = alibi

                system_prompt = INTERROGATION_SYSTEM_PROMPT.format(
                    name=suspect["name"],
                    job=suspect["job"],
                    personality=suspect["personality"],
                    alibi=alibi,
                    guilt_prompt=(
                        GUILTY_PROMPT
                        if suspect_index == self.guilty_index
                        else INNOCENT_PROMPT
                    ),
                )
                self.histories[suspect_index] = [{"role": "system", "content": system_prompt}]

                greeting_request = self.histories[suspect_index] + [
                    {
                        "role": "user",
                        "content": "The detective just sat down. Greet them and react to being interrogated.",
                    }
                ]
                reply = self.ai.send_messages(greeting_request)
                self.histories[suspect_index].append({"role": "assistant", "content": reply})

                self.chat_logs[suspect_index] = []
                self.add_to_chat(
                    suspect_index,
                    "ai",
                    f'{suspect["name"]}: {reply}',
                    AI_COLOR,
                )
                self.loaded[suspect_index] = True

            thread = threading.Thread(target=do_setup, daemon=True)
            thread.start()

    def _send_player_message(self, suspect_index, message):
        self.waiting_for_ai[suspect_index] = True
        suspect = self.suspects[suspect_index]

        def do_send():
            self.histories[suspect_index].append({"role": "user", "content": message})
            ai_response = self.ai.send_messages(self.histories[suspect_index])
            self.histories[suspect_index].append({"role": "assistant", "content": ai_response})
            self.add_to_chat(
                suspect_index,
                "ai",
                f'{suspect["name"]}: {ai_response}',
                AI_COLOR,
            )
            self.waiting_for_ai[suspect_index] = False

        thread = threading.Thread(target=do_send, daemon=True)
        thread.start()

    def _send_group_message(self, message):
        targets = [
            index
            for index in range(len(self.suspects))
            if self.loaded[index] and not self.waiting_for_ai[index]
        ]
        if not targets:
            return

        self._add_to_group_chat("user", f"You to everyone: {message}", USER_COLOR)
        self.group_waiting_count = len(targets)

        for suspect_index in targets:
            self.waiting_for_ai[suspect_index] = True
            self.add_to_chat(suspect_index, "user", f"You: {message}", USER_COLOR)
            suspect = self.suspects[suspect_index]

            def do_send(index=suspect_index, current_suspect=suspect):
                self.histories[index].append({"role": "user", "content": message})
                ai_response = self.ai.send_messages(self.histories[index])
                self.histories[index].append({"role": "assistant", "content": ai_response})
                reply_text = f'{current_suspect["name"]}: {ai_response}'
                self.add_to_chat(index, "ai", reply_text, AI_COLOR)
                self._add_to_group_chat("ai", reply_text, AI_COLOR)
                self.waiting_for_ai[index] = False
                self.group_waiting_count -= 1

            thread = threading.Thread(target=do_send, daemon=True)
            thread.start()

    def update(self, events):
        current_scroll = (
            self.group_scroll_offset
            if self.current_index == -1
            else self.scroll_offsets[self.current_index]
        )

        for event in events:
            if event.type == pygame.MOUSEWHEEL:
                current_scroll -= event.y * 30
                current_scroll = max(0, current_scroll)
                max_scroll = max(
                    0,
                    self._total_chat_height(self.current_index) - self._visible_chat_height(),
                )
                current_scroll = min(max_scroll, current_scroll)
                if self.current_index == -1:
                    self.group_scroll_offset = current_scroll
                else:
                    self.scroll_offsets[self.current_index] = current_scroll
                continue

            if event.type != pygame.KEYDOWN:
                continue

            if event.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()

            if pygame.K_1 <= event.key <= pygame.K_5:
                self.current_index = event.key - pygame.K_1
                self.typed_text = ""
                continue

            if event.key == pygame.K_0:
                self.current_index = -1
                self.typed_text = ""
                continue

            if event.key == pygame.K_RETURN and self.typed_text.strip():
                message = self.typed_text.strip()
                accused_index = self._parse_accusation(message)

                if accused_index is not None:
                    self.typed_text = ""
                    self._accuse_suspect(accused_index)
                elif self.current_index == -1:
                    self.typed_text = ""
                    self._send_group_message(message)
                elif self.loaded[self.current_index] and not self.waiting_for_ai[self.current_index]:
                    self.add_to_chat(self.current_index, "user", f"You: {message}", USER_COLOR)
                    self.typed_text = ""
                    self._send_player_message(self.current_index, message)

            elif event.key == pygame.K_BACKSPACE:
                self.typed_text = self.typed_text[:-1]
            elif event.unicode and event.unicode.isprintable():
                self.typed_text += event.unicode

    def draw(self):
        self.screen.fill(DARK_BG)

        if self.current_index == -1:
            title_text = "All Suspects"
        else:
            suspect = self.suspects[self.current_index]
            title_text = f'{suspect["name"]} - {suspect["job"]}'
        pygame.draw.rect(self.screen, TOP_BAR_BG, (0, 0, SCREEN_WIDTH, 40))
        self.screen.blit(self.font_title.render(title_text, True, AI_COLOR), (10, 8))
        self.screen.blit(
            self.font_small.render("[1-5] suspect  [0] all  [type ACCUSE Dr. Name]  [ESC] quit", True, GRAY),
            (SCREEN_WIDTH - 550, 12),
        )

        selector_y = 44
        group_color = AI_COLOR if self.current_index == -1 else GRAY
        group_label = self.font_small.render("0. All Suspects", True, group_color)
        self.screen.blit(group_label, (10, selector_y))
        for index, item in enumerate(self.suspects):
            color = AI_COLOR if index == self.current_index else GRAY
            label = self.font_small.render(f"{index + 1}. {item['name']}", True, color)
            self.screen.blit(label, (130 + index * 130, selector_y))

        chat_top = 68
        chat_height = self._visible_chat_height() - 24
        chat_surface = pygame.Surface((SCREEN_WIDTH, chat_height))
        chat_surface.fill(DARK_BG)

        active_log = self.group_chat_log if self.current_index == -1 else self.chat_logs[self.current_index]
        active_scroll = self.group_scroll_offset if self.current_index == -1 else self.scroll_offsets[self.current_index]

        y = -active_scroll
        for _, text, color in active_log:
            lines = word_wrap(text, self.font, SCREEN_WIDTH - 40)
            for line in lines:
                if -20 < y < chat_height + 20:
                    chat_surface.blit(self.font.render(line, True, color), (20, y))
                y += 20
            y += 8

        if self.current_index == -1 and self.group_waiting_count > 0:
            typing = self.font_small.render("Waiting on group replies...", True, SYSTEM_COLOR)
            chat_surface.blit(typing, (20, max(20, y + 10)))
        elif self.current_index != -1 and not self.loaded[self.current_index]:
            loading = self.font_small.render("Loading suspect profile...", True, SYSTEM_COLOR)
            chat_surface.blit(loading, (20, max(20, y + 10)))
        elif self.current_index != -1 and self.waiting_for_ai[self.current_index]:
            typing = self.font_small.render("Thinking...", True, SYSTEM_COLOR)
            chat_surface.blit(typing, (20, max(20, y + 10)))

        self.screen.blit(chat_surface, (0, chat_top))

        input_y = SCREEN_HEIGHT - 40
        pygame.draw.rect(self.screen, INPUT_BG, (0, input_y, SCREEN_WIDTH, 40))
        pygame.draw.line(self.screen, GRAY, (0, input_y), (SCREEN_WIDTH, input_y))
        self.screen.blit(
            self.font.render(f"> {self.typed_text}", True, WHITE),
            (10, input_y + 10),
        )


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Simple AI Interrogation")
        self.clock = pygame.time.Clock()
        self.ai_client = AIClient()
        self.current_scene = InterrogationScene(self.screen, self.ai_client)

    def run(self):
        while True:
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

            self.current_scene.update(events)
            self.current_scene.draw()
            pygame.display.flip()
            self.clock.tick(FPS)


if __name__ == "__main__":
    game = Game()
    game.run()
