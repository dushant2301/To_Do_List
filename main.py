import pygame
import sys
import time
import math

# --- Configuration & Constants ---
WIDTH, HEIGHT = 600, 800
FPS = 60

# Colors
BG_COLOR = (15, 23, 42)          # #0f172a
CARD_COLOR = (30, 41, 59)        # #1e293b
ACCENT_COLOR = (56, 189, 248)    # #38bdf8
TEXT_COLOR = (226, 232, 240)     # #e2e8f0
TEXT_MUTED = (148, 163, 184)     # #94a3b8
COMPLETED_COLOR = (71, 85, 105)  # #475569
DELETE_COLOR = (244, 63, 94)     # #f43f5e

# Layout
MARGIN_X = 40
MARGIN_Y = 50
CARD_HEIGHT = 70
CARD_SPACING = 15
CORNER_RADIUS = 12
CHECKBOX_SIZE = 24

# Animation Constants
EASE_SPEED = 0.15

# Global Init
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Modern To-Do List")
clock = pygame.time.Clock()

# Fonts
try:
    font_large = pygame.font.SysFont("segoeui", 36, bold=True)
    font_medium = pygame.font.SysFont("segoeui", 22)
    font_small = pygame.font.SysFont("segoeui", 16)
except:
    font_large = pygame.font.Font(None, 48)
    font_medium = pygame.font.Font(None, 32)
    font_small = pygame.font.Font(None, 24)

# --- Utility Functions ---
def draw_rounded_rect(surface, color, rect, radius):
    pygame.draw.rect(surface, color, rect, border_radius=radius)

def ease_out_expo(x):
    return x if x == 1 else 1 - math.pow(2, -10 * x)

def lerp(a, b, t):
    return a + (b - a) * t

# --- Classes ---
class Task:
    def __init__(self, text):
        self.text = text
        self.completed = False
        
        # Animations
        self.target_y = 0
        self.current_y = None # Will snap to target_y to avoid flying up through screen
        self.current_x_offset = -WIDTH # Slide in from left
        self.alpha_target = 255
        self.current_alpha = 0
        
        # State transitions
        self.completion_progress = 0.0 # 0 to 1
        
        # Hover states
        self.hover_progress = 0.0
        self.delete_hover_progress = 0.0
        
        self.deleting = False
        self.is_dead = False

    def update(self, dt):
        # Initialize starting positions
        if self.current_y is None:
            self.current_y = self.target_y
            
        # Position easing
        self.current_y = lerp(self.current_y, self.target_y, EASE_SPEED)
        self.current_x_offset = lerp(getattr(self, 'current_x_offset', 0), 0, EASE_SPEED)
        self.current_alpha = lerp(self.current_alpha, self.alpha_target, EASE_SPEED)
        
        if self.deleting:
            self.alpha_target = 0
            if self.current_alpha < 5:
                self.is_dead = True
                
        # Completion animation
        target_comp = 1.0 if self.completed else 0.0
        self.completion_progress = lerp(self.completion_progress, target_comp, EASE_SPEED)

    def draw(self, surface, x, y_override=None):
        y = y_override if y_override is not None else self.current_y
        
        if self.current_alpha < 5:
            return
            
        actual_x = x + int(getattr(self, 'current_x_offset', 0))
        rect = pygame.Rect(actual_x, y, WIDTH - 2 * x, CARD_HEIGHT)
        
        # Create a surface for alpha blending
        card_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        
        # Card background with hover effect
        bg_scale = lerp(0, 15, self.hover_progress)
        current_bg = (min(255, CARD_COLOR[0] + bg_scale), min(255, CARD_COLOR[1] + bg_scale), min(255, CARD_COLOR[2] + bg_scale), int(self.current_alpha))
        draw_rounded_rect(card_surf, current_bg, pygame.Rect(0, 0, rect.width, rect.height), CORNER_RADIUS)
        
        # Draw checkbox
        cb_rect = pygame.Rect(20, (CARD_HEIGHT - CHECKBOX_SIZE) // 2, CHECKBOX_SIZE, CHECKBOX_SIZE)
        
        # Checkbox background and border
        border_color = (ACCENT_COLOR[0], ACCENT_COLOR[1], ACCENT_COLOR[2], int(self.current_alpha))
        draw_rounded_rect(card_surf, (*CARD_COLOR, int(self.current_alpha)), cb_rect, 6)
        pygame.draw.rect(card_surf, border_color, cb_rect, 2, border_radius=6)
        
        # Fill checkbox if completed
        if self.completion_progress > 0.01:
            fill_rect = cb_rect.inflate(-8, -8)
            fill_alpha = int(self.current_alpha * self.completion_progress)
            
            # Use a slightly smaller rect based on completion progress for pop effect
            pop_size = int(fill_rect.width * self.completion_progress)
            if pop_size > 0:
                pop_rect = pygame.Rect(0, 0, pop_size, pop_size)
                pop_rect.center = cb_rect.center
                draw_rounded_rect(card_surf, (*ACCENT_COLOR, fill_alpha), pop_rect, 4)

        # Draw Text
        text_color = [
            int(lerp(TEXT_COLOR[i], TEXT_MUTED[i], self.completion_progress))
            for i in range(3)
        ]
        text_color.append(int(self.current_alpha))
        
        text_surf = font_medium.render(self.text, True, text_color)
        text_rect = text_surf.get_rect(midleft=(cb_rect.right + 15, CARD_HEIGHT // 2))
        
        # Truncate text if too long
        if text_rect.right > rect.width - 50:
            clip_width = rect.width - 50 - text_rect.left
            if clip_width > 0:
                card_surf.blit(text_surf, text_rect, pygame.Rect(0, 0, clip_width, text_rect.height))
        else:
            card_surf.blit(text_surf, text_rect)
        
        # Strikethrough
        if self.completion_progress > 0.01:
            line_length = text_surf.get_width() * self.completion_progress
            if text_rect.right > rect.width - 50:
                line_length = (rect.width - 50 - text_rect.left) * self.completion_progress
            line_y = text_rect.centery
            if line_length > 0:
                pygame.draw.line(card_surf, (*TEXT_MUTED, int(self.current_alpha)), 
                                 (text_rect.left, line_y), 
                                 (text_rect.left + line_length, line_y), 2)
                             
        # Draw Delete Button
        del_color = [
            int(lerp(TEXT_MUTED[i], DELETE_COLOR[i], self.delete_hover_progress))
            for i in range(3)
        ]
        del_color.append(int(self.current_alpha * lerp(0.3, 1.0, self.delete_hover_progress)))
        
        del_surf = font_small.render("X", True, del_color)
        del_rect = del_surf.get_rect(midright=(rect.width - 20, CARD_HEIGHT // 2))
        card_surf.blit(del_surf, del_rect)

        # Blit card back to main surface
        surface.blit(card_surf, rect.topleft)
        
    def check_interaction(self, mouse_pos, x):
        if self.current_y is None:
            return False, False
        actual_x = x + int(getattr(self, 'current_x_offset', 0))
        rect = pygame.Rect(actual_x, self.current_y, WIDTH - 2 * x, CARD_HEIGHT)
        is_hovered = rect.collidepoint(mouse_pos)
        
        self.hover_progress = lerp(self.hover_progress, 1.0 if is_hovered else 0.0, EASE_SPEED)
        
        # Delete button rect absolute space
        del_rect = pygame.Rect(rect.right - 40, rect.top, 40, CARD_HEIGHT)
        del_hovered = del_rect.collidepoint(mouse_pos)
        self.delete_hover_progress = lerp(self.delete_hover_progress, 1.0 if del_hovered else 0.0, EASE_SPEED)
        
        return is_hovered, del_hovered
        
    def handle_click(self, mouse_pos, x):
        if self.current_y is None:
            return False
        actual_x = x + int(getattr(self, 'current_x_offset', 0))
        rect = pygame.Rect(actual_x, self.current_y, WIDTH - 2 * x, CARD_HEIGHT)
        if not rect.collidepoint(mouse_pos):
            return False
            
        del_rect = pygame.Rect(rect.right - 40, rect.top, 40, CARD_HEIGHT)
        if del_rect.collidepoint(mouse_pos):
            self.deleting = True
            return True
            
        cb_rect = pygame.Rect(actual_x + 10, rect.top, CHECKBOX_SIZE + 20, CARD_HEIGHT)
        if cb_rect.collidepoint(mouse_pos):
            self.completed = not self.completed
            return True
        
        # Clicking whole card also toggles completion if not clicking delete
        self.completed = not self.completed
        return True

class InputBox:
    def __init__(self, x, y, w, h):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = ""
        self.active = False
        self.cursor_visible = True
        self.cursor_timer = 0
        self.hover_progress = 0.0
        self.focus_progress = 0.0
        
    def update(self, dt):
        self.cursor_timer += dt
        if self.cursor_timer >= 0.5:
            self.cursor_visible = not self.cursor_visible
            self.cursor_timer = 0
            
        self.focus_progress = lerp(self.focus_progress, 1.0 if self.active else 0.0, EASE_SPEED)

    def draw(self, surface, mouse_pos):
        is_hovered = self.rect.collidepoint(mouse_pos)
        self.hover_progress = lerp(self.hover_progress, 1.0 if is_hovered else 0.0, EASE_SPEED)
        
        # Background
        bg_scale = lerp(0, 10, self.hover_progress)
        current_bg = (min(255, CARD_COLOR[0] + bg_scale), min(255, CARD_COLOR[1] + bg_scale), min(255, CARD_COLOR[2] + bg_scale))
        draw_rounded_rect(surface, current_bg, self.rect, CORNER_RADIUS)
        
        # Border (Accent color if active)
        if self.focus_progress > 0.01:
            border_alpha = int(255 * self.focus_progress)
            border_surf = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
            draw_rounded_rect(border_surf, (*ACCENT_COLOR, border_alpha), border_surf.get_rect(), CORNER_RADIUS)
            surface.blit(border_surf, self.rect.topleft)
            # Inner erase to show background
            draw_rounded_rect(surface, current_bg, self.rect.inflate(-4, -4), CORNER_RADIUS - 2)

        # Text rendering
        display_text = self.text if self.text or self.active else "Add a new task..."
        text_color = TEXT_COLOR if self.text or self.active else TEXT_MUTED
        txt_surface = font_medium.render(display_text, True, text_color)
        
        # Clip area for text to fit in input box
        clip_rect = pygame.Rect(self.rect.x + 20, self.rect.y, self.rect.width - 40, self.rect.height)
        surface.set_clip(clip_rect)
        
        # Scroll text if too long
        txt_x = self.rect.x + 20
        if txt_surface.get_width() > clip_rect.width - 10 and self.active:
            txt_x = clip_rect.right - txt_surface.get_width() - 10
            
        surface.blit(txt_surface, (txt_x, self.rect.centery - txt_surface.get_height() // 2))
        
        # Draw Cursor
        if self.active and self.cursor_visible:
            cursor_x = txt_x + txt_surface.get_width() + 2 if self.text else self.rect.x + 20
            pygame.draw.line(surface, ACCENT_COLOR, 
                           (cursor_x, self.rect.centery - 12), 
                           (cursor_x, self.rect.centery + 12), 2)
                           
        surface.set_clip(None)

# --- App State ---
tasks = []
input_box = InputBox(MARGIN_X, MARGIN_Y + 95, WIDTH - 2 * MARGIN_X, 60)
scroll_y = 0
target_scroll_y = 0

# Initial App Fade-in
app_fade = 255

# --- Main Loop ---
running = True
dt = 0
last_time = time.time()

while running:
    # Delta Time Calculation
    current_time = time.time()
    dt = current_time - last_time
    last_time = current_time
    # Cap dt to prevent massive jumps on lag
    if dt > 0.1:
        dt = 0.1
    
    # Event Handling
    mouse_pos = pygame.mouse.get_pos()
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1: # Left click
                input_box.active = input_box.rect.collidepoint(event.pos)
                
                # Check task clicks
                task_clicked = False
                for task in tasks:
                    if not task.deleting:
                        if task.handle_click(event.pos, MARGIN_X):
                            task_clicked = True
                            
            elif event.button == 4: # Scroll Up
                target_scroll_y += 40
            elif event.button == 5: # Scroll Down
                target_scroll_y -= 40
                
        elif event.type == pygame.KEYDOWN:
            if input_box.active:
                if event.key == pygame.K_RETURN:
                    if input_box.text.strip():
                        tasks.insert(0, Task(input_box.text.strip()))
                        input_box.text = ""
                elif event.key == pygame.K_BACKSPACE:
                    input_box.text = input_box.text[:-1]
                else:
                    if event.unicode.isprintable():
                        input_box.text += event.unicode
                        
    # Update Logic
    input_box.update(dt)
    
    # Update scroll
    max_scroll = 0
    total_task_height = len([t for t in tasks if not t.deleting]) * (CARD_HEIGHT + CARD_SPACING)
    list_start_y = MARGIN_Y + 175
    if list_start_y + total_task_height > HEIGHT - 50:
        max_scroll = -(list_start_y + total_task_height - HEIGHT + 50)
        
    target_scroll_y = max(min(target_scroll_y, 0), max_scroll)
    scroll_y = lerp(scroll_y, target_scroll_y, EASE_SPEED)
    
    # Update tasks
    active_tasks = []
    current_y = list_start_y + scroll_y
    
    # Clean dead tasks list
    tasks = [t for t in tasks if not t.is_dead]
    
    # Calculate targets
    for task in tasks:
        if not task.deleting:
            task.target_y = current_y
            current_y += CARD_HEIGHT + CARD_SPACING
            
        task.check_interaction(mouse_pos, MARGIN_X)
        task.update(dt)

    # Rendering
    screen.fill(BG_COLOR)
    
    # Title
    title_surf = font_large.render("Today", True, TEXT_COLOR)
    screen.blit(title_surf, (MARGIN_X, MARGIN_Y))
    
    active_count = len([t for t in tasks if not t.completed and not t.deleting])
    total_count = len([t for t in tasks if not t.deleting])
    
    subtitle = f"{active_count} tasks left" if active_count > 0 else "All done!"
    if total_count == 0:
        subtitle = "No tasks yet"
        
    sub_surf = font_medium.render(subtitle, True, ACCENT_COLOR if active_count == 0 and total_count > 0 else TEXT_MUTED)
    screen.blit(sub_surf, (MARGIN_X, MARGIN_Y + 55))
    
    # Input Box
    input_box.draw(screen, mouse_pos)
    
    # Progress Bar (Top)
    if total_count > 0:
        comp_ratio = (total_count - active_count) / total_count
        prog_w = WIDTH * comp_ratio
        
        # Smooth progress bar width update can be done here if needed
        pygame.draw.rect(screen, COMPLETED_COLOR, (0, 0, WIDTH, 4))
        pygame.draw.rect(screen, ACCENT_COLOR, (0, 0, prog_w, 4))
    
    # Tasks list clipping area
    list_clip_rect = pygame.Rect(0, list_start_y, WIDTH, HEIGHT - list_start_y)
    screen.set_clip(list_clip_rect)
    
    for task in reversed(tasks): # Draw from bottom to top so newer tasks can slide over
        task.draw(screen, MARGIN_X)
        
    # Remove clip
    screen.set_clip(None)

    # Initial Fade in effect
    if app_fade > 0:
        fade_surf = pygame.Surface((WIDTH, HEIGHT))
        fade_surf.fill(BG_COLOR)
        fade_surf.set_alpha(int(app_fade))
        screen.blit(fade_surf, (0, 0))
        app_fade -= 5 * dt * 60
        if app_fade < 0:
            app_fade = 0

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
sys.exit()
