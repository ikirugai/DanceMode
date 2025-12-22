"""
Dancer Avatar Renderer
Renders a fun, colorful stick-figure dancer that follows body movements.
"""

import pygame
import math
import random
from typing import Dict, List, Optional, Tuple
from player_detection import PlayerLandmarks


# Fun, vibrant color palette for dancers
class DancerColors:
    # Player colors (one per player)
    PLAYER_COLORS = [
        {'body': (255, 100, 150), 'outline': (180, 50, 100), 'glow': (255, 180, 200)},  # Pink
        {'body': (100, 200, 255), 'outline': (50, 130, 180), 'glow': (180, 230, 255)},  # Blue
        {'body': (150, 255, 100), 'outline': (80, 180, 50), 'glow': (200, 255, 180)},   # Green
        {'body': (255, 200, 100), 'outline': (180, 130, 50), 'glow': (255, 230, 180)},  # Orange
    ]

    # Target colors
    TARGET_IDLE = (100, 255, 200)
    TARGET_ACTIVE = (255, 255, 100)
    TARGET_HIT = (100, 255, 100)
    TARGET_MISS = (255, 100, 100)


class DancerAvatar:
    """Renders a dancer avatar based on detected body positions."""

    def __init__(self, screen_width: int, screen_height: int):
        self.screen_width = screen_width
        self.screen_height = screen_height

        # Avatar sizing
        self.head_radius = 35
        self.body_thickness = 12
        self.limb_thickness = 10
        self.hand_radius = 20

        # Position smoothing
        self.smooth_factor = 0.25
        self.previous_positions: Dict[str, Tuple[float, float]] = {}

        # Animation
        self.bounce_offset = 0.0
        self.pulse_time = 0.0

    def render_player(self, surface: pygame.Surface, player: PlayerLandmarks,
                      player_index: int = 0):
        """Render a dancer avatar for a detected player."""
        positions = self._get_smoothed_positions(player, player_index)
        if not positions:
            return

        colors = DancerColors.PLAYER_COLORS[player_index % len(DancerColors.PLAYER_COLORS)]

        # Calculate body center for bounce effect
        self.pulse_time += 0.1
        bounce = math.sin(self.pulse_time * 2) * 3

        # Draw body parts (back to front)
        self._draw_body(surface, positions, colors, bounce)
        self._draw_limbs(surface, positions, colors, bounce)
        self._draw_hands(surface, positions, colors)
        self._draw_head(surface, positions, colors, bounce)

    def _get_smoothed_positions(self, player: PlayerLandmarks,
                                 player_index: int) -> Optional[Dict]:
        """Get smoothed positions for avatar rendering."""

        def smooth(point, name):
            if point is None:
                return None

            full_key = f"p{player_index}_{name}"

            if full_key in self.previous_positions:
                prev = self.previous_positions[full_key]
                point = (
                    prev[0] + (point[0] - prev[0]) * self.smooth_factor,
                    prev[1] + (point[1] - prev[1]) * self.smooth_factor
                )

            self.previous_positions[full_key] = point
            return point

        positions = {
            'nose': smooth(player.nose, 'nose'),
            'left_shoulder': smooth(player.left_shoulder, 'l_shoulder'),
            'right_shoulder': smooth(player.right_shoulder, 'r_shoulder'),
            'left_elbow': smooth(player.left_elbow, 'l_elbow'),
            'right_elbow': smooth(player.right_elbow, 'r_elbow'),
            'left_hand': smooth(player.left_hand, 'l_hand'),
            'right_hand': smooth(player.right_hand, 'r_hand'),
            'left_hip': smooth(player.left_hip, 'l_hip'),
            'right_hip': smooth(player.right_hip, 'r_hip'),
        }

        # Need at least shoulders
        if not positions['left_shoulder'] or not positions['right_shoulder']:
            return None

        # Calculate derived positions
        positions['neck'] = (
            (positions['left_shoulder'][0] + positions['right_shoulder'][0]) / 2,
            (positions['left_shoulder'][1] + positions['right_shoulder'][1]) / 2 - 20
        )

        if positions['left_hip'] and positions['right_hip']:
            positions['hip_center'] = (
                (positions['left_hip'][0] + positions['right_hip'][0]) / 2,
                (positions['left_hip'][1] + positions['right_hip'][1]) / 2
            )
        else:
            # Estimate hip position
            positions['hip_center'] = (
                positions['neck'][0],
                positions['neck'][1] + 120
            )

        return positions

    def _draw_body(self, surface: pygame.Surface, positions: Dict,
                   colors: Dict, bounce: float):
        """Draw the torso."""
        neck = positions['neck']
        hip = positions['hip_center']

        if neck and hip:
            # Body glow
            pygame.draw.line(surface, colors['glow'],
                           (neck[0], neck[1] + bounce),
                           (hip[0], hip[1] + bounce),
                           self.body_thickness + 8)
            # Body outline
            pygame.draw.line(surface, colors['outline'],
                           (neck[0], neck[1] + bounce),
                           (hip[0], hip[1] + bounce),
                           self.body_thickness + 4)
            # Body main
            pygame.draw.line(surface, colors['body'],
                           (neck[0], neck[1] + bounce),
                           (hip[0], hip[1] + bounce),
                           self.body_thickness)

    def _draw_limbs(self, surface: pygame.Surface, positions: Dict,
                    colors: Dict, bounce: float):
        """Draw arms."""
        # Left arm
        if positions['left_shoulder']:
            shoulder = (positions['left_shoulder'][0], positions['left_shoulder'][1] + bounce)
            elbow = positions.get('left_elbow')
            hand = positions.get('left_hand')

            if elbow:
                self._draw_limb_segment(surface, shoulder, elbow, colors)
                if hand:
                    self._draw_limb_segment(surface, elbow, hand, colors)
            elif hand:
                self._draw_limb_segment(surface, shoulder, hand, colors)

        # Right arm
        if positions['right_shoulder']:
            shoulder = (positions['right_shoulder'][0], positions['right_shoulder'][1] + bounce)
            elbow = positions.get('right_elbow')
            hand = positions.get('right_hand')

            if elbow:
                self._draw_limb_segment(surface, shoulder, elbow, colors)
                if hand:
                    self._draw_limb_segment(surface, elbow, hand, colors)
            elif hand:
                self._draw_limb_segment(surface, shoulder, hand, colors)

    def _draw_limb_segment(self, surface: pygame.Surface,
                           start: Tuple[float, float], end: Tuple[float, float],
                           colors: Dict):
        """Draw a single limb segment with glow effect."""
        start_int = (int(start[0]), int(start[1]))
        end_int = (int(end[0]), int(end[1]))

        # Glow
        pygame.draw.line(surface, colors['glow'], start_int, end_int,
                        self.limb_thickness + 6)
        # Outline
        pygame.draw.line(surface, colors['outline'], start_int, end_int,
                        self.limb_thickness + 2)
        # Main
        pygame.draw.line(surface, colors['body'], start_int, end_int,
                        self.limb_thickness)

    def _draw_hands(self, surface: pygame.Surface, positions: Dict, colors: Dict):
        """Draw hands as circles."""
        for hand_name in ['left_hand', 'right_hand']:
            hand = positions.get(hand_name)
            if hand:
                pos = (int(hand[0]), int(hand[1]))
                # Glow
                pygame.draw.circle(surface, colors['glow'], pos, self.hand_radius + 5)
                # Outline
                pygame.draw.circle(surface, colors['outline'], pos, self.hand_radius + 2)
                # Main
                pygame.draw.circle(surface, colors['body'], pos, self.hand_radius)
                # Highlight
                highlight_pos = (pos[0] - 5, pos[1] - 5)
                pygame.draw.circle(surface, (255, 255, 255), highlight_pos, 6)

    def _draw_head(self, surface: pygame.Surface, positions: Dict,
                   colors: Dict, bounce: float):
        """Draw the head with a fun face."""
        nose = positions.get('nose')
        neck = positions.get('neck')

        if nose:
            head_pos = (int(nose[0]), int(nose[1] + bounce))
        elif neck:
            head_pos = (int(neck[0]), int(neck[1] - 50 + bounce))
        else:
            return

        # Head glow
        pygame.draw.circle(surface, colors['glow'], head_pos, self.head_radius + 8)
        # Head outline
        pygame.draw.circle(surface, colors['outline'], head_pos, self.head_radius + 3)
        # Head main
        pygame.draw.circle(surface, colors['body'], head_pos, self.head_radius)

        # Happy face!
        eye_offset = 10
        eye_y = head_pos[1] - 5

        # Eyes
        pygame.draw.circle(surface, (255, 255, 255),
                          (head_pos[0] - eye_offset, eye_y), 8)
        pygame.draw.circle(surface, (255, 255, 255),
                          (head_pos[0] + eye_offset, eye_y), 8)
        pygame.draw.circle(surface, (50, 50, 50),
                          (head_pos[0] - eye_offset, eye_y), 4)
        pygame.draw.circle(surface, (50, 50, 50),
                          (head_pos[0] + eye_offset, eye_y), 4)

        # Smile
        smile_rect = pygame.Rect(head_pos[0] - 12, head_pos[1], 24, 16)
        pygame.draw.arc(surface, (50, 50, 50), smile_rect, 3.4, 6.0, 3)

    def get_hand_radius(self) -> int:
        """Get the hand collision radius."""
        return self.hand_radius


class TargetRenderer:
    """Renders dance move targets on screen."""

    def __init__(self):
        self.pulse_time = 0.0
        self.target_radius = 50  # Visual target radius

    def render_targets(self, surface: pygame.Surface,
                       left_target: Optional[Tuple[int, int]],
                       right_target: Optional[Tuple[int, int]],
                       left_hit: bool, right_hit: bool,
                       time_progress: float):
        """Render the current move targets."""
        self.pulse_time += 0.15

        # Pulsing effect
        pulse = math.sin(self.pulse_time) * 0.2 + 1.0
        urgency_pulse = 1.0 + (time_progress * 0.5)  # Gets bigger as time runs out

        if left_target:
            self._draw_target(surface, left_target, "L", left_hit,
                            pulse * urgency_pulse, time_progress)

        if right_target:
            self._draw_target(surface, right_target, "R", right_hit,
                            pulse * urgency_pulse, time_progress)

    def _draw_target(self, surface: pygame.Surface, pos: Tuple[int, int],
                     label: str, is_hit: bool, pulse: float, time_progress: float):
        """Draw a single target."""
        radius = int(self.target_radius * pulse)

        # Color based on state
        if is_hit:
            # Golden color when hit!
            color = (255, 215, 0)  # Gold
            inner_color = (255, 240, 150)  # Light gold
            glow_color = (255, 200, 50)  # Golden glow
        elif time_progress > 0.75:
            # Urgent - running out of time
            color = DancerColors.TARGET_MISS
            inner_color = (255, 150, 150)
            glow_color = color
        else:
            color = DancerColors.TARGET_ACTIVE
            inner_color = (255, 255, 200)
            glow_color = color

        # Outer glow ring - bigger and brighter when hit
        glow_rings = 5 if is_hit else 3
        for i in range(glow_rings):
            ring_radius = radius + 10 + i * 8
            alpha = 150 - i * 25 if is_hit else 100 - i * 30
            ring_color = (*glow_color[:3],) if len(glow_color) == 3 else glow_color
            pygame.draw.circle(surface, ring_color, pos, ring_radius, 4 if is_hit else 3)

        # Main target circle
        pygame.draw.circle(surface, color, pos, radius, 5 if is_hit else 4)

        # Inner circle - filled with gold when hit
        pygame.draw.circle(surface, inner_color, pos, radius - 15, 0)
        pygame.draw.circle(surface, color, pos, radius - 15, 2)

        # Center dot
        pygame.draw.circle(surface, color, pos, 10 if is_hit else 8)

        # Label or star when hit
        font = pygame.font.Font(None, 36)
        if is_hit:
            # Show star instead of L/R
            text = font.render("*", True, (180, 140, 0))
        else:
            text = font.render(label, True, (50, 50, 50))
        text_rect = text.get_rect(center=pos)
        surface.blit(text, text_rect)

        # Celebration text if hit
        if is_hit:
            check_font = pygame.font.Font(None, 48)
            check = check_font.render("POP!", True, (255, 200, 0))
            check_rect = check.get_rect(center=(pos[0], pos[1] - radius - 25))
            surface.blit(check, check_rect)

    def render_countdown_ring(self, surface: pygame.Surface,
                              center: Tuple[int, int], time_remaining: float,
                              max_time: float):
        """Render a countdown ring around a target."""
        if max_time <= 0:
            return

        progress = time_remaining / max_time
        radius = self.target_radius + 25

        # Draw arc based on time remaining
        if progress > 0:
            start_angle = -math.pi / 2
            end_angle = start_angle + (progress * 2 * math.pi)

            # Color transitions from green to red
            if progress > 0.5:
                color = (100, 255, 100)
            elif progress > 0.25:
                color = (255, 255, 100)
            else:
                color = (255, 100, 100)

            rect = pygame.Rect(center[0] - radius, center[1] - radius,
                              radius * 2, radius * 2)
            pygame.draw.arc(surface, color, rect, start_angle, end_angle, 5)


class Particle:
    """A single particle for effects."""

    def __init__(self, x: float, y: float, vx: float, vy: float,
                 color: Tuple[int, int, int], size: float, lifetime: float,
                 particle_type: str = "confetti"):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.size = size
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.particle_type = particle_type
        self.rotation = random.random() * 360
        self.rotation_speed = random.random() * 10 - 5

    def update(self, dt: float) -> bool:
        """Update particle. Returns False if dead."""
        self.lifetime -= dt
        if self.lifetime <= 0:
            return False

        # Physics
        self.x += self.vx * dt
        self.y += self.vy * dt

        if self.particle_type == "confetti":
            self.vy += 200 * dt  # Gravity
            self.vx *= 0.99  # Air resistance
            self.rotation += self.rotation_speed
        elif self.particle_type == "snowflake":
            self.vy += 20 * dt  # Gentle fall
            self.x += math.sin(self.y / 30) * 0.5  # Drift
            self.rotation += self.rotation_speed * 0.3

        return True

    def draw(self, surface: pygame.Surface):
        """Draw the particle."""
        alpha = self.lifetime / self.max_lifetime
        size = int(self.size * alpha)
        if size < 1:
            return

        if self.particle_type == "confetti":
            # Confetti rectangles
            rect_surf = pygame.Surface((size * 2, size), pygame.SRCALPHA)
            color_alpha = (*self.color, int(255 * alpha))
            pygame.draw.rect(rect_surf, color_alpha, (0, 0, size * 2, size))
            rotated = pygame.transform.rotate(rect_surf, self.rotation)
            rect = rotated.get_rect(center=(int(self.x), int(self.y)))
            surface.blit(rotated, rect)
        elif self.particle_type == "snowflake":
            # Snowflake circles with sparkle
            color_alpha = (*self.color, int(200 * alpha))
            pygame.draw.circle(surface, color_alpha, (int(self.x), int(self.y)), size)
            # Inner sparkle
            if size > 2:
                pygame.draw.circle(surface, (255, 255, 255),
                                 (int(self.x), int(self.y)), max(1, size // 2))


class ParticleSystem:
    """Manages particle effects for celebrations."""

    # Christmas colors
    CONFETTI_COLORS = [
        (255, 215, 0),   # Gold
        (255, 0, 0),     # Red
        (0, 255, 0),     # Green
        (255, 255, 255), # White
        (255, 100, 100), # Light red
        (100, 255, 100), # Light green
    ]

    SNOWFLAKE_COLORS = [
        (255, 255, 255),  # White
        (200, 220, 255),  # Light blue
        (220, 240, 255),  # Ice blue
    ]

    def __init__(self):
        self.particles: List[Particle] = []
        self.snowflakes_enabled = False
        self.snowflake_timer = 0.0

    def spawn_confetti(self, x: float, y: float, count: int = 30):
        """Spawn confetti burst at position."""
        import random
        for _ in range(count):
            angle = random.random() * 2 * math.pi
            speed = random.random() * 400 + 200
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed - 200  # Bias upward
            color = random.choice(self.CONFETTI_COLORS)
            size = random.random() * 8 + 4
            lifetime = random.random() * 1.5 + 1.0

            self.particles.append(Particle(x, y, vx, vy, color, size, lifetime, "confetti"))

    def spawn_snowflakes(self, screen_width: int, count: int = 3):
        """Spawn snowflakes from top of screen."""
        import random
        for _ in range(count):
            x = random.random() * screen_width
            y = -10
            vx = random.random() * 20 - 10
            vy = random.random() * 50 + 30
            color = random.choice(self.SNOWFLAKE_COLORS)
            size = random.random() * 6 + 3
            lifetime = random.random() * 5 + 3

            self.particles.append(Particle(x, y, vx, vy, color, size, lifetime, "snowflake"))

    def enable_snowflakes(self, enabled: bool = True):
        """Enable or disable continuous snowfall."""
        self.snowflakes_enabled = enabled

    def update(self, dt: float, screen_width: int = 1280):
        """Update all particles."""
        # Update existing particles
        self.particles = [p for p in self.particles if p.update(dt)]

        # Spawn snowflakes if enabled
        if self.snowflakes_enabled:
            self.snowflake_timer += dt
            if self.snowflake_timer >= 0.1:  # Spawn every 0.1 seconds
                self.snowflake_timer = 0.0
                self.spawn_snowflakes(screen_width, 2)

    def draw(self, surface: pygame.Surface):
        """Draw all particles."""
        for particle in self.particles:
            particle.draw(surface)

    def clear(self):
        """Clear all particles."""
        self.particles.clear()
