import os
import sys
import pygame

pygame.init()

WIDTH, HEIGHT = 1365, 768
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Lab Breakout")
CLOCK = pygame.time.Clock()

# ---------- Colors ----------
BG_DARK = (6, 12, 31)
BG_MID = (11, 27, 58)
BG_LIGHT = (20, 44, 90)
PANEL_BG = (15, 23, 46)
PANEL_STROKE = (5, 7, 15)
INNER_STROKE = (79, 111, 179)
TEXT = (238, 243, 255)
MUTED = (159, 180, 229)
BUTTON_BLUE = (58, 124, 255)
BUTTON_BLUE_DARK = (30, 72, 160)
BUTTON_TEAL = (77, 210, 192)
BUTTON_TEAL_DARK = (43, 115, 105)
NOTE_BG = (31, 63, 143)
NOTE_BG_DARK = (22, 44, 99)
WARNING = (233, 191, 63)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

# ---------- Fonts ----------
def get_font(size, bold=False):
    candidates = [
        "comicsansms",
        "comic sans ms",
        "arialrounded",
        "arial",
    ]
    for name in candidates:
        try:
            return pygame.font.SysFont(name, size, bold=bold)
        except Exception:
            continue
    return pygame.font.Font(None, size)

TITLE_FONT = get_font(72)
LABEL_FONT = get_font(34, bold=True)
BUTTON_FONT = get_font(28, bold=True)
SMALL_FONT = get_font(20)
TINY_FONT = get_font(16)

# ---------- Helpers ----------
def draw_vertical_gradient(surface, rect, top_color, bottom_color):
    x, y, w, h = rect
    for i in range(h):
        t = i / max(1, h - 1)
        color = (
            int(top_color[0] * (1 - t) + bottom_color[0] * t),
            int(top_color[1] * (1 - t) + bottom_color[1] * t),
            int(top_color[2] * (1 - t) + bottom_color[2] * t),
        )
        pygame.draw.line(surface, color, (x, y + i), (x + w, y + i))


def draw_round_rect(surface, rect, color, radius=20, border=0, border_color=None):
    pygame.draw.rect(surface, color, rect, border_radius=radius)
    if border and border_color:
        pygame.draw.rect(surface, border_color, rect, width=border, border_radius=radius)


def draw_text(surface, text, font, color, pos, center=False):
    img = font.render(text, True, color)
    r = img.get_rect()
    if center:
        r.center = pos
    else:
        r.topleft = pos
    surface.blit(img, r)
    return r


def blit_fit(surface, image, rect):
    target_ratio = rect.width / rect.height
    image_ratio = image.get_width() / image.get_height()

    if image_ratio > target_ratio:
        new_h = rect.height
        new_w = int(new_h * image_ratio)
    else:
        new_w = rect.width
        new_h = int(new_w / image_ratio)

    scaled = pygame.transform.smoothscale(image, (new_w, new_h))
    x = rect.x + (rect.width - new_w) // 2
    y = rect.y + (rect.height - new_h) // 2
    surface.blit(scaled, (x, y))


def load_lab_image():
    path = "/mnt/data/a9f7fdf3-c839-41ba-99fc-872591ddab52.png"
    if os.path.exists(path):
        try:
            return pygame.image.load(path).convert()
        except Exception:
            return None
    return None


LAB_IMAGE = load_lab_image()

# ---------- UI Components ----------
class Button:
    def __init__(self, rect, text, primary=True, icon=""):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.primary = primary
        self.icon = icon
        self.hovered = False

    def draw(self, surface):
        top = BUTTON_TEAL if self.primary else BUTTON_BLUE
        bottom = BUTTON_TEAL_DARK if self.primary else BUTTON_BLUE_DARK
        shadow_rect = self.rect.move(0, 6)
        draw_round_rect(surface, shadow_rect, (11, 19, 38), radius=14)

        btn_surf = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        draw_vertical_gradient(btn_surf, (0, 0, self.rect.width, self.rect.height), top, bottom)
        pygame.draw.rect(btn_surf, (255, 255, 255, 35), (0, 0, self.rect.width, 18), border_radius=14)
        surface.blit(btn_surf, self.rect.topleft)
        pygame.draw.rect(surface, (20, 30, 55), self.rect, width=3, border_radius=14)

        if self.hovered:
            glow = pygame.Surface((self.rect.width + 16, self.rect.height + 16), pygame.SRCALPHA)
            pygame.draw.rect(glow, (255, 255, 255, 26), glow.get_rect(), border_radius=18)
            surface.blit(glow, (self.rect.x - 8, self.rect.y - 8))

        if self.icon:
            draw_text(surface, self.icon, LABEL_FONT, WHITE, (self.rect.x + 16, self.rect.y + 16))
        draw_text(surface, self.text, BUTTON_FONT, WHITE, (self.rect.right - 170, self.rect.y + 20))

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self.rect.collidepoint(event.pos)
        return False


# ---------- Layout ----------
def draw_background(surface):
    draw_vertical_gradient(surface, (0, 0, WIDTH, HEIGHT), BG_LIGHT, BG_DARK)
    for x in range(0, WIDTH, 120):
        pygame.draw.line(surface, (255, 255, 255, 10), (x, 0), (x, HEIGHT))
    glow = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    pygame.draw.circle(glow, (80, 120, 255, 36), (WIDTH // 2, 0), 280)
    surface.blit(glow, (0, 0))


def draw_panel(surface, rect, bg=PANEL_BG, radius=22):
    shadow = rect.move(0, 6)
    draw_round_rect(surface, shadow, (8, 12, 24), radius)
    draw_round_rect(surface, rect, bg, radius, border=4, border_color=PANEL_STROKE)
    inner = rect.inflate(-8, -8)
    pygame.draw.rect(surface, INNER_STROKE, inner, width=2, border_radius=max(8, radius - 4))


def draw_note(surface, rect, title, text):
    note_surf = pygame.Surface(rect.size)
    draw_vertical_gradient(note_surf, (0, 0, rect.width, rect.height), NOTE_BG, NOTE_BG_DARK)
    surface.blit(note_surf, rect.topleft)
    pygame.draw.rect(surface, (26, 46, 90), rect, width=3, border_radius=12)
    draw_text(surface, title, TINY_FONT, MUTED, (rect.x + 14, rect.y + 10))
    draw_text(surface, text, SMALL_FONT, TEXT, (rect.x + 14, rect.y + 30))


def draw_visual_panel(surface, rect):
    draw_panel(surface, rect, bg=(23, 34, 70), radius=28)
    inner = rect.inflate(-26, -26)

    screen_frame = inner.copy()
    draw_round_rect(surface, screen_frame, (38, 53, 91), radius=18, border=4, border_color=(170, 185, 220))

    screen = screen_frame.inflate(-16, -16)
    draw_round_rect(surface, screen, (3, 5, 10), radius=14)

    if LAB_IMAGE:
        img_rect = screen.inflate(-2, -2)
        blit_fit(surface, LAB_IMAGE, img_rect)
        overlay = pygame.Surface((img_rect.width, img_rect.height), pygame.SRCALPHA)
        overlay.fill((10, 16, 30, 88))
        surface.blit(overlay, img_rect.topleft)
    else:
        pygame.draw.rect(surface, BLACK, screen, border_radius=14)
        for i in range(40):
            pygame.draw.circle(surface, WHITE, (screen.x + 30 + (i * 31) % (screen.width - 60), screen.y + 20 + (i * 47) % (screen.height - 40)), 2)

    shine = pygame.Surface((120, screen.height), pygame.SRCALPHA)
    pygame.draw.polygon(shine, (255, 255, 255, 22), [(70, 0), (120, 0), (50, screen.height), (0, screen.height)])
    surface.blit(shine, (screen.right - 190, screen.y))
    surface.blit(pygame.transform.scale(shine, (50, screen.height)), (screen.right - 110, screen.y))

    tag_rect = pygame.Rect(screen.x + 24, screen.bottom - 54, 190, 40)
    draw_round_rect(surface, tag_rect, WARNING, radius=10, border=3, border_color=(45, 48, 52))
    draw_text(surface, "QUARANTINE SECTOR", SMALL_FONT, (30, 33, 37), (tag_rect.x + 12, tag_rect.y + 10))


def main():
    left_w = 470
    gap = 24
    margin = 32
    top = 40
    title_y = top + 10
    title_x = margin + 24

    left_panel_rect = pygame.Rect(margin, top + 90, left_w, 560)
    right_panel_rect = pygame.Rect(margin + left_w + gap, top + 70, WIDTH - (margin * 2 + left_w + gap), 580)

    play_btn = Button((left_panel_rect.x + 18, left_panel_rect.y + 18, left_panel_rect.width - 36, 78), "Play", primary=True, icon="🧪")
    instr_btn = Button((left_panel_rect.x + 18, left_panel_rect.y + 110, left_panel_rect.width - 36, 78), "Instructions", primary=False, icon="🗒")

    note1 = pygame.Rect(left_panel_rect.x + 18, left_panel_rect.y + 220, left_panel_rect.width - 36, 74)
    note2 = pygame.Rect(left_panel_rect.x + 18, left_panel_rect.y + 306, left_panel_rect.width - 36, 74)

    credits_rect = pygame.Rect(left_panel_rect.x + 120, left_panel_rect.bottom - 62, 120, 38)

    running = True
    message = ""

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if play_btn.handle_event(event):
                message = "Play clicked"
            if instr_btn.handle_event(event):
                message = "Instructions clicked"

        draw_background(SCREEN)

        # Title
        draw_text(SCREEN, "Lab Breakout", TITLE_FONT, TEXT, (title_x, title_y))

        # Left panel
        draw_panel(SCREEN, left_panel_rect, bg=(20, 27, 54), radius=22)
        play_btn.draw(SCREEN)
        instr_btn.draw(SCREEN)

        draw_note(SCREEN, note1, "CASE FILE", "An experiment went wrong.")
        draw_note(SCREEN, note2, "OBJECTIVE", "Search for clues and escape.")

        draw_round_rect(SCREEN, credits_rect, (112, 114, 119), radius=8, border=3, border_color=(59, 64, 69))
        draw_text(SCREEN, "Credits", SMALL_FONT, (240, 240, 242), (credits_rect.x + 24, credits_rect.y + 8))
        draw_text(SCREEN, "v0.1.0a (prototype build)", TINY_FONT, MUTED, (left_panel_rect.x + 120, left_panel_rect.bottom - 18), center=False)

        # Right visual panel
        draw_visual_panel(SCREEN, right_panel_rect)

        # Optional status message
        if message:
            draw_text(SCREEN, message, SMALL_FONT, MUTED, (WIDTH - 220, HEIGHT - 36))

        pygame.display.flip()
        CLOCK.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()

