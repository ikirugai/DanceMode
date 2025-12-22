"""
Christmas Popper! - A festive hand-tracking game
Pop baubles, catch elves and Santa, avoid the Grinch!
"""

import pygame
import cv2
import math
import random
from typing import List, Optional, Tuple, Dict
from enum import Enum
from dataclasses import dataclass

from player_detection import PlayerDetector


class GameState(Enum):
    TITLE = "title"
    COUNTDOWN = "countdown"
    PLAYING = "playing"
    RESULTS = "results"


@dataclass
class Target:
    """A poppable target on screen."""
    x: float
    y: float
    target_type: str  # 'bauble', 'elf', 'santa', 'grinch'
    vx: float = 0  # velocity x
    vy: float = 0  # velocity y
    lifetime: float = 5.0  # seconds until despawn
    size: float = 50
    popped: bool = False
    pop_timer: float = 0  # animation timer after pop


class ChristmasPopper:
    """Main game class for Christmas Popper."""

    # Point values
    POINTS = {
        'bauble': 5,
        'elf': 50,
        'santa': 100,
        'grinch': -10,
    }

    # Spawn rates (seconds between spawns)
    SPAWN_RATES = {
        'bauble': 1.0,
        'elf': 4.0,
        'santa': 20.0,
        'grinch': 6.0,
    }

    # Target lifetimes
    LIFETIMES = {
        'bauble': 8.0,
        'elf': 3.0,
        'santa': 3.0,
        'grinch': 3.0,
    }

    # Movement speeds (pixels per second)
    SPEEDS = {
        'bauble': 0,
        'elf': 150,
        'santa': 300,  # Twice as fast!
        'grinch': 150,
    }

    def __init__(self, width: int = 1280, height: int = 720, fullscreen: bool = False):
        pygame.init()
        pygame.mixer.init()

        self.width = width
        self.height = height

        flags = pygame.DOUBLEBUF
        if fullscreen:
            flags |= pygame.FULLSCREEN
            info = pygame.display.Info()
            self.width = info.current_w
            self.height = info.current_h

        self.screen = pygame.display.set_mode((self.width, self.height), flags)
        pygame.display.set_caption("Christmas Popper!")

        self.clock = pygame.time.Clock()
        self.target_fps = 60

        # Player detection
        self.player_detector = PlayerDetector()
        self.camera_ready = False
        self.cached_players = []
        self.camera_surface = None

        # Fonts
        self.font_huge = pygame.font.Font(None, 120)
        self.font_large = pygame.font.Font(None, 72)
        self.font_medium = pygame.font.Font(None, 48)
        self.font_small = pygame.font.Font(None, 32)

        # Game state
        self.state = GameState.TITLE
        self.countdown_timer = 3.0
        self.game_timer = 60.0  # 1 minute rounds
        self.score = 0
        self.high_score = 0

        # Targets
        self.targets: List[Target] = []
        self.spawn_timers = {t: 0.0 for t in self.SPAWN_RATES}

        # Stats for results
        self.stats = {'bauble': 0, 'elf': 0, 'santa': 0, 'grinch': 0}

        # Particles for effects
        self.particles: List[dict] = []
        self.snowflakes: List[dict] = []
        self._init_snowflakes(100)

        # Sounds
        self._init_sounds()

        # Create character sprites
        self._create_sprites()

    def _init_snowflakes(self, count: int):
        """Create background snowflakes."""
        for _ in range(count):
            self.snowflakes.append({
                'x': random.randint(0, self.width),
                'y': random.randint(-self.height, self.height),
                'size': random.randint(2, 6),
                'speed': random.random() * 50 + 20,
                'drift': random.random() * 2 - 1,
            })

    def _create_sprites(self):
        """Create simple sprite surfaces for characters."""
        self.sprites = {}

        # Bauble - golden ornament
        bauble = pygame.Surface((60, 70), pygame.SRCALPHA)
        pygame.draw.circle(bauble, (255, 215, 0), (30, 35), 25)  # Gold ball
        pygame.draw.circle(bauble, (255, 240, 150), (22, 28), 8)  # Highlight
        pygame.draw.rect(bauble, (200, 200, 200), (24, 5, 12, 10))  # Cap
        pygame.draw.circle(bauble, (150, 150, 150), (30, 3), 5)  # Loop
        self.sprites['bauble'] = bauble

        # Elf - green with pointy hat
        elf = pygame.Surface((50, 70), pygame.SRCALPHA)
        # Body (green)
        pygame.draw.ellipse(elf, (34, 139, 34), (10, 35, 30, 35))
        # Head (skin tone)
        pygame.draw.circle(elf, (255, 218, 185), (25, 25), 15)
        # Hat (red with green)
        points = [(25, 0), (10, 25), (40, 25)]
        pygame.draw.polygon(elf, (220, 20, 60), points)
        pygame.draw.circle(elf, (255, 255, 0), (25, 2), 5)  # Hat tip
        # Eyes
        pygame.draw.circle(elf, (0, 0, 0), (20, 23), 3)
        pygame.draw.circle(elf, (0, 0, 0), (30, 23), 3)
        # Smile
        pygame.draw.arc(elf, (0, 0, 0), (18, 25, 14, 10), 3.4, 6.0, 2)
        # Ears (pointy)
        pygame.draw.polygon(elf, (255, 218, 185), [(8, 22), (5, 18), (12, 25)])
        pygame.draw.polygon(elf, (255, 218, 185), [(42, 22), (45, 18), (38, 25)])
        self.sprites['elf'] = elf

        # Santa - red suit, white beard
        santa = pygame.Surface((70, 90), pygame.SRCALPHA)
        # Body (red)
        pygame.draw.ellipse(santa, (220, 20, 60), (10, 40, 50, 50))
        # Belt
        pygame.draw.rect(santa, (0, 0, 0), (15, 55, 40, 8))
        pygame.draw.rect(santa, (255, 215, 0), (30, 54, 10, 10))  # Buckle
        # Head
        pygame.draw.circle(santa, (255, 218, 185), (35, 25), 18)
        # Beard (white)
        pygame.draw.ellipse(santa, (255, 255, 255), (20, 28, 30, 25))
        # Hat
        pygame.draw.polygon(santa, (220, 20, 60), [(35, 0), (15, 22), (55, 22)])
        pygame.draw.circle(santa, (255, 255, 255), (35, 2), 6)
        pygame.draw.ellipse(santa, (255, 255, 255), (12, 18, 46, 10))  # Brim
        # Eyes
        pygame.draw.circle(santa, (0, 0, 0), (28, 22), 3)
        pygame.draw.circle(santa, (0, 0, 0), (42, 22), 3)
        # Nose
        pygame.draw.circle(santa, (255, 150, 150), (35, 28), 4)
        self.sprites['santa'] = santa

        # Grinch - green, mean face
        grinch = pygame.Surface((60, 80), pygame.SRCALPHA)
        # Body (green furry)
        pygame.draw.ellipse(grinch, (0, 128, 0), (10, 40, 40, 40))
        # Head (green)
        pygame.draw.circle(grinch, (0, 128, 0), (30, 28), 22)
        # Mean eyebrows
        pygame.draw.line(grinch, (0, 80, 0), (15, 18), (28, 25), 4)
        pygame.draw.line(grinch, (0, 80, 0), (45, 18), (32, 25), 4)
        # Evil eyes (yellow)
        pygame.draw.circle(grinch, (255, 255, 0), (22, 25), 6)
        pygame.draw.circle(grinch, (255, 255, 0), (38, 25), 6)
        pygame.draw.circle(grinch, (255, 0, 0), (22, 25), 3)  # Red pupils
        pygame.draw.circle(grinch, (255, 0, 0), (38, 25), 3)
        # Evil grin
        pygame.draw.arc(grinch, (0, 80, 0), (15, 30, 30, 15), 3.5, 6.0, 3)
        # Santa hat (stolen!)
        pygame.draw.polygon(grinch, (220, 20, 60), [(30, 2), (12, 20), (48, 20)])
        pygame.draw.circle(grinch, (255, 255, 255), (30, 3), 5)
        self.sprites['grinch'] = grinch

    def _init_sounds(self):
        """Initialize sound effects."""
        self.sounds = {}
        try:
            sample_rate = 44100

            # Pop sound (happy)
            pop_duration = 0.1
            pop_samples = int(sample_rate * pop_duration)
            self.sounds['pop'] = pygame.mixer.Sound(
                buffer=bytes([
                    int(128 + 100 * math.sin(2 * math.pi * 800 * t / sample_rate) *
                        (1 - t / pop_samples))
                    for t in range(pop_samples)
                ])
            )

            # Santa/Elf catch (big success)
            catch_duration = 0.2
            catch_samples = int(sample_rate * catch_duration)
            self.sounds['catch'] = pygame.mixer.Sound(
                buffer=bytes([
                    int(128 + 100 * math.sin(2 * math.pi * (600 + t * 2) * t / sample_rate) *
                        (1 - t / catch_samples))
                    for t in range(catch_samples)
                ])
            )

            # Grinch (bad sound)
            bad_duration = 0.3
            bad_samples = int(sample_rate * bad_duration)
            self.sounds['bad'] = pygame.mixer.Sound(
                buffer=bytes([
                    int(128 + 80 * math.sin(2 * math.pi * 150 * t / sample_rate) *
                        (1 - t / bad_samples))
                    for t in range(bad_samples)
                ])
            )

            # Countdown beep
            beep_duration = 0.1
            beep_samples = int(sample_rate * beep_duration)
            self.sounds['beep'] = pygame.mixer.Sound(
                buffer=bytes([
                    int(128 + 80 * math.sin(2 * math.pi * 880 * t / sample_rate) *
                        (1 - t / beep_samples))
                    for t in range(beep_samples)
                ])
            )

        except Exception as e:
            print(f"Warning: Could not initialize sounds: {e}")

    def _play_sound(self, name: str):
        if name in self.sounds:
            try:
                self.sounds[name].play()
            except:
                pass

    def start(self):
        """Start the game."""
        print("Starting Christmas Popper!")
        print("Initializing camera...")

        self.camera_ready = self.player_detector.start()
        if not self.camera_ready:
            print("Warning: Camera not available.")

        self.run()

    def run(self):
        """Main game loop."""
        running = True
        frame_count = 0

        def process_events():
            nonlocal running
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False
                elif event.type == pygame.KEYDOWN:
                    if not self._handle_keydown(event.key):
                        return False
            return True

        while running:
            dt = self.clock.tick(self.target_fps) / 1000.0
            frame_count += 1

            if not process_events():
                running = False
                continue

            # Detect players every other frame
            if self.camera_ready and frame_count % 2 == 0:
                self.cached_players = self.player_detector.detect_players(
                    self.width, self.height)

            if not process_events():
                running = False
                continue

            self._update(dt)
            self._render()
            pygame.display.flip()

        self._cleanup()

    def _handle_keydown(self, key: int) -> bool:
        if key == pygame.K_ESCAPE:
            return False

        elif key == pygame.K_SPACE:
            if self.state == GameState.TITLE:
                self._start_countdown()
            elif self.state == GameState.RESULTS:
                self._start_countdown()

        return True

    def _start_countdown(self):
        """Start countdown before game."""
        self.state = GameState.COUNTDOWN
        self.countdown_timer = 3.0
        self._play_sound('beep')

    def _start_game(self):
        """Start a new game round."""
        self.state = GameState.PLAYING
        self.game_timer = 60.0
        self.score = 0
        self.targets.clear()
        self.particles.clear()
        self.stats = {'bauble': 0, 'elf': 0, 'santa': 0, 'grinch': 0}
        self.spawn_timers = {t: 0.0 for t in self.SPAWN_RATES}

    def _update(self, dt: float):
        """Update game logic."""
        # Update snowflakes always
        self._update_snowflakes(dt)

        # Update camera surface
        self._update_camera_surface()

        if self.state == GameState.COUNTDOWN:
            self._update_countdown(dt)
        elif self.state == GameState.PLAYING:
            self._update_playing(dt)

    def _update_snowflakes(self, dt: float):
        """Update falling snowflakes."""
        for snow in self.snowflakes:
            snow['y'] += snow['speed'] * dt
            snow['x'] += snow['drift'] * 20 * dt
            if snow['y'] > self.height:
                snow['y'] = -10
                snow['x'] = random.randint(0, self.width)

    def _update_camera_surface(self):
        """Convert camera frame to pygame surface."""
        if self.camera_ready and self.player_detector.last_frame is not None:
            frame = self.player_detector.last_frame
            # Convert BGR to RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            # Resize to screen size
            frame_resized = cv2.resize(frame_rgb, (self.width, self.height))
            # Rotate/flip for pygame
            frame_surface = pygame.surfarray.make_surface(frame_resized.swapaxes(0, 1))
            self.camera_surface = frame_surface

    def _update_countdown(self, dt: float):
        """Update countdown."""
        prev_second = int(self.countdown_timer)
        self.countdown_timer -= dt
        new_second = int(self.countdown_timer)

        if new_second < prev_second and new_second >= 0:
            self._play_sound('beep')

        if self.countdown_timer <= 0:
            self._start_game()

    def _update_playing(self, dt: float):
        """Update gameplay."""
        # Update game timer
        self.game_timer -= dt
        if self.game_timer <= 0:
            self.game_timer = 0
            self._end_game()
            return

        # Spawn targets
        self._update_spawning(dt)

        # Update targets
        self._update_targets(dt)

        # Check collisions with hands
        self._check_collisions()

        # Update particles
        self._update_particles(dt)

    def _update_spawning(self, dt: float):
        """Spawn new targets."""
        for target_type, rate in self.SPAWN_RATES.items():
            self.spawn_timers[target_type] += dt
            if self.spawn_timers[target_type] >= rate:
                self.spawn_timers[target_type] = 0
                self._spawn_target(target_type)

    def _spawn_target(self, target_type: str):
        """Spawn a new target of given type."""
        margin = 80
        x = random.randint(margin, self.width - margin)
        y = random.randint(margin, self.height - margin)

        speed = self.SPEEDS[target_type]
        if speed > 0:
            # Random direction for moving targets
            angle = random.random() * 2 * math.pi
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
        else:
            vx, vy = 0, 0

        lifetime = self.LIFETIMES[target_type]

        # Size varies by type
        sizes = {'bauble': 50, 'elf': 55, 'santa': 70, 'grinch': 60}

        target = Target(
            x=x, y=y,
            target_type=target_type,
            vx=vx, vy=vy,
            lifetime=lifetime,
            size=sizes[target_type]
        )
        self.targets.append(target)

    def _update_targets(self, dt: float):
        """Update all targets."""
        for target in self.targets[:]:
            if target.popped:
                target.pop_timer += dt
                if target.pop_timer > 0.3:
                    self.targets.remove(target)
                continue

            # Move
            target.x += target.vx * dt
            target.y += target.vy * dt

            # Bounce off walls
            if target.x < 50 or target.x > self.width - 50:
                target.vx = -target.vx
                target.x = max(50, min(self.width - 50, target.x))
            if target.y < 50 or target.y > self.height - 50:
                target.vy = -target.vy
                target.y = max(50, min(self.height - 50, target.y))

            # Lifetime
            target.lifetime -= dt
            if target.lifetime <= 0:
                self.targets.remove(target)

    def _check_collisions(self):
        """Check if hands hit any targets."""
        if not self.cached_players:
            return

        # Get all hand positions
        hands = []
        for player in self.cached_players:
            if player.left_hand:
                hands.append(player.left_hand)
            if player.right_hand:
                hands.append(player.right_hand)

        hit_radius = 50

        for target in self.targets:
            if target.popped:
                continue

            for hand in hands:
                dx = hand[0] - target.x
                dy = hand[1] - target.y
                dist = math.sqrt(dx * dx + dy * dy)

                if dist < hit_radius + target.size / 2:
                    self._pop_target(target)
                    break

    def _pop_target(self, target: Target):
        """Pop a target and award points."""
        target.popped = True
        target.pop_timer = 0

        points = self.POINTS[target.target_type]
        self.score += points
        self.stats[target.target_type] += 1

        # Spawn particles
        self._spawn_pop_particles(target.x, target.y, target.target_type)

        # Play sound
        if target.target_type == 'grinch':
            self._play_sound('bad')
        elif target.target_type in ['santa', 'elf']:
            self._play_sound('catch')
        else:
            self._play_sound('pop')

    def _spawn_pop_particles(self, x: float, y: float, target_type: str):
        """Spawn celebration particles."""
        colors = {
            'bauble': [(255, 215, 0), (255, 240, 150)],
            'elf': [(34, 139, 34), (255, 0, 0)],
            'santa': [(220, 20, 60), (255, 255, 255)],
            'grinch': [(0, 128, 0), (128, 128, 128)],
        }

        for _ in range(20):
            angle = random.random() * 2 * math.pi
            speed = random.random() * 300 + 100
            color = random.choice(colors[target_type])

            self.particles.append({
                'x': x,
                'y': y,
                'vx': math.cos(angle) * speed,
                'vy': math.sin(angle) * speed,
                'color': color,
                'size': random.randint(4, 10),
                'lifetime': random.random() * 0.5 + 0.3,
            })

    def _update_particles(self, dt: float):
        """Update particles."""
        for p in self.particles[:]:
            p['x'] += p['vx'] * dt
            p['y'] += p['vy'] * dt
            p['vy'] += 400 * dt  # Gravity
            p['lifetime'] -= dt
            if p['lifetime'] <= 0:
                self.particles.remove(p)

    def _end_game(self):
        """End the game and show results."""
        self.state = GameState.RESULTS
        if self.score > self.high_score:
            self.high_score = self.score

    def _render(self):
        """Render the game."""
        # Draw camera feed as background (or black if no camera)
        if self.camera_surface:
            self.screen.blit(self.camera_surface, (0, 0))
        else:
            self.screen.fill((20, 20, 40))

        # Darken camera slightly for better visibility
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 30, 80))
        self.screen.blit(overlay, (0, 0))

        # Draw snowflakes
        self._draw_snowflakes()

        # State-specific rendering
        if self.state == GameState.TITLE:
            self._render_title()
        elif self.state == GameState.COUNTDOWN:
            self._render_countdown()
        elif self.state == GameState.PLAYING:
            self._render_playing()
        elif self.state == GameState.RESULTS:
            self._render_results()

    def _draw_snowflakes(self):
        """Draw falling snowflakes."""
        for snow in self.snowflakes:
            alpha = 150
            size = snow['size']
            pygame.draw.circle(self.screen, (255, 255, 255),
                             (int(snow['x']), int(snow['y'])), size)

    def _render_title(self):
        """Render title screen."""
        # Title
        title = self.font_huge.render("Christmas", True, (255, 50, 50))
        title2 = self.font_huge.render("Popper!", True, (50, 255, 50))
        self.screen.blit(title, title.get_rect(center=(self.width // 2, self.height // 3 - 40)))
        self.screen.blit(title2, title2.get_rect(center=(self.width // 2, self.height // 3 + 50)))

        # Instructions
        instructions = [
            "Pop baubles with your hands!",
            "Catch Elves (+50) and Santa (+100)!",
            "Avoid the Grinch (-10)!",
            "60 seconds - get the highest score!",
        ]
        y = self.height // 2 + 50
        for line in instructions:
            text = self.font_medium.render(line, True, (255, 255, 255))
            self.screen.blit(text, text.get_rect(center=(self.width // 2, y)))
            y += 50

        # Start prompt
        pulse = abs(math.sin(pygame.time.get_ticks() / 500)) * 0.3 + 0.7
        color = (int(255 * pulse), int(255 * pulse), int(100 * pulse))
        start = self.font_large.render("Press SPACE to Start!", True, color)
        self.screen.blit(start, start.get_rect(center=(self.width // 2, self.height - 100)))

        # High score
        if self.high_score > 0:
            hs = self.font_medium.render(f"High Score: {self.high_score}", True, (255, 215, 0))
            self.screen.blit(hs, hs.get_rect(center=(self.width // 2, self.height - 40)))

    def _render_countdown(self):
        """Render countdown."""
        count = max(1, int(self.countdown_timer) + 1)
        if self.countdown_timer <= 0:
            text = "GO!"
            color = (50, 255, 50)
        else:
            text = str(count)
            color = (255, 255, 100)

        scale = 1.0 + (self.countdown_timer % 1.0) * 0.5
        font_size = int(150 * scale)
        font = pygame.font.Font(None, font_size)

        rendered = font.render(text, True, color)
        self.screen.blit(rendered, rendered.get_rect(center=(self.width // 2, self.height // 2)))

        # "Get Ready" text
        ready = self.font_medium.render("Get Ready!", True, (255, 255, 255))
        self.screen.blit(ready, ready.get_rect(center=(self.width // 2, self.height // 3)))

    def _render_playing(self):
        """Render gameplay."""
        # Draw targets
        for target in self.targets:
            self._draw_target(target)

        # Draw particles
        for p in self.particles:
            alpha = int(255 * (p['lifetime'] / 0.8))
            pygame.draw.circle(self.screen, p['color'],
                             (int(p['x']), int(p['y'])), p['size'])

        # Draw UI
        self._draw_game_ui()

    def _draw_target(self, target: Target):
        """Draw a single target."""
        if target.popped:
            # Pop animation - expand and fade
            scale = 1.0 + target.pop_timer * 3
            alpha = int(255 * (1 - target.pop_timer / 0.3))
            # Just draw expanding circle
            size = int(target.size * scale)
            surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            color = (255, 255, 100, alpha) if target.target_type != 'grinch' else (100, 100, 100, alpha)
            pygame.draw.circle(surf, color, (size, size), size)
            self.screen.blit(surf, (int(target.x - size), int(target.y - size)))
            return

        # Draw sprite
        sprite = self.sprites.get(target.target_type)
        if sprite:
            # Pulsing effect
            pulse = 1.0 + math.sin(pygame.time.get_ticks() / 200) * 0.1
            scaled = pygame.transform.scale(sprite,
                (int(sprite.get_width() * pulse), int(sprite.get_height() * pulse)))
            rect = scaled.get_rect(center=(int(target.x), int(target.y)))
            self.screen.blit(scaled, rect)

        # Draw lifetime indicator for moving targets
        if target.target_type in ['elf', 'santa', 'grinch']:
            progress = target.lifetime / self.LIFETIMES[target.target_type]
            bar_width = 40
            bar_height = 6
            bar_x = int(target.x - bar_width // 2)
            bar_y = int(target.y + target.size // 2 + 10)

            # Background
            pygame.draw.rect(self.screen, (50, 50, 50),
                           (bar_x, bar_y, bar_width, bar_height))
            # Progress
            color = (50, 255, 50) if progress > 0.3 else (255, 100, 50)
            pygame.draw.rect(self.screen, color,
                           (bar_x, bar_y, int(bar_width * progress), bar_height))

    def _draw_game_ui(self):
        """Draw game UI elements."""
        # Timer bar at top
        timer_progress = self.game_timer / 60.0
        bar_width = self.width - 200
        bar_height = 20
        bar_x = 100
        bar_y = 20

        # Background
        pygame.draw.rect(self.screen, (50, 50, 50),
                        (bar_x, bar_y, bar_width, bar_height), border_radius=10)
        # Progress
        color = (50, 255, 50) if timer_progress > 0.3 else (255, 50, 50)
        pygame.draw.rect(self.screen, color,
                        (bar_x, bar_y, int(bar_width * timer_progress), bar_height),
                        border_radius=10)

        # Timer text
        seconds = int(self.game_timer)
        timer_text = self.font_medium.render(f"{seconds}s", True, (255, 255, 255))
        self.screen.blit(timer_text, (bar_x - 60, bar_y - 5))

        # Score (left side)
        score_text = self.font_large.render(f"Score: {self.score}", True, (255, 215, 0))
        self.screen.blit(score_text, (20, 60))

        # High score (right side)
        hs_text = self.font_small.render(f"Best: {self.high_score}", True, (200, 200, 200))
        self.screen.blit(hs_text, (self.width - 150, 20))

        # Point values legend (bottom)
        legend_y = self.height - 35
        legend_items = [
            ("Bauble +5", (255, 215, 0)),
            ("Elf +50", (34, 139, 34)),
            ("Santa +100", (220, 20, 60)),
            ("Grinch -10", (0, 128, 0)),
        ]
        x = 20
        for text, color in legend_items:
            rendered = self.font_small.render(text, True, color)
            self.screen.blit(rendered, (x, legend_y))
            x += 200

    def _render_results(self):
        """Render results screen."""
        # Dark overlay
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        # Title
        if self.score >= self.high_score and self.score > 0:
            title = self.font_huge.render("NEW HIGH SCORE!", True, (255, 215, 0))
        else:
            title = self.font_huge.render("Time's Up!", True, (255, 100, 100))
        self.screen.blit(title, title.get_rect(center=(self.width // 2, 80)))

        # Score breakdown
        y = 180
        breakdown = [
            (f"Baubles: {self.stats['bauble']}", f"× 5 = {self.stats['bauble'] * 5}", (255, 215, 0)),
            (f"Elves: {self.stats['elf']}", f"× 50 = {self.stats['elf'] * 50}", (34, 139, 34)),
            (f"Santas: {self.stats['santa']}", f"× 100 = {self.stats['santa'] * 100}", (220, 20, 60)),
            (f"Grinches: {self.stats['grinch']}", f"× -10 = {self.stats['grinch'] * -10}", (0, 128, 0)),
        ]

        for label, points, color in breakdown:
            label_text = self.font_medium.render(label, True, color)
            points_text = self.font_medium.render(points, True, (255, 255, 255))
            self.screen.blit(label_text, (self.width // 2 - 200, y))
            self.screen.blit(points_text, (self.width // 2 + 50, y))
            y += 60

        # Line
        pygame.draw.line(self.screen, (255, 255, 255),
                        (self.width // 2 - 200, y), (self.width // 2 + 200, y), 2)
        y += 20

        # Total
        total_text = self.font_large.render(f"TOTAL: {self.score}", True, (255, 255, 100))
        self.screen.blit(total_text, total_text.get_rect(center=(self.width // 2, y + 30)))

        # High score
        y += 100
        hs_text = self.font_medium.render(f"High Score: {self.high_score}", True, (200, 200, 200))
        self.screen.blit(hs_text, hs_text.get_rect(center=(self.width // 2, y)))

        # Play again
        y += 80
        pulse = abs(math.sin(pygame.time.get_ticks() / 500)) * 0.3 + 0.7
        color = (int(255 * pulse), int(255 * pulse), int(100 * pulse))
        again = self.font_medium.render("Press SPACE to Play Again!", True, color)
        self.screen.blit(again, again.get_rect(center=(self.width // 2, y)))

    def _cleanup(self):
        """Clean up resources."""
        self.player_detector.stop()
        pygame.quit()


def main():
    """Entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Christmas Popper!")
    parser.add_argument('--width', type=int, default=1280, help='Screen width')
    parser.add_argument('--height', type=int, default=720, help='Screen height')
    parser.add_argument('--fullscreen', action='store_true', help='Fullscreen mode')

    args = parser.parse_args()

    game = ChristmasPopper(
        width=args.width,
        height=args.height,
        fullscreen=args.fullscreen
    )
    game.start()


if __name__ == '__main__':
    main()
