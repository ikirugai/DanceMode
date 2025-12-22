"""
Asset Generator
Generates Bluey-inspired cartoon graphics programmatically.
Creates the iconic Bluey park background and game elements.
"""

import pygame
import math
import random
import os
from typing import Tuple


# Bluey-inspired color palette
class Palette:
    # Sky colors (bright Australian sky)
    SKY_TOP = (120, 200, 255)         # Bright blue top
    SKY_BOTTOM = (180, 230, 255)      # Lighter blue horizon

    # Blues
    SKY_BLUE = (108, 172, 228)
    DEEP_BLUE = (59, 108, 180)
    PALE_BLUE = (168, 216, 240)
    NAVY = (45, 80, 140)

    # Warm colors
    ORANGE = (245, 132, 38)
    CORAL = (255, 140, 148)
    WARM_YELLOW = (255, 218, 107)
    SUNSET_ORANGE = (255, 180, 100)

    # Environment - Bluey park greens
    GRASS_BRIGHT = (140, 200, 80)     # Bright grass (foreground)
    GRASS_GREEN = (120, 180, 70)      # Main grass
    GRASS_DARK = (90, 150, 50)        # Darker grass (shadows/hills)
    GRASS_LIGHT = (170, 220, 110)     # Light grass highlights

    # Tree colors (eucalyptus style)
    TREE_TRUNK = (140, 100, 70)       # Brown trunk
    TREE_TRUNK_DARK = (100, 70, 50)   # Dark trunk shadow
    TREE_LEAVES = (80, 150, 80)       # Green leaves
    TREE_LEAVES_LIGHT = (120, 180, 100)  # Light leaf highlights
    TREE_LEAVES_DARK = (50, 110, 50)  # Dark leaf shadows

    # Bush colors
    BUSH_GREEN = (70, 140, 70)
    BUSH_LIGHT = (100, 170, 90)

    # Flowers
    FLOWER_YELLOW = (255, 230, 100)
    FLOWER_PINK = (255, 150, 180)
    FLOWER_WHITE = (255, 255, 255)
    FLOWER_PURPLE = (180, 130, 200)

    # Balloon colors
    BALLOON_RED = (255, 100, 100)
    BALLOON_PINK = (255, 180, 200)
    BALLOON_HIGHLIGHT = (255, 255, 255)

    # UI
    WHITE = (255, 255, 255)
    BLACK = (40, 40, 50)
    CREAM = (255, 250, 240)


class AssetGenerator:
    """Generates game assets with a Bluey-inspired cartoon style."""

    def __init__(self, screen_width: int, screen_height: int):
        """Initialize the asset generator."""
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.assets = {}
        # Use a seed for consistent "random" elements
        random.seed(42)

    def generate_all(self):
        """Generate all game assets."""
        self.assets['background'] = self._create_bluey_park_background()
        self.assets['balloon'] = self._create_balloon(100)
        self.assets['balloon_popped'] = self._create_popped_balloon(100)
        self.assets['cloud1'] = self._create_fluffy_cloud(150, 80)
        self.assets['cloud2'] = self._create_fluffy_cloud(120, 65)
        self.assets['sun'] = self._create_sun(90)
        self.assets['wind_arrow'] = self._create_wind_arrow(60)

        return self.assets

    def _create_bluey_park_background(self) -> pygame.Surface:
        """Create the Bluey background - uses house.jpg if available, otherwise generates park."""
        surface = pygame.Surface((self.screen_width, self.screen_height))

        # Try to load house.jpg background
        assets_dir = os.path.join(os.path.dirname(__file__), 'assets')
        house_path = os.path.join(assets_dir, 'house.jpg')

        if os.path.exists(house_path):
            try:
                house_img = pygame.image.load(house_path).convert()
                # Scale to fit screen while maintaining aspect ratio, then crop/fit
                img_width, img_height = house_img.get_size()
                screen_ratio = self.screen_width / self.screen_height
                img_ratio = img_width / img_height

                if img_ratio > screen_ratio:
                    # Image is wider - scale by height and crop width
                    new_height = self.screen_height
                    new_width = int(img_width * (self.screen_height / img_height))
                    scaled = pygame.transform.smoothscale(house_img, (new_width, new_height))
                    x_offset = (new_width - self.screen_width) // 2
                    surface.blit(scaled, (-x_offset, 0))
                else:
                    # Image is taller - scale by width and crop height
                    new_width = self.screen_width
                    new_height = int(img_height * (self.screen_width / img_width))
                    scaled = pygame.transform.smoothscale(house_img, (new_width, new_height))
                    y_offset = (new_height - self.screen_height) // 2
                    surface.blit(scaled, (0, -y_offset))

                print(f"Loaded house.jpg background: {img_width}x{img_height}")
                return surface
            except Exception as e:
                print(f"Could not load house.jpg: {e}, generating park background")

        # Fallback: generate park background procedurally
        ground_y = self.screen_height - 120  # Ground level

        # 1. Draw gradient sky
        self._draw_sky_gradient(surface, ground_y)

        # 2. Draw distant hills (background layer)
        self._draw_distant_hills(surface, ground_y)

        # 3. Draw the big iconic tree on the left
        self._draw_big_tree(surface, 150, ground_y)

        # 4. Draw another tree on the right
        self._draw_medium_tree(surface, self.screen_width - 200, ground_y)

        # 5. Draw bushes
        self._draw_bushes(surface, ground_y)

        # 6. Draw main grass ground with rolling hills
        self._draw_grass_ground(surface, ground_y)

        # 7. Draw grass details and flowers
        self._draw_grass_details(surface, ground_y)

        return surface

    def _draw_sky_gradient(self, surface: pygame.Surface, ground_y: int):
        """Draw the bright Australian sky gradient."""
        for y in range(ground_y):
            ratio = y / ground_y
            # Interpolate from top to bottom
            r = int(Palette.SKY_TOP[0] + (Palette.SKY_BOTTOM[0] - Palette.SKY_TOP[0]) * ratio)
            g = int(Palette.SKY_TOP[1] + (Palette.SKY_BOTTOM[1] - Palette.SKY_TOP[1]) * ratio)
            b = int(Palette.SKY_TOP[2] + (Palette.SKY_BOTTOM[2] - Palette.SKY_TOP[2]) * ratio)
            pygame.draw.line(surface, (r, g, b), (0, y), (self.screen_width, y))

    def _draw_distant_hills(self, surface: pygame.Surface, ground_y: int):
        """Draw rolling hills in the background."""
        # Far distant hill (lighter)
        hill_color = (160, 210, 140)
        points = [(0, ground_y - 40)]
        for x in range(0, self.screen_width + 50, 50):
            y_offset = math.sin(x * 0.008) * 30 + math.sin(x * 0.015) * 15
            points.append((x, ground_y - 60 + y_offset))
        points.append((self.screen_width, ground_y - 40))
        points.append((self.screen_width, ground_y))
        points.append((0, ground_y))
        pygame.draw.polygon(surface, hill_color, points)

        # Closer hill (darker green)
        hill_color2 = (130, 190, 100)
        points2 = [(0, ground_y - 20)]
        for x in range(0, self.screen_width + 50, 50):
            y_offset = math.sin(x * 0.012 + 1) * 25 + math.sin(x * 0.02) * 10
            points2.append((x, ground_y - 35 + y_offset))
        points2.append((self.screen_width, ground_y - 20))
        points2.append((self.screen_width, ground_y))
        points2.append((0, ground_y))
        pygame.draw.polygon(surface, hill_color2, points2)

    def _draw_big_tree(self, surface: pygame.Surface, x: int, ground_y: int):
        """Draw the iconic big Bluey tree with spread branches."""
        trunk_width = 45
        trunk_height = 250

        # Tree trunk shadow
        trunk_shadow = [
            (x - trunk_width//2 + 8, ground_y),
            (x - trunk_width//3 + 8, ground_y - trunk_height),
            (x + trunk_width//3 + 8, ground_y - trunk_height),
            (x + trunk_width//2 + 8, ground_y),
        ]
        pygame.draw.polygon(surface, Palette.TREE_TRUNK_DARK, trunk_shadow)

        # Main trunk
        trunk_points = [
            (x - trunk_width//2, ground_y),
            (x - trunk_width//3, ground_y - trunk_height),
            (x + trunk_width//3, ground_y - trunk_height),
            (x + trunk_width//2, ground_y),
        ]
        pygame.draw.polygon(surface, Palette.TREE_TRUNK, trunk_points)

        # Trunk texture lines
        for i in range(5):
            line_y = ground_y - 40 - i * 45
            pygame.draw.line(surface, Palette.TREE_TRUNK_DARK,
                           (x - trunk_width//3 + 5, line_y),
                           (x + trunk_width//3 - 5, line_y + 10), 2)

        # Large leafy canopy (multiple overlapping circles)
        canopy_y = ground_y - trunk_height - 40
        canopy_radius = 120

        # Shadow layer
        shadow_offset = 8
        canopy_circles = [
            (x, canopy_y, canopy_radius),
            (x - 80, canopy_y + 30, 70),
            (x + 80, canopy_y + 30, 70),
            (x - 50, canopy_y - 40, 60),
            (x + 50, canopy_y - 40, 60),
            (x, canopy_y - 60, 50),
            (x - 100, canopy_y + 60, 55),
            (x + 100, canopy_y + 60, 55),
        ]

        # Draw shadow
        for cx, cy, r in canopy_circles:
            pygame.draw.circle(surface, Palette.TREE_LEAVES_DARK,
                             (cx + shadow_offset, cy + shadow_offset), r)

        # Draw main canopy
        for cx, cy, r in canopy_circles:
            pygame.draw.circle(surface, Palette.TREE_LEAVES, (cx, cy), r)

        # Draw highlights
        for cx, cy, r in canopy_circles:
            pygame.draw.circle(surface, Palette.TREE_LEAVES_LIGHT,
                             (cx - r//4, cy - r//4), r//2)

    def _draw_medium_tree(self, surface: pygame.Surface, x: int, ground_y: int):
        """Draw a smaller tree for the right side."""
        trunk_width = 30
        trunk_height = 180

        # Trunk
        trunk_points = [
            (x - trunk_width//2, ground_y),
            (x - trunk_width//3, ground_y - trunk_height),
            (x + trunk_width//3, ground_y - trunk_height),
            (x + trunk_width//2, ground_y),
        ]
        pygame.draw.polygon(surface, Palette.TREE_TRUNK, trunk_points)

        # Canopy
        canopy_y = ground_y - trunk_height - 30
        canopy_circles = [
            (x, canopy_y, 80),
            (x - 50, canopy_y + 20, 50),
            (x + 50, canopy_y + 20, 50),
            (x - 30, canopy_y - 30, 45),
            (x + 30, canopy_y - 30, 45),
        ]

        for cx, cy, r in canopy_circles:
            pygame.draw.circle(surface, Palette.TREE_LEAVES_DARK, (cx + 5, cy + 5), r)

        for cx, cy, r in canopy_circles:
            pygame.draw.circle(surface, Palette.TREE_LEAVES, (cx, cy), r)

        for cx, cy, r in canopy_circles:
            pygame.draw.circle(surface, Palette.TREE_LEAVES_LIGHT,
                             (cx - r//4, cy - r//4), r//3)

    def _draw_bushes(self, surface: pygame.Surface, ground_y: int):
        """Draw decorative bushes."""
        bush_positions = [
            (80, ground_y - 5, 40),
            (300, ground_y - 8, 35),
            (500, ground_y - 5, 45),
            (750, ground_y - 6, 38),
            (950, ground_y - 5, 42),
            (1150, ground_y - 7, 36),
        ]

        for bx, by, size in bush_positions:
            if bx < self.screen_width:
                # Bush shadow
                pygame.draw.ellipse(surface, Palette.BUSH_GREEN,
                                  (bx - size + 3, by - size//2 + 3, size * 2, size))
                # Main bush
                pygame.draw.ellipse(surface, Palette.BUSH_LIGHT,
                                  (bx - size, by - size//2, size * 2, size))
                # Highlight
                pygame.draw.ellipse(surface, (130, 190, 110),
                                  (bx - size//2, by - size//2, size, size//2))

    def _draw_grass_ground(self, surface: pygame.Surface, ground_y: int):
        """Draw the main grass ground with subtle hills."""
        # Main grass area
        grass_rect = pygame.Rect(0, ground_y, self.screen_width, self.screen_height - ground_y)
        pygame.draw.rect(surface, Palette.GRASS_GREEN, grass_rect)

        # Add rolling hill effect on top edge
        for x in range(0, self.screen_width, 3):
            hill_offset = math.sin(x * 0.02) * 8 + math.sin(x * 0.05) * 4
            pygame.draw.line(surface, Palette.GRASS_BRIGHT,
                           (x, ground_y + hill_offset),
                           (x, ground_y + hill_offset + 15))

    def _draw_grass_details(self, surface: pygame.Surface, ground_y: int):
        """Draw grass tufts and flowers."""
        # Grass tufts along the ground
        for x in range(20, self.screen_width - 20, 35):
            tuft_y = ground_y + 5 + (x * 7) % 15
            self._draw_grass_tuft(surface, x, tuft_y)

        # Flowers scattered on the grass
        flower_positions = [
            (120, ground_y + 40, Palette.FLOWER_YELLOW),
            (250, ground_y + 55, Palette.FLOWER_PINK),
            (380, ground_y + 35, Palette.FLOWER_WHITE),
            (520, ground_y + 50, Palette.FLOWER_PURPLE),
            (650, ground_y + 42, Palette.FLOWER_YELLOW),
            (780, ground_y + 58, Palette.FLOWER_PINK),
            (900, ground_y + 38, Palette.FLOWER_WHITE),
            (1050, ground_y + 48, Palette.FLOWER_YELLOW),
            (1180, ground_y + 52, Palette.FLOWER_PURPLE),
        ]

        for fx, fy, color in flower_positions:
            if fx < self.screen_width:
                self._draw_flower(surface, fx, fy, color)

    def _draw_grass_tuft(self, surface: pygame.Surface, x: int, y: int):
        """Draw a small grass tuft."""
        for i, offset in enumerate([-6, -3, 0, 3, 6]):
            height = 15 + (i % 3) * 5
            blade_color = Palette.GRASS_BRIGHT if i % 2 == 0 else Palette.GRASS_LIGHT
            points = [
                (x + offset - 2, y),
                (x + offset, y - height),
                (x + offset + 2, y),
            ]
            pygame.draw.polygon(surface, blade_color, points)

    def _draw_flower(self, surface: pygame.Surface, x: int, y: int, color: Tuple[int, int, int]):
        """Draw a simple cartoon flower."""
        # Stem
        pygame.draw.line(surface, Palette.GRASS_DARK, (x, y), (x, y - 15), 2)

        # Petals
        petal_size = 6
        for angle in range(0, 360, 72):
            rad = math.radians(angle)
            px = x + math.cos(rad) * 5
            py = y - 15 + math.sin(rad) * 5
            pygame.draw.circle(surface, color, (int(px), int(py)), petal_size)

        # Center
        pygame.draw.circle(surface, Palette.WARM_YELLOW, (x, y - 15), 4)

    def _create_balloon(self, size: int) -> pygame.Surface:
        """Create a cartoon balloon surface."""
        surface = pygame.Surface((size, size + 60), pygame.SRCALPHA)

        center_x = size // 2
        center_y = size // 2
        radius = size // 2 - 4

        # Balloon shadow
        pygame.draw.ellipse(surface, (*Palette.BALLOON_RED[:3], 100),
                           (center_x - radius + 6, center_y - radius + 6,
                            radius * 2, radius * 2 + 10))

        # Main balloon body (slightly oval)
        pygame.draw.ellipse(surface, Palette.BALLOON_RED,
                           (center_x - radius, center_y - radius,
                            radius * 2, radius * 2 + 10))

        # Balloon outline
        pygame.draw.ellipse(surface, Palette.NAVY,
                           (center_x - radius, center_y - radius,
                            radius * 2, radius * 2 + 10), 4)

        # Highlight (shine effect)
        highlight_radius = radius // 3
        pygame.draw.ellipse(surface, Palette.BALLOON_PINK,
                           (center_x - radius // 2, center_y - radius // 2,
                            highlight_radius, highlight_radius * 2))

        # Small white shine
        pygame.draw.circle(surface, Palette.BALLOON_HIGHLIGHT,
                          (center_x - radius // 3, center_y - radius // 3),
                          radius // 6)

        # Balloon knot
        knot_y = center_y + radius + 5
        pygame.draw.polygon(surface, Palette.BALLOON_RED, [
            (center_x - 8, knot_y),
            (center_x + 8, knot_y),
            (center_x, knot_y + 12),
        ])
        pygame.draw.polygon(surface, Palette.NAVY, [
            (center_x - 8, knot_y),
            (center_x + 8, knot_y),
            (center_x, knot_y + 12),
        ], 2)

        # String (curvy)
        prev_x, prev_y = center_x, knot_y + 12
        for i in range(30):
            y = knot_y + 12 + i * 1.5
            x = center_x + math.sin(i * 0.3) * 5
            pygame.draw.line(surface, Palette.NAVY, (prev_x, prev_y), (x, y), 2)
            prev_x, prev_y = x, y

        return surface

    def _create_popped_balloon(self, size: int) -> pygame.Surface:
        """Create a popped balloon effect."""
        surface = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
        center = size

        # Draw scattered pieces
        pieces = [
            (center - 30, center - 20, 15),
            (center + 25, center - 15, 12),
            (center - 10, center + 20, 18),
            (center + 35, center + 10, 10),
            (center - 35, center + 5, 14),
            (center + 5, center - 35, 11),
        ]

        for px, py, ps in pieces:
            points = []
            for i in range(6):
                angle = i * math.pi / 3 + (px % 10) * 0.1
                r = ps * (0.7 + (py % 5) * 0.1)
                points.append((px + math.cos(angle) * r,
                              py + math.sin(angle) * r))
            pygame.draw.polygon(surface, Palette.BALLOON_RED, points)
            pygame.draw.polygon(surface, Palette.NAVY, points, 2)

        # "POP!" text effect
        font = pygame.font.Font(None, 48)
        text = font.render("POP!", True, Palette.ORANGE)
        text_rect = text.get_rect(center=(center, center))

        # Text outline
        for dx, dy in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
            outline = font.render("POP!", True, Palette.NAVY)
            surface.blit(outline, (text_rect.x + dx, text_rect.y + dy))

        surface.blit(text, text_rect)

        return surface

    def _create_fluffy_cloud(self, width: int, height: int) -> pygame.Surface:
        """Create a fluffy Bluey-style cloud."""
        surface = pygame.Surface((width + 20, height + 20), pygame.SRCALPHA)

        # More circles for fluffier cloud
        circles = [
            (width // 4 + 10, height // 2 + 10, height // 2.5),
            (width // 2 + 10, height // 3 + 10, height // 2),
            (width * 3 // 4 + 10, height // 2 + 10, height // 2.5),
            (width // 3 + 10, height // 2 + 5, height // 3),
            (width * 2 // 3 + 10, height // 2 + 5, height // 3),
            (width // 2 + 10, height // 2 + 10, height // 3),
        ]

        # Shadow
        for cx, cy, r in circles:
            pygame.draw.circle(surface, (220, 235, 250),
                              (int(cx) + 4, int(cy) + 4), int(r))

        # White cloud
        for cx, cy, r in circles:
            pygame.draw.circle(surface, Palette.WHITE,
                              (int(cx), int(cy)), int(r))

        return surface

    def _create_sun(self, size: int) -> pygame.Surface:
        """Create a cartoon sun with a happy face."""
        surface = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
        center = size

        # Sun rays
        ray_color = (255, 230, 130)
        for i in range(12):
            angle = i * math.pi / 6
            inner_r = size // 2 + 8
            outer_r = size - 3
            x1 = center + math.cos(angle) * inner_r
            y1 = center + math.sin(angle) * inner_r
            x2 = center + math.cos(angle) * outer_r
            y2 = center + math.sin(angle) * outer_r
            pygame.draw.line(surface, ray_color, (x1, y1), (x2, y2), 8)

        # Main sun circle
        pygame.draw.circle(surface, Palette.WARM_YELLOW, (center, center), size // 2)
        pygame.draw.circle(surface, Palette.ORANGE, (center, center), size // 2, 4)

        # Happy face
        eye_y = center - 8
        pygame.draw.circle(surface, Palette.BLACK, (center - 12, eye_y), 5)
        pygame.draw.circle(surface, Palette.BLACK, (center + 12, eye_y), 5)

        # Smile
        smile_rect = pygame.Rect(center - 15, center - 8, 30, 25)
        pygame.draw.arc(surface, Palette.BLACK, smile_rect,
                       math.pi + 0.2, 2 * math.pi - 0.2, 4)

        return surface

    def _create_wind_arrow(self, size: int) -> pygame.Surface:
        """Create a wind indicator arrow."""
        surface = pygame.Surface((size, size), pygame.SRCALPHA)

        arrow_points = [
            (5, size // 2 - 8),
            (size - 15, size // 2 - 8),
            (size - 15, size // 2 - 15),
            (size - 5, size // 2),
            (size - 15, size // 2 + 15),
            (size - 15, size // 2 + 8),
            (5, size // 2 + 8),
        ]

        pygame.draw.polygon(surface, Palette.PALE_BLUE, arrow_points)
        pygame.draw.polygon(surface, Palette.DEEP_BLUE, arrow_points, 3)

        # Wind swoosh lines
        for i, offset in enumerate([10, 0, -10]):
            start_x = 15 + i * 8
            pygame.draw.arc(surface, Palette.DEEP_BLUE,
                           (start_x, size // 2 + offset - 5, 12, 10),
                           0, math.pi, 2)

        return surface


def create_game_font(size: int) -> pygame.font.Font:
    """Create a font for game text (uses system font for compatibility)."""
    try:
        return pygame.font.SysFont('Comic Sans MS', size)
    except:
        try:
            return pygame.font.SysFont('Arial Rounded MT Bold', size)
        except:
            return pygame.font.Font(None, size)
