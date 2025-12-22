"""
Avatar Rendering System - Bluey Character Sprites
Renders Bluey, Bingo, Bandit, and Chilli with limb extensions that follow body tracking.
"""

import pygame
import math
import os
from typing import Optional, Tuple, List, Dict
from player_detection import PlayerLandmarks


class CharacterConfig:
    """Configuration for each character sprite."""

    # Character order: Player 1 = Bluey, 2 = Bingo, 3 = Bandit (Dad), 4 = Chilli (Mum)
    CHARACTERS = [
        {
            'name': 'bluey',
            'file': 'bluey.png',
            'fur_color': (147, 200, 230),      # Light blue
            'fur_dark': (90, 140, 180),        # Darker blue
            'paw_color': (200, 225, 240),      # Light paw
            'outline': (50, 80, 120),
            # Approximate positions in sprite (as ratios of sprite size)
            'left_shoulder': (0.22, 0.42),     # Where left arm connects
            'right_shoulder': (0.78, 0.42),    # Where right arm connects
            'left_hip': (0.30, 0.75),          # Where left leg connects
            'right_hip': (0.70, 0.75),         # Where right leg connects
        },
        {
            'name': 'bingo',
            'file': 'bingo.png',
            'fur_color': (230, 170, 130),      # Orange/tan
            'fur_dark': (190, 120, 80),        # Darker orange
            'paw_color': (250, 240, 220),      # Light paw
            'outline': (120, 70, 40),
            'left_shoulder': (0.20, 0.45),
            'right_shoulder': (0.80, 0.45),
            'left_hip': (0.32, 0.78),
            'right_hip': (0.68, 0.78),
        },
        {
            'name': 'bandit',
            'file': 'bandit.png',
            'fur_color': (160, 200, 230),      # Light blue (dad)
            'fur_dark': (60, 80, 100),         # Dark blue/black
            'paw_color': (240, 240, 245),      # White paws
            'outline': (40, 50, 70),
            'left_shoulder': (0.18, 0.40),
            'right_shoulder': (0.75, 0.40),
            'left_hip': (0.28, 0.78),
            'right_hip': (0.55, 0.78),
        },
        {
            'name': 'chilli',
            'file': 'chilli.png',
            'fur_color': (235, 180, 150),      # Orange/peach (mum)
            'fur_dark': (160, 100, 70),        # Brown
            'paw_color': (250, 245, 235),      # Light paw
            'outline': (100, 60, 40),
            'left_shoulder': (0.20, 0.38),
            'right_shoulder': (0.72, 0.38),
            'left_hip': (0.25, 0.80),
            'right_hip': (0.50, 0.80),
        },
    ]


class AvatarRenderer:
    """Renders Bluey character sprites with dynamic limb extensions."""

    def __init__(self, screen_width: int, screen_height: int):
        self.screen_width = screen_width
        self.screen_height = screen_height

        # Smoothing for positions
        self.smooth_factor = 0.4
        self.previous_positions: Dict[str, Tuple[float, float]] = {}

        # Load character sprites
        self.sprites = {}
        self.configs = {}
        self._load_sprites()

    def _load_sprites(self):
        """Load all character sprite images."""
        assets_dir = os.path.join(os.path.dirname(__file__), 'assets')

        for config in CharacterConfig.CHARACTERS:
            name = config['name']
            sprite_path = os.path.join(assets_dir, config['file'])

            if os.path.exists(sprite_path):
                try:
                    sprite = pygame.image.load(sprite_path).convert_alpha()
                    self.sprites[name] = sprite
                    self.configs[name] = config
                    print(f"Loaded {name} sprite: {sprite.get_size()}")
                except Exception as e:
                    print(f"Could not load {name} sprite: {e}")

    def render_player(self, surface: pygame.Surface, player: PlayerLandmarks,
                     player_index: int = 0):
        """Render a character with limb extensions."""
        if not player.is_visible:
            return

        # Get character config
        config_index = player_index % len(CharacterConfig.CHARACTERS)
        config = CharacterConfig.CHARACTERS[config_index]
        char_name = config['name']

        # Get smoothed positions
        positions = self._get_smoothed_positions(player, player_index)
        if not positions:
            return

        # Calculate body metrics
        body_scale = self._calculate_body_scale(positions)
        sprite_bounds = self._calculate_sprite_bounds(positions, body_scale)

        if not sprite_bounds:
            return

        sprite_x, sprite_y, sprite_width, sprite_height = sprite_bounds

        # Calculate limb thickness based on sprite size
        limb_thickness = max(12, int(sprite_width * 0.08))
        paw_size = max(20, int(sprite_width * 0.12))

        # Calculate where limbs connect on the sprite
        left_shoulder_pos = (
            sprite_x + sprite_width * config['left_shoulder'][0],
            sprite_y + sprite_height * config['left_shoulder'][1]
        )
        right_shoulder_pos = (
            sprite_x + sprite_width * config['right_shoulder'][0],
            sprite_y + sprite_height * config['right_shoulder'][1]
        )
        left_hip_pos = (
            sprite_x + sprite_width * config['left_hip'][0],
            sprite_y + sprite_height * config['left_hip'][1]
        )
        right_hip_pos = (
            sprite_x + sprite_width * config['right_hip'][0],
            sprite_y + sprite_height * config['right_hip'][1]
        )

        # Draw limbs BEHIND the sprite
        # Draw arms only (no legs)
        if positions.get('left_hand'):
            self._draw_limb(surface, left_shoulder_pos, positions['left_hand'], limb_thickness, config)
            self._draw_paw(surface, positions['left_hand'], paw_size, config)

        if positions.get('right_hand'):
            self._draw_limb(surface, right_shoulder_pos, positions['right_hand'], limb_thickness, config)
            self._draw_paw(surface, positions['right_hand'], paw_size, config)

        # Draw the sprite on top
        if char_name in self.sprites:
            sprite = self.sprites[char_name]
            scaled_sprite = pygame.transform.smoothscale(sprite, (int(sprite_width), int(sprite_height)))
            surface.blit(scaled_sprite, (int(sprite_x), int(sprite_y)))

    def _calculate_sprite_bounds(self, positions: Dict, scale: float) -> Optional[Tuple[float, float, float, float]]:
        """Calculate where to position and how to size the sprite."""
        neck = positions.get('neck')
        hip_center = positions.get('hip_center')
        nose = positions.get('nose')

        if not neck:
            return None

        # Calculate body center
        if hip_center:
            body_center_x = (neck[0] + hip_center[0]) / 2
            body_center_y = (neck[1] + hip_center[1]) / 2
            body_height = abs(hip_center[1] - neck[1]) * 2.8
        else:
            body_center_x = neck[0]
            body_center_y = neck[1] + 100
            body_height = 350 * scale

        # If we have nose, extend up to include head
        if nose:
            head_space = abs(neck[1] - nose[1]) * 1.5
            body_height = body_height + head_space
            body_center_y = body_center_y - head_space * 0.2

        # Scale down to 50% size
        body_height = body_height * 0.5

        # Calculate dimensions maintaining aspect ratio (roughly 0.67 width:height for these sprites)
        aspect_ratio = 0.67
        sprite_height = body_height
        sprite_width = sprite_height * aspect_ratio

        sprite_x = body_center_x - sprite_width / 2
        sprite_y = body_center_y - sprite_height / 2 - sprite_height * 0.05

        return (sprite_x, sprite_y, sprite_width, sprite_height)

    def _draw_limb(self, surface: pygame.Surface, start: Tuple[float, float],
                   end: Tuple[float, float], thickness: int, config: Dict, is_leg: bool = False):
        """Draw a limb extension from sprite to detected position."""
        start_pos = (int(start[0]), int(start[1]))
        end_pos = (int(end[0]), int(end[1]))

        fur_color = config['fur_color']
        fur_dark = config['fur_dark']
        outline_color = config['outline']

        # Calculate direction and perpendicular
        dx = end_pos[0] - start_pos[0]
        dy = end_pos[1] - start_pos[1]
        length = max(1, math.sqrt(dx * dx + dy * dy))
        nx, ny = -dy / length, dx / length

        half_width = thickness // 2

        # Create limb polygon
        points = [
            (start_pos[0] + nx * half_width, start_pos[1] + ny * half_width),
            (start_pos[0] - nx * half_width, start_pos[1] - ny * half_width),
            (end_pos[0] - nx * half_width, end_pos[1] - ny * half_width),
            (end_pos[0] + nx * half_width, end_pos[1] + ny * half_width),
        ]

        # Draw shadow
        shadow_offset = 3
        shadow_points = [(p[0] + shadow_offset, p[1] + shadow_offset) for p in points]
        pygame.draw.polygon(surface, self._darken(fur_color, 0.4), shadow_points)

        # Draw main limb
        pygame.draw.polygon(surface, fur_color, points)

        # Draw stripe/marking for legs
        if is_leg and length > 30:
            stripe_start = (
                start_pos[0] + dx * 0.6,
                start_pos[1] + dy * 0.6
            )
            stripe_end = (
                start_pos[0] + dx * 0.8,
                start_pos[1] + dy * 0.8
            )
            stripe_points = [
                (stripe_start[0] + nx * half_width * 0.9, stripe_start[1] + ny * half_width * 0.9),
                (stripe_start[0] - nx * half_width * 0.9, stripe_start[1] - ny * half_width * 0.9),
                (stripe_end[0] - nx * half_width * 0.9, stripe_end[1] - ny * half_width * 0.9),
                (stripe_end[0] + nx * half_width * 0.9, stripe_end[1] + ny * half_width * 0.9),
            ]
            pygame.draw.polygon(surface, config['paw_color'], stripe_points)

        # Draw outline
        pygame.draw.polygon(surface, outline_color, points, 2)

        # Draw joint circles for smooth connections
        pygame.draw.circle(surface, fur_color, start_pos, half_width)
        pygame.draw.circle(surface, outline_color, start_pos, half_width, 2)
        pygame.draw.circle(surface, fur_color, end_pos, half_width)
        pygame.draw.circle(surface, outline_color, end_pos, half_width, 2)

    def _draw_paw(self, surface: pygame.Surface, position: Tuple[float, float],
                  size: int, config: Dict, is_foot: bool = False):
        """Draw a cartoon paw at the given position."""
        x, y = int(position[0]), int(position[1])

        paw_color = config['paw_color']
        outline_color = config['outline']

        # Draw shadow
        pygame.draw.ellipse(surface, self._darken(paw_color, 0.5),
                           (x - size // 2 + 3, y - size // 2 + 3, size, size))

        # Draw main paw
        pygame.draw.ellipse(surface, paw_color,
                           (x - size // 2, y - size // 2, size, size))

        # Draw paw pads
        pad_color = (70, 70, 80)
        if is_foot:
            # Larger central pad for feet
            pygame.draw.ellipse(surface, pad_color,
                              (x - size // 4, y - size // 6, size // 2, size // 3))
        else:
            # Three toe pads for hands
            pad_size = size // 5
            for offset in [-1, 0, 1]:
                pad_x = x + offset * (size // 4)
                pad_y = y - size // 6
                pygame.draw.circle(surface, pad_color, (pad_x, pad_y), pad_size // 2)

        # Draw outline
        pygame.draw.ellipse(surface, outline_color,
                           (x - size // 2, y - size // 2, size, size), 2)

    def _get_smoothed_positions(self, player: PlayerLandmarks,
                                player_index: int) -> Optional[Dict]:
        """Get smoothed positions for all body parts."""
        prefix = f"p{player_index}_"

        def smooth(point: Optional[Tuple[float, float]], key: str) -> Optional[Tuple[float, float]]:
            if point is None:
                return self.previous_positions.get(prefix + key)

            full_key = prefix + key
            if full_key in self.previous_positions:
                prev = self.previous_positions[full_key]
                smoothed = (
                    prev[0] + (point[0] - prev[0]) * self.smooth_factor,
                    prev[1] + (point[1] - prev[1]) * self.smooth_factor
                )
                self.previous_positions[full_key] = smoothed
                return smoothed

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

        if not positions['left_shoulder'] or not positions['right_shoulder']:
            return None

        # Calculate neck position
        positions['neck'] = (
            (positions['left_shoulder'][0] + positions['right_shoulder'][0]) / 2,
            (positions['left_shoulder'][1] + positions['right_shoulder'][1]) / 2
        )

        # Calculate hip center
        if positions['left_hip'] and positions['right_hip']:
            positions['hip_center'] = (
                (positions['left_hip'][0] + positions['right_hip'][0]) / 2,
                (positions['left_hip'][1] + positions['right_hip'][1]) / 2
            )
        else:
            positions['hip_center'] = (
                positions['neck'][0],
                positions['neck'][1] + 150
            )

        return positions

    def _calculate_body_scale(self, positions: Dict) -> float:
        """Calculate scale factor based on detected body size."""
        if positions['left_shoulder'] and positions['right_shoulder']:
            shoulder_width = abs(positions['right_shoulder'][0] - positions['left_shoulder'][0])
            return max(0.5, min(2.0, shoulder_width / 150))
        return 1.0

    def _darken(self, color: Tuple[int, int, int], factor: float) -> Tuple[int, int, int]:
        """Darken a color by a factor."""
        return (int(color[0] * factor), int(color[1] * factor), int(color[2] * factor))

    def get_hand_positions(self, player: PlayerLandmarks) -> List[Tuple[float, float]]:
        """Get hand positions for collision detection."""
        positions = []
        if player.left_hand:
            positions.append(player.left_hand)
        if player.right_hand:
            positions.append(player.right_hand)
        return positions

    def get_collision_radius(self) -> float:
        """Get collision radius for hands."""
        return 35


# Keep BlueyColors for backwards compatibility
class BlueyColors:
    CHARACTERS = CharacterConfig.CHARACTERS
    CHARACTER_NAMES = ['Bluey', 'Bingo', 'Bandit', 'Chilli']
