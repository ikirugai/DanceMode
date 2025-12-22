"""
DanceMode Main Game Module
Interactive dance game where players follow on-screen dance moves.
"""

import pygame
import cv2
import math
import sys
import random
from typing import List, Optional, Tuple
from enum import Enum

from player_detection import PlayerDetector, PlayerLandmarks
from dance_targets import DanceTargetManager, DanceLibrary
from dancer_avatar import DancerAvatar, TargetRenderer, DancerColors


# Fun color palette for DanceMode
class DancePalette:
    # Backgrounds
    BG_DARK = (30, 20, 50)
    BG_PURPLE = (60, 30, 80)
    BG_GRADIENT_TOP = (40, 20, 60)
    BG_GRADIENT_BOTTOM = (80, 40, 100)

    # UI Colors
    WHITE = (255, 255, 255)
    BLACK = (30, 30, 40)
    GOLD = (255, 215, 0)
    SILVER = (192, 192, 192)

    # Accent colors
    PINK = (255, 100, 150)
    CYAN = (100, 255, 255)
    YELLOW = (255, 255, 100)
    GREEN = (100, 255, 150)
    ORANGE = (255, 180, 100)


class GameState(Enum):
    """Game state machine states."""
    MENU = "menu"
    DANCE_SELECT = "dance_select"
    COUNTDOWN = "countdown"
    PLAYING = "playing"
    RESULTS = "results"
    PAUSED = "paused"


class DanceModeGame:
    """
    Main game class for DanceMode.
    An interactive dance game with motion tracking.
    """

    def __init__(self, width: int = 1280, height: int = 720,
                 fullscreen: bool = False, show_camera: bool = True):
        """Initialize the game."""
        pygame.init()
        pygame.mixer.init()

        self.width = width
        self.height = height

        # Set up display
        flags = pygame.DOUBLEBUF
        if fullscreen:
            flags |= pygame.FULLSCREEN
            info = pygame.display.Info()
            self.width = info.current_w
            self.height = info.current_h

        self.screen = pygame.display.set_mode((self.width, self.height), flags)
        pygame.display.set_caption("DanceMode! - Follow the Moves!")

        # Clock
        self.clock = pygame.time.Clock()
        self.target_fps = 60

        # Game components
        self.player_detector = PlayerDetector()
        self.dance_manager = DanceTargetManager(self.width, self.height)
        self.dancer_avatar = DancerAvatar(self.width, self.height)
        self.target_renderer = TargetRenderer()

        # Fonts
        self.font_large = pygame.font.Font(None, 72)
        self.font_medium = pygame.font.Font(None, 48)
        self.font_small = pygame.font.Font(None, 32)

        # Game state
        self.state = GameState.MENU
        self.countdown_timer = 3.0
        self.selected_dance_index = 0
        self.available_dances = DanceLibrary.get_all_sequences()

        # Camera
        self.camera_ready = False
        self.show_camera = show_camera
        self.cached_players = []

        # Visual effects
        self.bg_hue = 0
        self.stars = self._create_stars(50)
        self.disco_time = 0

        # Sounds
        self._init_sounds()

    def _create_stars(self, count: int) -> List[dict]:
        """Create background stars for disco effect."""
        stars = []
        for _ in range(count):
            stars.append({
                'x': random.randint(0, self.width),
                'y': random.randint(0, self.height),
                'size': random.randint(2, 5),
                'speed': random.random() * 2 + 1,
                'brightness': random.random(),
            })
        return stars

    def _init_sounds(self):
        """Initialize sound effects."""
        self.sounds = {}
        try:
            sample_rate = 44100

            # Hit sound (happy boop)
            hit_duration = 0.15
            hit_samples = int(sample_rate * hit_duration)
            hit_sound = pygame.mixer.Sound(
                buffer=bytes([
                    int(128 + 100 * math.sin(2 * math.pi * 660 * t / sample_rate) *
                        (1 - t / hit_samples))
                    for t in range(hit_samples)
                ])
            )
            self.sounds['hit'] = hit_sound

            # Miss sound
            miss_duration = 0.2
            miss_samples = int(sample_rate * miss_duration)
            miss_sound = pygame.mixer.Sound(
                buffer=bytes([
                    int(128 + 60 * math.sin(2 * math.pi * 200 * t / sample_rate) *
                        (1 - t / miss_samples))
                    for t in range(miss_samples)
                ])
            )
            self.sounds['miss'] = miss_sound

            # Countdown beep
            beep_duration = 0.1
            beep_samples = int(sample_rate * beep_duration)
            beep_sound = pygame.mixer.Sound(
                buffer=bytes([
                    int(128 + 80 * math.sin(2 * math.pi * 880 * t / sample_rate) *
                        (1 - t / beep_samples))
                    for t in range(beep_samples)
                ])
            )
            self.sounds['beep'] = beep_sound

            # Success fanfare
            success_duration = 0.4
            success_samples = int(sample_rate * success_duration)
            success_sound = pygame.mixer.Sound(
                buffer=bytes([
                    int(128 + 80 * math.sin(2 * math.pi * (440 + t * 0.5) * t / sample_rate) *
                        max(0, 1 - t / success_samples))
                    for t in range(success_samples)
                ])
            )
            self.sounds['success'] = success_sound

        except Exception as e:
            print(f"Warning: Could not initialize sounds: {e}")
            self.sounds = {}

    def _play_sound(self, name: str):
        """Play a sound effect."""
        if name in self.sounds:
            try:
                self.sounds[name].play()
            except:
                pass

    def start(self):
        """Start the game."""
        print("Starting DanceMode!")
        print("Initializing camera...")

        self.camera_ready = self.player_detector.start()
        if not self.camera_ready:
            print("Warning: Camera not available.")

        self.run()

    def run(self):
        """Main game loop."""
        running = True

        while running:
            dt = self.clock.tick(self.target_fps) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    running = self._handle_keydown(event.key)

            # Detect players
            if self.camera_ready:
                self.cached_players = self.player_detector.detect_players(
                    self.width, self.height)

            # Update
            self._update(dt)

            # Render
            self._render()

            # Camera preview
            self._show_camera_preview()

            pygame.display.flip()

        self._cleanup()

    def _handle_keydown(self, key: int) -> bool:
        """Handle keyboard input."""
        if key == pygame.K_ESCAPE:
            if self.state == GameState.PLAYING:
                self.state = GameState.PAUSED
            elif self.state == GameState.PAUSED:
                self.state = GameState.PLAYING
            elif self.state in [GameState.MENU, GameState.DANCE_SELECT]:
                return False
            else:
                self.state = GameState.MENU

        elif key == pygame.K_SPACE:
            if self.state == GameState.MENU:
                self.state = GameState.DANCE_SELECT
            elif self.state == GameState.DANCE_SELECT:
                self._start_countdown()
            elif self.state == GameState.RESULTS:
                self.state = GameState.MENU
            elif self.state == GameState.PAUSED:
                self.state = GameState.PLAYING

        elif key == pygame.K_LEFT:
            if self.state == GameState.DANCE_SELECT:
                self.selected_dance_index = (self.selected_dance_index - 1) % len(self.available_dances)
                self._play_sound('beep')

        elif key == pygame.K_RIGHT:
            if self.state == GameState.DANCE_SELECT:
                self.selected_dance_index = (self.selected_dance_index + 1) % len(self.available_dances)
                self._play_sound('beep')

        elif key == pygame.K_r:
            if self.state in [GameState.RESULTS, GameState.PAUSED]:
                self._start_countdown()

        return True

    def _start_countdown(self):
        """Start countdown before dance."""
        self.state = GameState.COUNTDOWN
        self.countdown_timer = 3.0
        selected_dance = self.available_dances[self.selected_dance_index]
        self.dance_manager.start_sequence(selected_dance)
        self._play_sound('beep')

    def _update(self, dt: float):
        """Update game logic."""
        # Update visual effects
        self.disco_time += dt
        self.bg_hue = (self.bg_hue + dt * 10) % 360

        # Update stars
        for star in self.stars:
            star['brightness'] = (math.sin(self.disco_time * star['speed']) + 1) / 2

        # State updates
        if self.state == GameState.COUNTDOWN:
            self._update_countdown(dt)
        elif self.state == GameState.PLAYING:
            self._update_playing(dt)

    def _update_countdown(self, dt: float):
        """Update countdown."""
        prev_second = int(self.countdown_timer)
        self.countdown_timer -= dt
        new_second = int(self.countdown_timer)

        if new_second < prev_second and new_second >= 0:
            self._play_sound('beep')

        if self.countdown_timer <= 0:
            self.state = GameState.PLAYING

    def _update_playing(self, dt: float):
        """Update gameplay."""
        # Get player hand positions
        left_hand = None
        right_hand = None

        if self.cached_players:
            player = self.cached_players[0]  # Primary player
            left_hand = player.left_hand
            right_hand = player.right_hand

        # Update dance manager
        events = self.dance_manager.update(dt, left_hand, right_hand)

        # Handle events
        if events['hit']:
            self._play_sound('hit')
        if events['miss']:
            self._play_sound('miss')
        if events['sequence_complete']:
            self._play_sound('success')
            self.state = GameState.RESULTS

    def _render(self):
        """Render the game."""
        # Draw disco background
        self._draw_disco_background()

        # State-specific rendering
        if self.state == GameState.MENU:
            self._render_menu()
        elif self.state == GameState.DANCE_SELECT:
            self._render_dance_select()
        elif self.state == GameState.COUNTDOWN:
            self._render_countdown()
        elif self.state == GameState.PLAYING:
            self._render_playing()
        elif self.state == GameState.RESULTS:
            self._render_results()
        elif self.state == GameState.PAUSED:
            self._render_playing()
            self._render_pause_overlay()

    def _draw_disco_background(self):
        """Draw animated disco background."""
        # Gradient background
        for y in range(self.height):
            ratio = y / self.height
            r = int(DancePalette.BG_GRADIENT_TOP[0] * (1 - ratio) +
                   DancePalette.BG_GRADIENT_BOTTOM[0] * ratio)
            g = int(DancePalette.BG_GRADIENT_TOP[1] * (1 - ratio) +
                   DancePalette.BG_GRADIENT_BOTTOM[1] * ratio)
            b = int(DancePalette.BG_GRADIENT_TOP[2] * (1 - ratio) +
                   DancePalette.BG_GRADIENT_BOTTOM[2] * ratio)
            pygame.draw.line(self.screen, (r, g, b), (0, y), (self.width, y))

        # Disco stars
        for star in self.stars:
            brightness = int(star['brightness'] * 200 + 55)
            color = (brightness, brightness, brightness)
            pygame.draw.circle(self.screen, color,
                             (star['x'], star['y']), star['size'])

        # Disco floor lines
        floor_y = self.height - 100
        for i in range(20):
            x = (i * 100 + int(self.disco_time * 50)) % (self.width + 200) - 100
            alpha = 100 + int(math.sin(i + self.disco_time) * 50)
            color = (alpha, alpha // 2, alpha)
            pygame.draw.line(self.screen, color, (x, floor_y), (x + 50, self.height), 3)

    def _render_menu(self):
        """Render main menu."""
        # Title
        title = self.font_large.render("DanceMode!", True, DancePalette.PINK)
        title_glow = self.font_large.render("DanceMode!", True, DancePalette.CYAN)
        title_rect = title.get_rect(center=(self.width // 2, self.height // 3))

        # Glow effect
        self.screen.blit(title_glow, (title_rect.x + 3, title_rect.y + 3))
        self.screen.blit(title, title_rect)

        # Subtitle
        subtitle = self.font_medium.render("Follow the dance moves!", True, DancePalette.WHITE)
        sub_rect = subtitle.get_rect(center=(self.width // 2, self.height // 3 + 60))
        self.screen.blit(subtitle, sub_rect)

        # Camera status
        if self.camera_ready:
            status_text = f"Camera ready! {len(self.cached_players)} player(s) detected"
            status_color = DancePalette.GREEN
        else:
            status_text = "No camera detected"
            status_color = DancePalette.ORANGE

        status = self.font_small.render(status_text, True, status_color)
        status_rect = status.get_rect(center=(self.width // 2, self.height // 2 + 20))
        self.screen.blit(status, status_rect)

        # Start prompt
        pulse = abs(math.sin(self.disco_time * 3)) * 0.3 + 0.7
        prompt_color = tuple(int(c * pulse) for c in DancePalette.YELLOW)
        prompt = self.font_medium.render("Press SPACE to Start", True, prompt_color)
        prompt_rect = prompt.get_rect(center=(self.width // 2, self.height * 2 // 3))
        self.screen.blit(prompt, prompt_rect)

        # Render dancers if detected
        for i, player in enumerate(self.cached_players[:4]):
            self.dancer_avatar.render_player(self.screen, player, i)

    def _render_dance_select(self):
        """Render dance selection screen."""
        # Title
        title = self.font_large.render("Choose Your Dance!", True, DancePalette.CYAN)
        title_rect = title.get_rect(center=(self.width // 2, 80))
        self.screen.blit(title, title_rect)

        # Dance options
        for i, dance in enumerate(self.available_dances):
            y_pos = 180 + i * 80

            if i == self.selected_dance_index:
                # Selected dance
                color = DancePalette.YELLOW
                pygame.draw.rect(self.screen, DancePalette.PINK,
                               (self.width // 4, y_pos - 30, self.width // 2, 60),
                               border_radius=10)
                prefix = "> "
            else:
                color = DancePalette.WHITE
                prefix = "  "

            dance_text = f"{prefix}{dance.name}"
            diff_stars = "*" * dance.difficulty
            full_text = f"{dance_text}  {diff_stars}"

            text = self.font_medium.render(full_text, True, color)
            text_rect = text.get_rect(center=(self.width // 2, y_pos))
            self.screen.blit(text, text_rect)

        # Instructions
        instr = self.font_small.render("LEFT/RIGHT to select, SPACE to start", True, DancePalette.WHITE)
        instr_rect = instr.get_rect(center=(self.width // 2, self.height - 50))
        self.screen.blit(instr, instr_rect)

        # Render dancers
        for i, player in enumerate(self.cached_players[:4]):
            self.dancer_avatar.render_player(self.screen, player, i)

    def _render_countdown(self):
        """Render countdown."""
        # Render dancers
        for i, player in enumerate(self.cached_players[:4]):
            self.dancer_avatar.render_player(self.screen, player, i)

        # Countdown number
        count = max(1, int(self.countdown_timer) + 1)
        if self.countdown_timer <= 0:
            count_text = "GO!"
            color = DancePalette.GREEN
        else:
            count_text = str(count)
            color = DancePalette.YELLOW

        # Scale effect
        scale = 1.0 + (self.countdown_timer % 1.0) * 0.5
        font_size = int(120 * scale)
        countdown_font = pygame.font.Font(None, font_size)

        text = countdown_font.render(count_text, True, color)
        text_rect = text.get_rect(center=(self.width // 2, self.height // 2))

        # Glow
        glow = countdown_font.render(count_text, True, DancePalette.WHITE)
        self.screen.blit(glow, (text_rect.x + 4, text_rect.y + 4))
        self.screen.blit(text, text_rect)

        # Dance name
        dance = self.available_dances[self.selected_dance_index]
        name = self.font_medium.render(f"Get ready for: {dance.name}!", True, DancePalette.PINK)
        name_rect = name.get_rect(center=(self.width // 2, self.height // 3))
        self.screen.blit(name, name_rect)

    def _render_playing(self):
        """Render gameplay."""
        # Render dancers
        for i, player in enumerate(self.cached_players[:4]):
            self.dancer_avatar.render_player(self.screen, player, i)

        # Render targets
        left_target, right_target = self.dance_manager.get_target_positions()
        time_progress = self.dance_manager.get_time_progress()

        self.target_renderer.render_targets(
            self.screen, left_target, right_target,
            self.dance_manager.left_hand_hit,
            self.dance_manager.right_hand_hit,
            time_progress
        )

        # Draw countdown rings around targets
        time_remaining = self.dance_manager.get_time_remaining()
        if left_target:
            self.target_renderer.render_countdown_ring(
                self.screen, left_target, time_remaining, 2.0)
        if right_target:
            self.target_renderer.render_countdown_ring(
                self.screen, right_target, time_remaining, 2.0)

        # Current move instruction
        move = self.dance_manager.get_current_move()
        if move:
            instr = self.font_medium.render(move.description, True, DancePalette.WHITE)
            instr_rect = instr.get_rect(center=(self.width // 2, 50))
            self.screen.blit(instr, instr_rect)

        # Score and stats
        stats = self.dance_manager.get_stats()

        score_text = f"Score: {stats['score']}"
        score = self.font_medium.render(score_text, True, DancePalette.GOLD)
        self.screen.blit(score, (20, 20))

        streak_text = f"Streak: {stats['current_streak']}"
        streak_color = DancePalette.PINK if stats['current_streak'] >= 3 else DancePalette.WHITE
        streak = self.font_small.render(streak_text, True, streak_color)
        self.screen.blit(streak, (20, 70))

        dance_name = self.font_small.render(stats['dance_name'], True, DancePalette.CYAN)
        self.screen.blit(dance_name, (self.width - 200, 20))

    def _render_results(self):
        """Render results screen."""
        # Overlay
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        stats = self.dance_manager.get_stats()

        # Title
        title = self.font_large.render("Dance Complete!", True, DancePalette.PINK)
        title_rect = title.get_rect(center=(self.width // 2, self.height // 4))
        self.screen.blit(title, title_rect)

        # Score
        score_text = f"Final Score: {stats['score']}"
        score = self.font_large.render(score_text, True, DancePalette.GOLD)
        score_rect = score.get_rect(center=(self.width // 2, self.height // 2 - 40))
        self.screen.blit(score, score_rect)

        # Stats
        stats_lines = [
            f"Moves Hit: {stats['moves_hit']}",
            f"Moves Missed: {stats['moves_missed']}",
            f"Accuracy: {stats['accuracy']:.0f}%",
            f"Best Streak: {stats['best_streak']}",
        ]

        for i, line in enumerate(stats_lines):
            text = self.font_small.render(line, True, DancePalette.WHITE)
            text_rect = text.get_rect(center=(self.width // 2, self.height // 2 + 40 + i * 35))
            self.screen.blit(text, text_rect)

        # Rating
        accuracy = stats['accuracy']
        if accuracy >= 90:
            rating = "SUPERSTAR!"
            rating_color = DancePalette.GOLD
        elif accuracy >= 70:
            rating = "Great Moves!"
            rating_color = DancePalette.PINK
        elif accuracy >= 50:
            rating = "Good Try!"
            rating_color = DancePalette.CYAN
        else:
            rating = "Keep Practicing!"
            rating_color = DancePalette.WHITE

        rating_text = self.font_large.render(rating, True, rating_color)
        rating_rect = rating_text.get_rect(center=(self.width // 2, self.height * 3 // 4))
        self.screen.blit(rating_text, rating_rect)

        # Continue prompt
        prompt = self.font_small.render("Press SPACE for menu, R to replay", True, DancePalette.WHITE)
        prompt_rect = prompt.get_rect(center=(self.width // 2, self.height - 50))
        self.screen.blit(prompt, prompt_rect)

    def _render_pause_overlay(self):
        """Render pause overlay."""
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        pause_text = self.font_large.render("PAUSED", True, DancePalette.WHITE)
        pause_rect = pause_text.get_rect(center=(self.width // 2, self.height // 2))
        self.screen.blit(pause_text, pause_rect)

        resume = self.font_small.render("Press SPACE or ESC to Resume", True, DancePalette.CYAN)
        resume_rect = resume.get_rect(center=(self.width // 2, self.height // 2 + 60))
        self.screen.blit(resume, resume_rect)

    def _show_camera_preview(self):
        """Show camera preview window."""
        if not self.show_camera or not self.camera_ready:
            return

        frame = self.player_detector.last_frame
        if frame is not None:
            display_frame = frame.copy()
            h, w = display_frame.shape[:2]

            players = self.cached_players
            scale_x = w / self.width
            scale_y = h / self.height

            player_colors = [
                (255, 100, 150),
                (100, 200, 255),
                (150, 255, 100),
                (255, 200, 100),
            ]

            def scale_pt(pt):
                if pt is None:
                    return None
                return (int(pt[0] * scale_x), int(pt[1] * scale_y))

            for i, player in enumerate(players):
                color = player_colors[i % len(player_colors)]

                connections = [
                    ('left_shoulder', 'right_shoulder'),
                    ('left_shoulder', 'left_elbow'),
                    ('left_elbow', 'left_hand'),
                    ('right_shoulder', 'right_elbow'),
                    ('right_elbow', 'right_hand'),
                    ('left_shoulder', 'left_hip'),
                    ('right_shoulder', 'right_hip'),
                    ('left_hip', 'right_hip'),
                ]

                for start_name, end_name in connections:
                    start_pt = scale_pt(getattr(player, start_name, None))
                    end_pt = scale_pt(getattr(player, end_name, None))
                    if start_pt and end_pt:
                        cv2.line(display_frame, start_pt, end_pt, color, 3)

                joints = ['nose', 'left_shoulder', 'right_shoulder', 'left_elbow',
                         'right_elbow', 'left_hand', 'right_hand', 'left_hip', 'right_hip']

                for joint_name in joints:
                    pt = scale_pt(getattr(player, joint_name, None))
                    if pt:
                        radius = 15 if 'hand' in joint_name else 6
                        cv2.circle(display_frame, pt, radius, color, -1)
                        cv2.circle(display_frame, pt, radius, (255, 255, 255), 2)

            # Status
            cv2.putText(display_frame, f"DanceMode - {len(players)} player(s)",
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

            bounds = self.player_detector.get_detection_bounds(w, h)
            cv2.rectangle(display_frame,
                         (bounds[0], bounds[1]),
                         (bounds[0] + bounds[2], bounds[1] + bounds[3]),
                         (0, 255, 0), 2)

            cv2.imshow("DanceMode - Camera", display_frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                self.show_camera = False
                cv2.destroyWindow("DanceMode - Camera")

    def _cleanup(self):
        """Clean up resources."""
        print("Shutting down...")
        self.player_detector.stop()
        cv2.destroyAllWindows()
        pygame.quit()


def main():
    """Entry point for the game."""
    import argparse

    parser = argparse.ArgumentParser(description="DanceMode - Interactive Dance Game")
    parser.add_argument('--width', type=int, default=1280,
                       help='Screen width (default: 1280)')
    parser.add_argument('--height', type=int, default=720,
                       help='Screen height (default: 720)')
    parser.add_argument('--fullscreen', action='store_true',
                       help='Run in fullscreen mode')
    parser.add_argument('--no-camera-preview', action='store_true',
                       help='Hide the camera preview window')

    args = parser.parse_args()

    game = DanceModeGame(
        width=args.width,
        height=args.height,
        fullscreen=args.fullscreen,
        show_camera=not args.no_camera_preview
    )
    game.start()


if __name__ == '__main__':
    main()
