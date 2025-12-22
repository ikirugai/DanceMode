"""
KeepyUppy Main Game Module
The core game logic that ties together all components.
"""

import pygame
import cv2
import math
import sys
from typing import List, Optional, Tuple
from enum import Enum

from player_detection import PlayerDetector, PlayerLandmarks
from balloon import BalloonPhysics
from avatar import AvatarRenderer, BlueyColors
from scoring import ScoringSystem
from assets_generator import AssetGenerator, Palette, create_game_font


class GameState(Enum):
    """Game state machine states."""
    TITLE = "title"
    COUNTDOWN = "countdown"
    PLAYING = "playing"
    GAME_OVER = "game_over"
    PAUSED = "paused"


class KeepyUppyGame:
    """
    Main game class for KeepyUppy.
    A motion-controlled balloon keeping game with Bluey-inspired graphics.
    """

    def __init__(self, width: int = 1280, height: int = 720, fullscreen: bool = False, show_camera: bool = True):
        """
        Initialize the game.

        Args:
            width: Screen width
            height: Screen height
            fullscreen: Whether to run in fullscreen mode
            show_camera: Whether to show camera preview window
        """
        # Initialize pygame
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
        pygame.display.set_caption("KeepyUppy! - Keep the Balloon in the Air!")

        # Initialize clock for consistent framerate
        self.clock = pygame.time.Clock()
        self.target_fps = 60

        # Initialize game components
        self.player_detector = PlayerDetector()
        self.balloon = BalloonPhysics(self.width, self.height)
        self.avatar_renderer = AvatarRenderer(self.width, self.height)
        self.scoring = ScoringSystem()

        # Generate assets
        self.asset_gen = AssetGenerator(self.width, self.height)
        self.assets = self.asset_gen.generate_all()

        # Fonts
        self.font_large = create_game_font(72)
        self.font_medium = create_game_font(48)
        self.font_small = create_game_font(32)

        # Game state
        self.state = GameState.TITLE
        self.countdown_timer = 3.0
        self.game_over_timer = 0.0
        self.new_high_score = False

        # Cloud positions (decorative)
        self.clouds = [
            {'x': 100, 'y': 80, 'speed': 15, 'asset': 'cloud1'},
            {'x': 400, 'y': 120, 'speed': 20, 'asset': 'cloud2'},
            {'x': 800, 'y': 60, 'speed': 12, 'asset': 'cloud1'},
            {'x': 1100, 'y': 140, 'speed': 18, 'asset': 'cloud2'},
        ]

        # Track previous hand positions for velocity calculation
        self.prev_hand_positions = {}

        # Camera status
        self.camera_ready = False
        self.show_camera = show_camera
        self.cached_players = []  # Cache detected players to avoid double detection

        # Sound effects (simple beeps using pygame)
        self._init_sounds()

    def _init_sounds(self):
        """Initialize sound effects."""
        self.sounds = {}
        try:
            # Generate simple sounds programmatically
            sample_rate = 44100

            # Hit sound (short boop)
            hit_duration = 0.1
            hit_samples = int(sample_rate * hit_duration)
            hit_sound = pygame.mixer.Sound(
                buffer=bytes([
                    int(128 + 100 * math.sin(2 * math.pi * 440 * t / sample_rate) *
                        (1 - t / hit_samples))
                    for t in range(hit_samples)
                ])
            )
            self.sounds['hit'] = hit_sound

            # Pop sound
            pop_duration = 0.2
            pop_samples = int(sample_rate * pop_duration)
            pop_sound = pygame.mixer.Sound(
                buffer=bytes([
                    int(128 + 100 * math.sin(2 * math.pi * (200 + t * 2) * t / sample_rate) *
                        max(0, 1 - t / pop_samples))
                    for t in range(pop_samples)
                ])
            )
            self.sounds['pop'] = pop_sound

            # Countdown beep
            beep_duration = 0.15
            beep_samples = int(sample_rate * beep_duration)
            beep_sound = pygame.mixer.Sound(
                buffer=bytes([
                    int(128 + 80 * math.sin(2 * math.pi * 880 * t / sample_rate) *
                        (1 - t / beep_samples))
                    for t in range(beep_samples)
                ])
            )
            self.sounds['beep'] = beep_sound

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
        """Start the game (initialize camera and enter main loop)."""
        print("Starting KeepyUppy!")
        print("Initializing camera...")

        self.camera_ready = self.player_detector.start()
        if not self.camera_ready:
            print("Warning: Camera not available. Running in demo mode.")

        self.run()

    def run(self):
        """Main game loop."""
        running = True

        while running:
            # Calculate delta time
            dt = self.clock.tick(self.target_fps) / 1000.0

            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    running = self._handle_keydown(event.key)

            # Update game state
            self._update(dt)

            # Render
            self._render()

            # Show camera preview window
            self._show_camera_preview()

            # Update display
            pygame.display.flip()

        self._cleanup()

    def _handle_keydown(self, key: int) -> bool:
        """
        Handle keyboard input.

        Returns:
            False if game should quit, True otherwise
        """
        if key == pygame.K_ESCAPE:
            if self.state == GameState.PLAYING:
                self.state = GameState.PAUSED
            elif self.state == GameState.PAUSED:
                self.state = GameState.PLAYING
            else:
                return False  # Quit game

        elif key == pygame.K_SPACE:
            if self.state == GameState.TITLE:
                self._start_countdown()
            elif self.state == GameState.GAME_OVER:
                self._start_countdown()
            elif self.state == GameState.PAUSED:
                self.state = GameState.PLAYING

        elif key == pygame.K_r:
            if self.state in [GameState.GAME_OVER, GameState.PAUSED]:
                self._start_countdown()

        return True

    def _start_countdown(self):
        """Start the countdown before gameplay."""
        self.state = GameState.COUNTDOWN
        self.countdown_timer = 3.0
        self.balloon.reset()
        self.scoring.start_game()
        self._play_sound('beep')

    def _update(self, dt: float):
        """Update game logic."""
        # Always detect players for camera preview (do this once per frame)
        if self.camera_ready:
            self.cached_players = self.player_detector.detect_players(self.width, self.height)

        # Update clouds (always moving for ambiance)
        for cloud in self.clouds:
            cloud['x'] += cloud['speed'] * dt
            if cloud['x'] > self.width + 150:
                cloud['x'] = -150

        # State-specific updates
        if self.state == GameState.COUNTDOWN:
            self._update_countdown(dt)
        elif self.state == GameState.PLAYING:
            self._update_playing(dt)
        elif self.state == GameState.GAME_OVER:
            self._update_game_over(dt)

    def _update_countdown(self, dt: float):
        """Update countdown state."""
        prev_second = int(self.countdown_timer)
        self.countdown_timer -= dt
        new_second = int(self.countdown_timer)

        # Play beep on each second
        if new_second < prev_second and new_second >= 0:
            self._play_sound('beep')

        if self.countdown_timer <= 0:
            self.state = GameState.PLAYING
            self.balloon.reset()

    def _update_playing(self, dt: float):
        """Update main gameplay."""
        # Update balloon physics
        self.balloon.update(dt)

        # Update score
        self.scoring.update(dt)

        # Handle player collisions (players already detected in _update)
        if self.camera_ready and self.cached_players:
            self._handle_player_collisions(self.cached_players, dt)

        # Check for game over
        if self.balloon.is_popped:
            self._play_sound('pop')
            self.new_high_score = self.scoring.end_game()
            self.state = GameState.GAME_OVER
            self.game_over_timer = 0.0

    def _handle_player_collisions(self, players: List[PlayerLandmarks], dt: float):
        """Handle collisions between players and balloon."""
        collision_radius = self.avatar_renderer.get_collision_radius()

        for i, player in enumerate(players):
            # Get all collision points from player
            collision_points = player.get_collision_points()

            for point in collision_points:
                if point is None:
                    continue

                # Check collision
                if self.balloon.check_collision(point, collision_radius):
                    # Calculate hand velocity for better hit response
                    point_key = f"p{i}_{point[0]:.0f}_{point[1]:.0f}"
                    velocity = (0.0, 0.0)

                    if point_key in self.prev_hand_positions:
                        prev = self.prev_hand_positions[point_key]
                        velocity = (
                            (point[0] - prev[0]) / max(dt, 0.001),
                            (point[1] - prev[1]) / max(dt, 0.001)
                        )

                    # Apply hit
                    self.balloon.apply_hit(point, velocity)
                    self.scoring.record_hit()
                    self._play_sound('hit')

                    # Update previous position
                    self.prev_hand_positions[point_key] = point

    def _update_game_over(self, dt: float):
        """Update game over state."""
        self.game_over_timer += dt

    def _render(self):
        """Render the game."""
        # Draw background
        self.screen.blit(self.assets['background'], (0, 0))

        # Draw sun
        self.screen.blit(self.assets['sun'], (self.width - 150, 20))

        # Draw clouds
        for cloud in self.clouds:
            self.screen.blit(self.assets[cloud['asset']],
                           (int(cloud['x']), cloud['y']))

        # State-specific rendering
        if self.state == GameState.TITLE:
            self._render_title()
        elif self.state == GameState.COUNTDOWN:
            self._render_countdown()
            self._render_players()
        elif self.state == GameState.PLAYING:
            self._render_gameplay()
        elif self.state == GameState.GAME_OVER:
            self._render_game_over()
        elif self.state == GameState.PAUSED:
            self._render_gameplay()
            self._render_pause_overlay()

    def _render_title(self):
        """Render title screen."""
        # Title
        title_text = self.font_large.render("KeepyUppy!", True, Palette.DEEP_BLUE)
        title_shadow = self.font_large.render("KeepyUppy!", True, Palette.NAVY)
        title_rect = title_text.get_rect(center=(self.width // 2, self.height // 3))

        self.screen.blit(title_shadow, (title_rect.x + 4, title_rect.y + 4))
        self.screen.blit(title_text, title_rect)

        # Subtitle
        subtitle = self.font_medium.render("Keep the Balloon in the Air!", True,
                                          Palette.ORANGE)
        subtitle_rect = subtitle.get_rect(center=(self.width // 2,
                                                  self.height // 3 + 70))
        self.screen.blit(subtitle, subtitle_rect)

        # Instructions
        if self.camera_ready:
            instr_text = "Wave your hands to hit the balloon!"
        else:
            instr_text = "Camera not detected - Demo mode"

        instr = self.font_small.render(instr_text, True, Palette.BLACK)
        instr_rect = instr.get_rect(center=(self.width // 2, self.height // 2 + 50))
        self.screen.blit(instr, instr_rect)

        # Start prompt
        start_text = "Press SPACE to Start"
        # Pulsing effect
        pulse = abs(math.sin(pygame.time.get_ticks() / 500)) * 0.3 + 0.7
        start_color = tuple(int(c * pulse) for c in Palette.DEEP_BLUE)
        start = self.font_medium.render(start_text, True, start_color)
        start_rect = start.get_rect(center=(self.width // 2, self.height * 2 // 3))
        self.screen.blit(start, start_rect)

        # High score
        high_score = self.scoring.get_high_score_formatted()
        hs_text = self.font_small.render(f"Best Time: {high_score}", True,
                                        Palette.WARM_YELLOW)
        hs_rect = hs_text.get_rect(center=(self.width // 2, self.height - 80))
        self.screen.blit(hs_text, hs_rect)

        # Draw decorative balloon
        balloon_x = self.width // 2 - 50 + math.sin(pygame.time.get_ticks() / 1000) * 30
        balloon_y = self.height // 2 - 100 + math.cos(pygame.time.get_ticks() / 800) * 20
        self.screen.blit(self.assets['balloon'], (int(balloon_x), int(balloon_y)))

    def _render_countdown(self):
        """Render countdown overlay."""
        # Semi-transparent overlay
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((255, 255, 255, 100))
        self.screen.blit(overlay, (0, 0))

        # Countdown number
        count = max(1, int(self.countdown_timer) + 1)
        if self.countdown_timer <= 0:
            count_text = "GO!"
            color = Palette.GRASS_GREEN
        else:
            count_text = str(count)
            color = Palette.ORANGE

        # Scaling effect
        scale = 1.0 + (self.countdown_timer % 1.0) * 0.3
        font_size = int(120 * scale)
        try:
            countdown_font = create_game_font(font_size)
        except:
            countdown_font = self.font_large

        text = countdown_font.render(count_text, True, color)
        shadow = countdown_font.render(count_text, True, Palette.NAVY)
        rect = text.get_rect(center=(self.width // 2, self.height // 2))

        self.screen.blit(shadow, (rect.x + 4, rect.y + 4))
        self.screen.blit(text, rect)

    def _render_players(self):
        """Render detected players."""
        if not self.camera_ready:
            return

        players = self.player_detector.detect_players(self.width, self.height)
        for i, player in enumerate(players):
            self.avatar_renderer.render_player(self.screen, player, i)

    def _render_gameplay(self):
        """Render main gameplay."""
        # Render players first (behind balloon)
        self._render_players()

        # Render balloon
        balloon_info = self.balloon.get_render_info()
        if not balloon_info['is_popped']:
            balloon_surf = self.assets['balloon']
            # Apply wobble rotation
            wobble = balloon_info['wobble']
            rotated = pygame.transform.rotate(balloon_surf, wobble)
            rect = rotated.get_rect(center=(int(balloon_info['x']),
                                           int(balloon_info['y'])))
            self.screen.blit(rotated, rect)

        # Render wind indicator if active
        wind_info = self.balloon.get_wind_indicator()
        if wind_info:
            self._render_wind_indicator(wind_info)

        # Render score UI
        self._render_score_ui()

    def _render_wind_indicator(self, wind_info: Tuple[float, float, float]):
        """Render wind direction indicator."""
        direction, strength, remaining = wind_info

        # Position in top-left area
        indicator_x = 100
        indicator_y = 100

        # Rotate wind arrow
        angle_degrees = -math.degrees(direction)
        rotated_arrow = pygame.transform.rotate(self.assets['wind_arrow'],
                                               angle_degrees)
        rect = rotated_arrow.get_rect(center=(indicator_x, indicator_y))

        # Fade based on remaining time
        alpha = int(255 * remaining)
        rotated_arrow.set_alpha(alpha)

        self.screen.blit(rotated_arrow, rect)

        # Wind text
        wind_text = self.font_small.render("WIND!", True, Palette.DEEP_BLUE)
        wind_text.set_alpha(alpha)
        text_rect = wind_text.get_rect(center=(indicator_x, indicator_y + 50))
        self.screen.blit(wind_text, text_rect)

    def _render_score_ui(self):
        """Render score display."""
        # Current score (large, top-center)
        score_text = self.scoring.get_current_score_formatted()
        score_surf = self.font_large.render(score_text, True, Palette.WHITE)
        score_shadow = self.font_large.render(score_text, True, Palette.NAVY)
        score_rect = score_surf.get_rect(center=(self.width // 2, 50))

        self.screen.blit(score_shadow, (score_rect.x + 3, score_rect.y + 3))
        self.screen.blit(score_surf, score_rect)

        # High score (smaller, top-right)
        hs_text = f"BEST: {self.scoring.get_high_score_formatted()}"
        hs_surf = self.font_small.render(hs_text, True, Palette.WARM_YELLOW)
        hs_rect = hs_surf.get_rect(topright=(self.width - 20, 20))
        self.screen.blit(hs_surf, hs_rect)

        # Hit counter (top-left)
        hits = self.scoring.get_current_hits()
        hits_text = f"Hits: {hits}"
        hits_surf = self.font_small.render(hits_text, True, Palette.SKY_BLUE)
        self.screen.blit(hits_surf, (20, 20))

    def _render_game_over(self):
        """Render game over screen."""
        # Keep the last gameplay state visible
        self._render_players()

        # Show popped balloon
        popped_surf = self.assets['balloon_popped']
        balloon_pos = self.balloon.get_position()
        rect = popped_surf.get_rect(center=(int(balloon_pos[0]),
                                           int(balloon_pos[1])))
        self.screen.blit(popped_surf, rect)

        # Dark overlay
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))

        # Game Over text
        go_text = self.font_large.render("Game Over!", True, Palette.CORAL)
        go_shadow = self.font_large.render("Game Over!", True, Palette.NAVY)
        go_rect = go_text.get_rect(center=(self.width // 2, self.height // 3))

        self.screen.blit(go_shadow, (go_rect.x + 4, go_rect.y + 4))
        self.screen.blit(go_text, go_rect)

        # Final score
        final_score = self.scoring.get_current_score_formatted()
        score_label = self.font_medium.render("Time:", True, Palette.WHITE)
        score_value = self.font_large.render(final_score, True, Palette.WARM_YELLOW)

        label_rect = score_label.get_rect(center=(self.width // 2,
                                                  self.height // 2 - 20))
        value_rect = score_value.get_rect(center=(self.width // 2,
                                                  self.height // 2 + 40))

        self.screen.blit(score_label, label_rect)
        self.screen.blit(score_value, value_rect)

        # New high score celebration
        if self.new_high_score:
            # Pulsing effect
            pulse = abs(math.sin(pygame.time.get_ticks() / 200))
            hs_color = (
                int(255 * pulse + Palette.WARM_YELLOW[0] * (1 - pulse)),
                int(200 * pulse + Palette.WARM_YELLOW[1] * (1 - pulse)),
                int(0 * pulse + Palette.WARM_YELLOW[2] * (1 - pulse)),
            )
            new_hs = self.font_medium.render("NEW BEST TIME!", True, hs_color)
            new_hs_rect = new_hs.get_rect(center=(self.width // 2,
                                                  self.height // 2 + 100))
            self.screen.blit(new_hs, new_hs_rect)

        # Play again prompt
        if self.game_over_timer > 1.0:
            again_text = "Press SPACE to Play Again"
            pulse = abs(math.sin(pygame.time.get_ticks() / 500)) * 0.3 + 0.7
            again_color = tuple(int(c * pulse) for c in Palette.WHITE)
            again = self.font_small.render(again_text, True, again_color)
            again_rect = again.get_rect(center=(self.width // 2,
                                               self.height * 3 // 4))
            self.screen.blit(again, again_rect)

    def _render_pause_overlay(self):
        """Render pause screen overlay."""
        # Dark overlay
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        # Paused text
        pause_text = self.font_large.render("PAUSED", True, Palette.WHITE)
        pause_rect = pause_text.get_rect(center=(self.width // 2, self.height // 2))
        self.screen.blit(pause_text, pause_rect)

        # Instructions
        resume_text = self.font_small.render("Press SPACE or ESC to Resume",
                                            True, Palette.PALE_BLUE)
        resume_rect = resume_text.get_rect(center=(self.width // 2,
                                                   self.height // 2 + 60))
        self.screen.blit(resume_text, resume_rect)

    def _show_camera_preview(self):
        """Show camera feed in a separate window with detected skeleton."""
        if not self.show_camera or not self.camera_ready:
            return

        frame = self.player_detector.last_frame
        if frame is not None:
            display_frame = frame.copy()
            h, w = display_frame.shape[:2]

            # Use cached players - scale from game coords to camera coords
            players = self.cached_players
            scale_x = w / self.width
            scale_y = h / self.height

            # Colors for different players (BGR format)
            player_colors = [
                (255, 150, 0),    # Bluey - light blue
                (0, 165, 255),    # Bingo - orange
                (200, 100, 50),   # Bandit - blue-grey
                (100, 130, 255),  # Chilli - salmon
            ]

            def scale_pt(pt):
                """Scale game coordinates to camera coordinates."""
                if pt is None:
                    return None
                return (int(pt[0] * scale_x), int(pt[1] * scale_y))

            for i, player in enumerate(players):
                color = player_colors[i % len(player_colors)]

                # Draw skeleton connections (upper body only)
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

                # Draw joint points (upper body only)
                joints = ['nose', 'left_shoulder', 'right_shoulder', 'left_elbow',
                         'right_elbow', 'left_hand', 'right_hand', 'left_hip', 'right_hip']

                for joint_name in joints:
                    pt = scale_pt(getattr(player, joint_name, None))
                    if pt:
                        # Larger circles for hands (collision points)
                        radius = 12 if 'hand' in joint_name else 6
                        cv2.circle(display_frame, pt, radius, color, -1)
                        cv2.circle(display_frame, pt, radius, (255, 255, 255), 2)

                # Label the player
                nose_pt = scale_pt(player.nose)
                if nose_pt:
                    label = ['Bluey', 'Bingo', 'Bandit', 'Chilli'][i % 4]
                    cv2.putText(display_frame, label,
                               (nose_pt[0] - 30, nose_pt[1] - 30),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

            # Add text overlay
            num_players = len(players)
            status = f"Detected: {num_players} player{'s' if num_players != 1 else ''}"
            cv2.putText(display_frame, status,
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(display_frame, "Press 'Q' to hide | +/- to adjust detection area",
                       (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

            # Draw detection region boundary
            bounds = self.player_detector.get_detection_bounds(w, h)
            cv2.rectangle(display_frame,
                         (bounds[0], bounds[1]),
                         (bounds[0] + bounds[2], bounds[1] + bounds[3]),
                         (0, 255, 0), 2)
            cv2.putText(display_frame, "Detection Zone",
                       (bounds[0] + 5, bounds[1] + 20),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

            cv2.imshow("KeepyUppy - Camera", display_frame)

            # Check for camera window key presses
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                self.show_camera = False
                cv2.destroyWindow("KeepyUppy - Camera")
            elif key == ord('+') or key == ord('='):
                # Increase margin (smaller detection area)
                new_margin = self.player_detector.detection_margin + 0.05
                self.player_detector.set_detection_margin(new_margin)
                print(f"Detection margin: {self.player_detector.detection_margin:.0%}")
            elif key == ord('-') or key == ord('_'):
                # Decrease margin (larger detection area)
                new_margin = self.player_detector.detection_margin - 0.05
                self.player_detector.set_detection_margin(new_margin)
                print(f"Detection margin: {self.player_detector.detection_margin:.0%}")

    def _cleanup(self):
        """Clean up resources."""
        print("Shutting down...")
        self.player_detector.stop()
        cv2.destroyAllWindows()
        pygame.quit()


def main():
    """Entry point for the game."""
    import argparse

    parser = argparse.ArgumentParser(description="KeepyUppy - Balloon Game")
    parser.add_argument('--width', type=int, default=1280,
                       help='Screen width (default: 1280)')
    parser.add_argument('--height', type=int, default=720,
                       help='Screen height (default: 720)')
    parser.add_argument('--fullscreen', action='store_true',
                       help='Run in fullscreen mode')
    parser.add_argument('--no-camera-preview', action='store_true',
                       help='Hide the camera preview window')

    args = parser.parse_args()

    game = KeepyUppyGame(
        width=args.width,
        height=args.height,
        fullscreen=args.fullscreen,
        show_camera=not args.no_camera_preview
    )
    game.start()


if __name__ == '__main__':
    main()
