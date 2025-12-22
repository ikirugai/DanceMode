"""
Dancer Avatar Renderer
Renders a fun, colorful stick-figure dancer that follows body movements.
"""

import pygame
import math
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
        self.target_radius = 120  # Large visible target - matches hit detection

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
            color = DancerColors.TARGET_HIT
            inner_color = (150, 255, 150)
        elif time_progress > 0.75:
            # Urgent - running out of time
            color = DancerColors.TARGET_MISS
            inner_color = (255, 150, 150)
        else:
            color = DancerColors.TARGET_ACTIVE
            inner_color = (255, 255, 200)

        # Outer glow ring
        for i in range(3):
            ring_radius = radius + 10 + i * 8
            alpha = 100 - i * 30
            glow_color = (*color[:3], alpha) if len(color) == 3 else color
            pygame.draw.circle(surface, glow_color, pos, ring_radius, 3)

        # Main target circle
        pygame.draw.circle(surface, color, pos, radius, 4)

        # Inner circle
        pygame.draw.circle(surface, inner_color, pos, radius - 15, 0)
        pygame.draw.circle(surface, color, pos, radius - 15, 2)

        # Center dot
        pygame.draw.circle(surface, color, pos, 8)

        # Label
        font = pygame.font.Font(None, 36)
        text = font.render(label, True, (50, 50, 50))
        text_rect = text.get_rect(center=pos)
        surface.blit(text, text_rect)

        # Checkmark if hit
        if is_hit:
            check_font = pygame.font.Font(None, 48)
            check = check_font.render("OK!", True, (50, 150, 50))
            check_rect = check.get_rect(center=(pos[0], pos[1] - radius - 20))
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
