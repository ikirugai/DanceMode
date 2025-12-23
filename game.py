"""
DanceMode - A festive hand-tracking game!
Choose Christmas or Chanukkah theme and pop targets with your hands!
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
    MENU = "menu"  # Theme selection
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


class DanceModeGame:
    """Main game class for DanceMode!"""

    # Point values (same for both themes)
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

    # Theme configurations
    THEMES = {
        'christmas': {
            'name': 'Christmas',
            'bauble_name': 'Bauble',
            'elf_name': 'Elf',
            'santa_name': 'Santa',
            'grinch_name': 'Grinch',
            'colors': {
                'primary': (255, 50, 50),  # Red
                'secondary': (50, 255, 50),  # Green
                'accent': (255, 215, 0),  # Gold
            },
            'particle_colors': {
                'bauble': [(255, 215, 0), (255, 240, 150)],
                'elf': [(34, 139, 34), (255, 0, 0)],
                'santa': [(220, 20, 60), (255, 255, 255)],
                'grinch': [(0, 128, 0), (128, 128, 128)],
            },
        },
        'chanukkah': {
            'name': 'Chanukkah',
            'bauble_name': 'Sufganiyah',
            'elf_name': 'Star',
            'santa_name': 'Menorah',
            'grinch_name': 'Antiochus',
            'colors': {
                'primary': (0, 100, 200),  # Blue
                'secondary': (255, 255, 255),  # White
                'accent': (255, 215, 0),  # Gold
            },
            'particle_colors': {
                'bauble': [(210, 180, 140), (255, 200, 150)],  # Donut colors
                'elf': [(0, 100, 200), (255, 215, 0)],  # Blue and gold
                'santa': [(255, 215, 0), (255, 165, 0)],  # Gold flames
                'grinch': [(128, 0, 128), (100, 100, 100)],  # Purple/gray
            },
        },
        'kpop': {
            'name': 'K-Pop Demon Hunters',
            'bauble_name': 'Ramen',
            'elf_name': 'Light Stick',
            'santa_name': 'Derpy',
            'grinch_name': 'Saja Boys',
            'colors': {
                'primary': (255, 0, 128),  # Hot pink
                'secondary': (0, 255, 255),  # Cyan
                'accent': (255, 215, 0),  # Gold
            },
            'particle_colors': {
                'bauble': [(255, 200, 100), (255, 255, 200)],  # Noodle colors
                'elf': [(255, 0, 128), (0, 255, 255)],  # Pink and cyan
                'santa': [(100, 150, 255), (255, 165, 0)],  # Blue tiger, orange
                'grinch': [(50, 50, 50), (100, 50, 50)],  # Dark colors
            },
        },
    }

    def __init__(self, width: int = 1280, height: int = 720, fullscreen: bool = False):
        pygame.init()
        pygame.mixer.init()

        self.width = width
        self.height = height
        self.fullscreen = fullscreen

        # Theme selection
        self.theme = 'christmas'  # Default
        self.menu_selection = 0  # 0 = Christmas, 1 = Chanukkah

        # Allow resizing
        flags = pygame.DOUBLEBUF | pygame.RESIZABLE
        if fullscreen:
            flags = pygame.DOUBLEBUF | pygame.FULLSCREEN
            info = pygame.display.Info()
            self.width = info.current_w
            self.height = info.current_h

        self.screen = pygame.display.set_mode((self.width, self.height), flags)
        pygame.display.set_caption("DanceMode!")

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

        # Game state - start at menu
        self.state = GameState.MENU
        self.countdown_timer = 3.0
        self.game_timer = 60.0  # 1 minute rounds
        self.score = 0
        self.high_scores = {'christmas': 0, 'chanukkah': 0, 'kpop': 0}

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

        # Create sprites for all themes
        self.sprites = {}
        self._create_christmas_sprites()
        self._create_chanukkah_sprites()
        self._create_kpop_sprites()

    def _init_snowflakes(self, count: int):
        """Create background snowflakes/sparkles."""
        self.snowflakes.clear()
        for _ in range(count):
            self.snowflakes.append({
                'x': random.randint(0, self.width),
                'y': random.randint(-self.height, self.height),
                'size': random.randint(2, 6),
                'speed': random.random() * 50 + 20,
                'drift': random.random() * 2 - 1,
            })

    def _create_christmas_sprites(self):
        """Create Christmas-themed sprites."""
        # Bauble - golden ornament (2x size: 120x140)
        bauble = pygame.Surface((120, 140), pygame.SRCALPHA)
        pygame.draw.circle(bauble, (255, 215, 0), (60, 70), 50)  # Gold ball
        pygame.draw.circle(bauble, (255, 240, 150), (44, 56), 16)  # Highlight
        pygame.draw.rect(bauble, (200, 200, 200), (48, 10, 24, 20))  # Cap
        pygame.draw.circle(bauble, (150, 150, 150), (60, 6), 10)  # Loop
        self.sprites['christmas_bauble'] = bauble

        # Elf - green with pointy hat (2x size: 100x140)
        elf = pygame.Surface((100, 140), pygame.SRCALPHA)
        pygame.draw.ellipse(elf, (34, 139, 34), (20, 70, 60, 70))  # Body
        pygame.draw.circle(elf, (255, 218, 185), (50, 50), 30)  # Head
        pygame.draw.polygon(elf, (220, 20, 60), [(50, 0), (20, 50), (80, 50)])  # Hat
        pygame.draw.circle(elf, (255, 255, 0), (50, 4), 10)  # Hat tip
        pygame.draw.circle(elf, (0, 0, 0), (40, 46), 6)  # Eyes
        pygame.draw.circle(elf, (0, 0, 0), (60, 46), 6)
        pygame.draw.arc(elf, (0, 0, 0), (36, 50, 28, 20), 3.4, 6.0, 3)  # Smile
        pygame.draw.polygon(elf, (255, 218, 185), [(16, 44), (10, 36), (24, 50)])  # Ears
        pygame.draw.polygon(elf, (255, 218, 185), [(84, 44), (90, 36), (76, 50)])
        self.sprites['christmas_elf'] = elf

        # Santa - red suit, white beard (2x size: 140x180)
        santa = pygame.Surface((140, 180), pygame.SRCALPHA)
        pygame.draw.ellipse(santa, (220, 20, 60), (20, 80, 100, 100))  # Body
        pygame.draw.rect(santa, (0, 0, 0), (30, 110, 80, 16))  # Belt
        pygame.draw.rect(santa, (255, 215, 0), (60, 108, 20, 20))  # Buckle
        pygame.draw.circle(santa, (255, 218, 185), (70, 50), 36)  # Head
        pygame.draw.ellipse(santa, (255, 255, 255), (40, 56, 60, 50))  # Beard
        pygame.draw.polygon(santa, (220, 20, 60), [(70, 0), (30, 44), (110, 44)])  # Hat
        pygame.draw.circle(santa, (255, 255, 255), (70, 4), 12)
        pygame.draw.ellipse(santa, (255, 255, 255), (24, 36, 92, 20))  # Brim
        pygame.draw.circle(santa, (0, 0, 0), (56, 44), 6)  # Eyes
        pygame.draw.circle(santa, (0, 0, 0), (84, 44), 6)
        pygame.draw.circle(santa, (255, 150, 150), (70, 56), 8)  # Nose
        self.sprites['christmas_santa'] = santa

        # Grinch - green, mean face (2x size: 120x160)
        grinch = pygame.Surface((120, 160), pygame.SRCALPHA)
        pygame.draw.ellipse(grinch, (0, 128, 0), (20, 80, 80, 80))  # Body
        pygame.draw.circle(grinch, (0, 128, 0), (60, 56), 44)  # Head
        pygame.draw.line(grinch, (0, 80, 0), (30, 36), (56, 50), 6)  # Eyebrows
        pygame.draw.line(grinch, (0, 80, 0), (90, 36), (64, 50), 6)
        pygame.draw.circle(grinch, (255, 255, 0), (44, 50), 12)  # Eyes
        pygame.draw.circle(grinch, (255, 255, 0), (76, 50), 12)
        pygame.draw.circle(grinch, (255, 0, 0), (44, 50), 6)  # Red pupils
        pygame.draw.circle(grinch, (255, 0, 0), (76, 50), 6)
        pygame.draw.arc(grinch, (0, 80, 0), (30, 60, 60, 30), 3.5, 6.0, 4)  # Grin
        pygame.draw.polygon(grinch, (220, 20, 60), [(60, 4), (24, 40), (96, 40)])  # Stolen hat
        pygame.draw.circle(grinch, (255, 255, 255), (60, 6), 10)
        self.sprites['christmas_grinch'] = grinch

    def _create_chanukkah_sprites(self):
        """Create Chanukkah-themed sprites."""
        # Sufganiyah (jelly donut) - 120x140
        donut = pygame.Surface((120, 140), pygame.SRCALPHA)
        # Main donut body (tan/brown)
        pygame.draw.ellipse(donut, (210, 180, 140), (10, 40, 100, 70))
        # Lighter top
        pygame.draw.ellipse(donut, (240, 210, 170), (20, 45, 80, 40))
        # Powdered sugar spots
        for _ in range(15):
            x = random.randint(25, 95)
            y = random.randint(50, 85)
            pygame.draw.circle(donut, (255, 255, 255), (x, y), random.randint(2, 4))
        # Jelly center (red blob on top)
        pygame.draw.ellipse(donut, (200, 50, 50), (45, 55, 30, 20))
        pygame.draw.ellipse(donut, (255, 100, 100), (50, 58, 15, 10))  # Highlight
        self.sprites['chanukkah_bauble'] = donut

        # Star of David - 100x140
        star = pygame.Surface((100, 140), pygame.SRCALPHA)
        cx, cy = 50, 70
        size = 45
        # Draw two overlapping triangles
        # Upward triangle
        points1 = [
            (cx, cy - size),
            (cx - size * 0.866, cy + size * 0.5),
            (cx + size * 0.866, cy + size * 0.5)
        ]
        # Downward triangle
        points2 = [
            (cx, cy + size),
            (cx - size * 0.866, cy - size * 0.5),
            (cx + size * 0.866, cy - size * 0.5)
        ]
        # Gold fill
        pygame.draw.polygon(star, (255, 215, 0), points1)
        pygame.draw.polygon(star, (255, 215, 0), points2)
        # Blue outline
        pygame.draw.polygon(star, (0, 100, 200), points1, 4)
        pygame.draw.polygon(star, (0, 100, 200), points2, 4)
        # Inner glow
        pygame.draw.circle(star, (255, 240, 150), (cx, cy), 15)
        self.sprites['chanukkah_elf'] = star

        # Menorah - 140x180
        menorah = pygame.Surface((140, 180), pygame.SRCALPHA)
        gold = (255, 215, 0)
        dark_gold = (200, 170, 0)
        # Base
        pygame.draw.ellipse(menorah, gold, (30, 150, 80, 25))
        pygame.draw.rect(menorah, gold, (60, 130, 20, 25))
        # Main stem
        pygame.draw.rect(menorah, gold, (65, 60, 10, 75))
        # Arms (4 on each side)
        arm_y = 70
        for i, offset in enumerate([15, 30, 45, 60]):
            # Left arm
            pygame.draw.rect(menorah, gold, (70 - offset - 8, arm_y, 8, 4))
            pygame.draw.rect(menorah, gold, (70 - offset - 8, arm_y, 4, 30 - i * 5))
            # Right arm
            pygame.draw.rect(menorah, gold, (70 + offset, arm_y, 8, 4))
            pygame.draw.rect(menorah, gold, (70 + offset + 4, arm_y, 4, 30 - i * 5))
        # Candles and flames
        flame_color = (255, 165, 0)
        flame_inner = (255, 255, 100)
        candle_tops = [(70, 45)]  # Center (shamash - taller)
        for offset in [15, 30, 45, 60]:
            candle_tops.append((70 - offset - 6, 70 - (60 - offset) // 4))
            candle_tops.append((70 + offset + 6, 70 - (60 - offset) // 4))
        for x, y in candle_tops:
            # Candle
            pygame.draw.rect(menorah, (200, 200, 220), (x - 3, y, 6, 20))
            # Flame
            pygame.draw.ellipse(menorah, flame_color, (x - 5, y - 15, 10, 18))
            pygame.draw.ellipse(menorah, flame_inner, (x - 3, y - 10, 6, 10))
        self.sprites['chanukkah_santa'] = menorah

        # Antiochus (Greek villain in toga) - 120x160
        antiochus = pygame.Surface((120, 160), pygame.SRCALPHA)
        # Toga body (white/cream)
        pygame.draw.ellipse(antiochus, (240, 235, 220), (20, 70, 80, 90))
        # Purple sash (royal)
        pygame.draw.line(antiochus, (128, 0, 128), (35, 75), (85, 130), 12)
        # Head
        pygame.draw.circle(antiochus, (255, 218, 185), (60, 50), 35)
        # Laurel wreath (golden leaves)
        for angle in range(-60, 61, 20):
            rad = math.radians(angle)
            lx = 60 + math.sin(rad) * 30
            ly = 35 + math.cos(rad) * 10
            pygame.draw.ellipse(antiochus, (200, 170, 0), (lx - 5, ly - 8, 10, 16))
        # Mean eyebrows
        pygame.draw.line(antiochus, (100, 80, 60), (35, 38), (52, 46), 4)
        pygame.draw.line(antiochus, (100, 80, 60), (85, 38), (68, 46), 4)
        # Angry eyes
        pygame.draw.circle(antiochus, (50, 50, 50), (48, 48), 8)
        pygame.draw.circle(antiochus, (50, 50, 50), (72, 48), 8)
        pygame.draw.circle(antiochus, (200, 50, 50), (48, 48), 4)  # Red glint
        pygame.draw.circle(antiochus, (200, 50, 50), (72, 48), 4)
        # Frowning mouth
        pygame.draw.arc(antiochus, (100, 50, 50), (42, 55, 36, 25), 0.3, 2.8, 4)
        # Beard
        pygame.draw.ellipse(antiochus, (80, 60, 40), (45, 65, 30, 25))
        self.sprites['chanukkah_grinch'] = antiochus

    def _create_kpop_sprites(self):
        """Create K-Pop Demon Hunters themed sprites."""
        # Ramen bowl - 120x140
        ramen = pygame.Surface((120, 140), pygame.SRCALPHA)
        # Bowl
        pygame.draw.ellipse(ramen, (255, 100, 100), (10, 60, 100, 60))  # Red bowl
        pygame.draw.ellipse(ramen, (255, 150, 150), (15, 65, 90, 50))  # Inner bowl
        # Broth
        pygame.draw.ellipse(ramen, (255, 220, 150), (20, 55, 80, 45))
        # Noodles (wavy lines)
        for i in range(5):
            start_x = 30 + i * 12
            points = [(start_x + math.sin(j * 0.5) * 5, 60 + j * 3) for j in range(10)]
            if len(points) > 1:
                pygame.draw.lines(ramen, (255, 240, 200), False, points, 3)
        # Egg
        pygame.draw.ellipse(ramen, (255, 255, 255), (45, 50, 30, 20))
        pygame.draw.ellipse(ramen, (255, 180, 50), (52, 55, 16, 12))
        # Chopsticks
        pygame.draw.line(ramen, (139, 90, 43), (80, 30), (100, 80), 4)
        pygame.draw.line(ramen, (139, 90, 43), (85, 28), (105, 78), 4)
        # Steam
        for i in range(3):
            x = 40 + i * 20
            pygame.draw.arc(ramen, (200, 200, 200), (x, 25, 15, 25), 0, 3.14, 2)
        self.sprites['kpop_bauble'] = ramen

        # Light Stick (Huntrix style) - 100x140
        lightstick = pygame.Surface((100, 140), pygame.SRCALPHA)
        # Handle
        pygame.draw.rect(lightstick, (40, 40, 40), (40, 70, 20, 70))
        pygame.draw.rect(lightstick, (60, 60, 60), (42, 72, 16, 66))
        # Glowing top (star/diamond shape)
        glow_color = (255, 0, 128)  # Hot pink
        glow_inner = (255, 150, 200)
        # Diamond shape
        diamond_points = [(50, 10), (75, 45), (50, 80), (25, 45)]
        pygame.draw.polygon(lightstick, glow_color, diamond_points)
        pygame.draw.polygon(lightstick, glow_inner, [(50, 20), (65, 45), (50, 70), (35, 45)])
        # Inner glow
        pygame.draw.circle(lightstick, (255, 255, 255), (50, 45), 12)
        # Sparkles
        for angle in range(0, 360, 45):
            rad = math.radians(angle)
            sx = 50 + math.cos(rad) * 30
            sy = 45 + math.sin(rad) * 25
            pygame.draw.circle(lightstick, (255, 255, 255), (int(sx), int(sy)), 3)
        self.sprites['kpop_elf'] = lightstick

        # Derpy the Blue Tiger - 140x180
        derpy = pygame.Surface((140, 180), pygame.SRCALPHA)
        # Body (blue)
        pygame.draw.ellipse(derpy, (100, 150, 255), (25, 80, 90, 90))
        # Tiger stripes on body
        for i in range(3):
            y = 95 + i * 25
            pygame.draw.arc(derpy, (50, 100, 200), (35, y, 70, 20), 0, 3.14, 4)
        # Head (blue)
        pygame.draw.circle(derpy, (100, 150, 255), (70, 55), 45)
        # Ears
        pygame.draw.polygon(derpy, (100, 150, 255), [(35, 25), (25, 0), (50, 20)])
        pygame.draw.polygon(derpy, (100, 150, 255), [(105, 25), (115, 0), (90, 20)])
        pygame.draw.polygon(derpy, (255, 180, 200), [(38, 22), (32, 5), (48, 20)])
        pygame.draw.polygon(derpy, (255, 180, 200), [(102, 22), (108, 5), (92, 20)])
        # Tiger stripes on face
        pygame.draw.arc(derpy, (50, 100, 200), (40, 30, 25, 15), 0, 3.14, 3)
        pygame.draw.arc(derpy, (50, 100, 200), (75, 30, 25, 15), 0, 3.14, 3)
        # Big derpy orange eyes
        pygame.draw.circle(derpy, (255, 165, 0), (55, 50), 18)  # Left eye
        pygame.draw.circle(derpy, (255, 165, 0), (85, 50), 18)  # Right eye
        pygame.draw.circle(derpy, (0, 0, 0), (58, 52), 10)  # Left pupil (off-center for derpy look)
        pygame.draw.circle(derpy, (0, 0, 0), (82, 48), 10)  # Right pupil (different position)
        pygame.draw.circle(derpy, (255, 255, 255), (60, 48), 5)  # Left highlight
        pygame.draw.circle(derpy, (255, 255, 255), (84, 44), 5)  # Right highlight
        # Nose
        pygame.draw.polygon(derpy, (255, 150, 200), [(70, 65), (65, 75), (75, 75)])
        # Derpy smile
        pygame.draw.arc(derpy, (50, 100, 200), (55, 70, 30, 20), 3.3, 6.1, 3)
        # Whiskers
        pygame.draw.line(derpy, (50, 100, 200), (40, 70), (20, 65), 2)
        pygame.draw.line(derpy, (50, 100, 200), (40, 75), (20, 78), 2)
        pygame.draw.line(derpy, (50, 100, 200), (100, 70), (120, 65), 2)
        pygame.draw.line(derpy, (50, 100, 200), (100, 75), (120, 78), 2)
        self.sprites['kpop_santa'] = derpy

        # Saja Boys (with traditional Korean gat hats) - 120x160
        saja = pygame.Surface((120, 160), pygame.SRCALPHA)
        # Body (dark hanbok)
        pygame.draw.ellipse(saja, (30, 30, 50), (25, 75, 70, 85))
        # White collar detail
        pygame.draw.polygon(saja, (200, 200, 200), [(45, 75), (60, 95), (75, 75)])
        # Head
        pygame.draw.circle(saja, (80, 70, 60), (60, 50), 30)
        # Traditional Gat hat (wide-brimmed Korean hat)
        # Brim (very wide, black)
        pygame.draw.ellipse(saja, (20, 20, 20), (5, 20, 110, 30))
        # Top of hat (cylindrical)
        pygame.draw.ellipse(saja, (20, 20, 20), (35, 5, 50, 25))
        pygame.draw.rect(saja, (20, 20, 20), (35, 15, 50, 15))
        # Hat string
        pygame.draw.line(saja, (100, 50, 50), (30, 45), (25, 80), 2)
        pygame.draw.line(saja, (100, 50, 50), (90, 45), (95, 80), 2)
        # Mean eyebrows
        pygame.draw.line(saja, (40, 30, 30), (40, 42), (55, 48), 4)
        pygame.draw.line(saja, (40, 30, 30), (80, 42), (65, 48), 4)
        # Glowing red eyes (demon!)
        pygame.draw.circle(saja, (255, 0, 0), (50, 52), 8)
        pygame.draw.circle(saja, (255, 0, 0), (70, 52), 8)
        pygame.draw.circle(saja, (255, 100, 100), (52, 50), 3)
        pygame.draw.circle(saja, (255, 100, 100), (72, 50), 3)
        # Angry mouth
        pygame.draw.arc(saja, (100, 50, 50), (45, 60, 30, 15), 0.3, 2.8, 3)
        self.sprites['kpop_grinch'] = saja

    def _get_sprite(self, target_type: str):
        """Get the correct sprite for current theme."""
        return self.sprites.get(f"{self.theme}_{target_type}")

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

            # Catch sound (big success)
            catch_duration = 0.2
            catch_samples = int(sample_rate * catch_duration)
            self.sounds['catch'] = pygame.mixer.Sound(
                buffer=bytes([
                    int(128 + 100 * math.sin(2 * math.pi * (600 + t * 2) * t / sample_rate) *
                        (1 - t / catch_samples))
                    for t in range(catch_samples)
                ])
            )

            # Bad sound
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

            # Select sound
            select_duration = 0.1
            select_samples = int(sample_rate * select_duration)
            self.sounds['select'] = pygame.mixer.Sound(
                buffer=bytes([
                    int(128 + 60 * math.sin(2 * math.pi * 500 * t / sample_rate) *
                        (1 - t / select_samples))
                    for t in range(select_samples)
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
        print("Starting DanceMode!")
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
                elif event.type == pygame.VIDEORESIZE:
                    self._handle_resize(event.w, event.h)
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
            if self.state == GameState.MENU:
                return False
            else:
                # Go back to menu
                self.state = GameState.MENU
                return True

        elif key == pygame.K_SPACE or key == pygame.K_RETURN:
            if self.state == GameState.MENU:
                # Select theme and go to title
                theme_keys = ['christmas', 'chanukkah', 'kpop']
                self.theme = theme_keys[self.menu_selection]
                self.state = GameState.TITLE
                self._play_sound('select')
            elif self.state == GameState.TITLE:
                self._start_countdown()
            elif self.state == GameState.RESULTS:
                self.state = GameState.TITLE

        elif key == pygame.K_LEFT or key == pygame.K_UP:
            if self.state == GameState.MENU:
                self.menu_selection = (self.menu_selection - 1) % 3
                self._play_sound('select')

        elif key == pygame.K_RIGHT or key == pygame.K_DOWN:
            if self.state == GameState.MENU:
                self.menu_selection = (self.menu_selection + 1) % 3
                self._play_sound('select')

        elif key == pygame.K_1:
            if self.state == GameState.MENU:
                self.menu_selection = 0
                self.theme = 'christmas'
                self.state = GameState.TITLE
                self._play_sound('select')

        elif key == pygame.K_2:
            if self.state == GameState.MENU:
                self.menu_selection = 1
                self.theme = 'chanukkah'
                self.state = GameState.TITLE
                self._play_sound('select')

        elif key == pygame.K_3:
            if self.state == GameState.MENU:
                self.menu_selection = 2
                self.theme = 'kpop'
                self.state = GameState.TITLE
                self._play_sound('select')

        elif key == pygame.K_f or key == pygame.K_F11:
            self._toggle_fullscreen()

        return True

    def _handle_resize(self, new_width: int, new_height: int):
        """Handle window resize."""
        self.width = new_width
        self.height = new_height
        if not self.fullscreen:
            self.screen = pygame.display.set_mode((self.width, self.height),
                                                   pygame.DOUBLEBUF | pygame.RESIZABLE)
        self._init_snowflakes(100)

    def _toggle_fullscreen(self):
        """Toggle fullscreen mode."""
        self.fullscreen = not self.fullscreen
        if self.fullscreen:
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
            info = pygame.display.Info()
            self.width = info.current_w
            self.height = info.current_h
        else:
            self.width = 1280
            self.height = 720
            self.screen = pygame.display.set_mode((self.width, self.height),
                                                   pygame.DOUBLEBUF | pygame.RESIZABLE)
        self._init_snowflakes(100)

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
        """Update falling snowflakes/sparkles."""
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
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_resized = cv2.resize(frame_rgb, (self.width, self.height))
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
        self.game_timer -= dt
        if self.game_timer <= 0:
            self.game_timer = 0
            self._end_game()
            return

        self._update_spawning(dt)
        self._update_targets(dt)
        self._check_collisions()
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
            angle = random.random() * 2 * math.pi
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
        else:
            vx, vy = 0, 0

        lifetime = self.LIFETIMES[target_type]
        sizes = {'bauble': 100, 'elf': 110, 'santa': 140, 'grinch': 120}

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

            target.x += target.vx * dt
            target.y += target.vy * dt

            if target.x < 50 or target.x > self.width - 50:
                target.vx = -target.vx
                target.x = max(50, min(self.width - 50, target.x))
            if target.y < 50 or target.y > self.height - 50:
                target.vy = -target.vy
                target.y = max(50, min(self.height - 50, target.y))

            target.lifetime -= dt
            if target.lifetime <= 0:
                self.targets.remove(target)

    def _check_collisions(self):
        """Check if hands hit any targets."""
        if not self.cached_players:
            return

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

        self._spawn_pop_particles(target.x, target.y, target.target_type)

        if target.target_type == 'grinch':
            self._play_sound('bad')
        elif target.target_type in ['santa', 'elf']:
            self._play_sound('catch')
        else:
            self._play_sound('pop')

    def _spawn_pop_particles(self, x: float, y: float, target_type: str):
        """Spawn celebration particles."""
        theme_config = self.THEMES[self.theme]
        colors = theme_config['particle_colors'].get(target_type, [(255, 255, 255)])

        for _ in range(20):
            angle = random.random() * 2 * math.pi
            speed = random.random() * 300 + 100
            color = random.choice(colors)

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
            p['vy'] += 400 * dt
            p['lifetime'] -= dt
            if p['lifetime'] <= 0:
                self.particles.remove(p)

    def _end_game(self):
        """End the game and show results."""
        self.state = GameState.RESULTS
        if self.score > self.high_scores[self.theme]:
            self.high_scores[self.theme] = self.score

    def _render(self):
        """Render the game."""
        # Draw camera feed as background
        if self.camera_surface:
            self.screen.blit(self.camera_surface, (0, 0))
        else:
            self.screen.fill((20, 20, 40))

        # Darken camera slightly
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 30, 80))
        self.screen.blit(overlay, (0, 0))

        # Draw snowflakes/sparkles
        self._draw_snowflakes()

        # State-specific rendering
        if self.state == GameState.MENU:
            self._render_menu()
        elif self.state == GameState.TITLE:
            self._render_title()
        elif self.state == GameState.COUNTDOWN:
            self._render_countdown()
        elif self.state == GameState.PLAYING:
            self._render_playing()
        elif self.state == GameState.RESULTS:
            self._render_results()

    def _draw_snowflakes(self):
        """Draw falling snowflakes (Christmas), dreidels (Chanukkah), or disco balls (K-Pop)."""
        if self.theme == 'chanukkah':
            # Draw spinning dreidels
            for snow in self.snowflakes:
                x, y = int(snow['x']), int(snow['y'])
                size = snow['size'] * 2
                # Rotate based on position for spinning effect
                angle = (pygame.time.get_ticks() / 500 + snow['x']) % (2 * math.pi)

                # Draw dreidel body (rotated square)
                points = []
                for i in range(4):
                    a = angle + i * math.pi / 2
                    px = x + math.cos(a) * size
                    py = y + math.sin(a) * size
                    points.append((px, py))
                pygame.draw.polygon(self.screen, (0, 100, 200), points)
                pygame.draw.polygon(self.screen, (255, 215, 0), points, 1)

                # Draw handle on top
                handle_angle = angle - math.pi / 2
                hx = x + math.cos(handle_angle) * size * 1.3
                hy = y + math.sin(handle_angle) * size * 1.3
                pygame.draw.line(self.screen, (0, 100, 200), (x, y), (int(hx), int(hy)), 2)
        elif self.theme == 'kpop':
            # Draw golden disco balls
            for snow in self.snowflakes:
                x, y = int(snow['x']), int(snow['y'])
                size = snow['size'] + 2
                # Disco ball - golden with sparkle effect
                time_offset = pygame.time.get_ticks() / 200 + snow['x']
                brightness = int(200 + 55 * math.sin(time_offset))
                color = (brightness, int(brightness * 0.85), 0)  # Golden
                pygame.draw.circle(self.screen, color, (x, y), size)
                # Sparkle highlight
                highlight_angle = time_offset % (2 * math.pi)
                hx = x + math.cos(highlight_angle) * size * 0.4
                hy = y + math.sin(highlight_angle) * size * 0.4
                pygame.draw.circle(self.screen, (255, 255, 200), (int(hx), int(hy)), max(1, size // 3))
                # Mirror tile effect
                if size > 3:
                    pygame.draw.circle(self.screen, (255, 255, 255), (x - size // 3, y - size // 3), 1)
        else:
            # Draw snowflakes for Christmas
            for snow in self.snowflakes:
                pygame.draw.circle(self.screen, (255, 255, 255),
                                 (int(snow['x']), int(snow['y'])), snow['size'])

    def _render_menu(self):
        """Render theme selection menu."""
        # Title
        title = self.font_huge.render("Dance Mode", True, (255, 255, 255))
        self.screen.blit(title, title.get_rect(center=(self.width // 2, self.height // 5)))

        subtitle = self.font_medium.render("Choose Your Theme", True, (200, 200, 200))
        self.screen.blit(subtitle, subtitle.get_rect(center=(self.width // 2, self.height // 5 + 70)))

        # Theme options - 3 boxes
        box_width = 240
        box_height = 180
        gap = 40
        total_width = 3 * box_width + 2 * gap
        start_x = (self.width - total_width) // 2
        box_y = self.height // 2 - 20

        themes = [
            ('Christmas', (255, 50, 50), 'christmas', '1'),
            ('Chanukkah', (0, 100, 200), 'chanukkah', '2'),
            ('K-Pop', (255, 0, 128), 'kpop', '3'),
        ]

        for i, (name, color1, theme_key, key) in enumerate(themes):
            box_x = start_x + i * (box_width + gap)
            selected = (i == self.menu_selection)

            # Draw box
            box_color = color1 if selected else (80, 80, 80)
            border_width = 6 if selected else 2
            pygame.draw.rect(self.screen, box_color,
                           (box_x, box_y, box_width, box_height), border_width, border_radius=15)

            # Draw theme preview sprite
            sprite_key = f"{theme_key}_bauble"
            sprite = self.sprites.get(sprite_key)
            if sprite:
                # Scale down sprite a bit to fit
                scaled = pygame.transform.scale(sprite, (80, 93))
                sprite_rect = scaled.get_rect(center=(box_x + box_width // 2, box_y + 60))
                self.screen.blit(scaled, sprite_rect)

            # Theme name
            name_color = (255, 255, 255) if selected else (150, 150, 150)
            # Use smaller font for K-Pop Demon Hunters
            display_name = "Demon Hunters" if name == "K-Pop" else name
            name_text = self.font_medium.render(display_name, True, name_color)
            self.screen.blit(name_text, name_text.get_rect(center=(box_x + box_width // 2, box_y + 130)))

            # Key hint
            key_text = self.font_small.render(f"Press {key}", True, (150, 150, 150))
            self.screen.blit(key_text, key_text.get_rect(center=(box_x + box_width // 2, box_y + 160)))

        # Instructions
        pulse = abs(math.sin(pygame.time.get_ticks() / 500)) * 0.3 + 0.7
        inst_color = (int(255 * pulse), int(255 * pulse), int(100 * pulse))
        instructions = self.font_medium.render("Use Arrow Keys to Select, SPACE to Start", True, inst_color)
        self.screen.blit(instructions, instructions.get_rect(center=(self.width // 2, self.height - 80)))

    def _render_title(self):
        """Render title screen."""
        theme_config = self.THEMES[self.theme]
        colors = theme_config['colors']

        # Title
        title = self.font_huge.render("Dance Mode", True, (255, 255, 255))
        self.screen.blit(title, title.get_rect(center=(self.width // 2, self.height // 4 - 20)))

        # Theme subtitle
        theme_name = theme_config['name']
        subtitle = self.font_large.render(f"~ {theme_name} Edition ~", True, colors['primary'])
        self.screen.blit(subtitle, subtitle.get_rect(center=(self.width // 2, self.height // 4 + 60)))

        # Instructions based on theme
        bauble_name = theme_config['bauble_name']
        elf_name = theme_config['elf_name']
        santa_name = theme_config['santa_name']
        grinch_name = theme_config['grinch_name']

        instructions = [
            f"Pop {bauble_name}s with your hands! (+5)",
            f"Catch {elf_name}s (+50) and {santa_name}s (+100)!",
            f"Avoid {grinch_name}! (-10)",
            "60 seconds - get the highest score!",
        ]

        y = self.height // 2 + 30
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
        high_score = self.high_scores[self.theme]
        if high_score > 0:
            hs = self.font_medium.render(f"High Score: {high_score}", True, colors['accent'])
            self.screen.blit(hs, hs.get_rect(center=(self.width // 2, self.height - 40)))

        # Back hint
        back = self.font_small.render("ESC to change theme", True, (150, 150, 150))
        self.screen.blit(back, (20, self.height - 40))

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

        ready = self.font_medium.render("Get Ready!", True, (255, 255, 255))
        self.screen.blit(ready, ready.get_rect(center=(self.width // 2, self.height // 3)))

    def _render_playing(self):
        """Render gameplay."""
        self._draw_skeleton_overlay()

        for target in self.targets:
            self._draw_target(target)

        for p in self.particles:
            pygame.draw.circle(self.screen, p['color'],
                             (int(p['x']), int(p['y'])), p['size'])

        self._draw_game_ui()

    def _draw_skeleton_overlay(self):
        """Draw skeleton/body tracking overlay."""
        if not self.cached_players:
            return

        player_colors = [
            (255, 100, 150),
            (100, 200, 255),
            (150, 255, 100),
            (255, 200, 100),
        ]

        for i, player in enumerate(self.cached_players[:4]):
            color = player_colors[i % len(player_colors)]

            joints = {
                'nose': player.nose,
                'left_shoulder': player.left_shoulder,
                'right_shoulder': player.right_shoulder,
                'left_elbow': player.left_elbow,
                'right_elbow': player.right_elbow,
                'left_hand': player.left_hand,
                'right_hand': player.right_hand,
                'left_hip': player.left_hip,
                'right_hip': player.right_hip,
            }

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
                start = joints.get(start_name)
                end = joints.get(end_name)
                if start and end:
                    pygame.draw.line(self.screen, color,
                                   (int(start[0]), int(start[1])),
                                   (int(end[0]), int(end[1])), 4)

            for joint_name, pos in joints.items():
                if pos:
                    if 'hand' in joint_name:
                        pygame.draw.circle(self.screen, (255, 255, 255),
                                         (int(pos[0]), int(pos[1])), 25, 3)
                        pygame.draw.circle(self.screen, color,
                                         (int(pos[0]), int(pos[1])), 20)
                        pygame.draw.circle(self.screen, (255, 255, 255),
                                         (int(pos[0]), int(pos[1])), 8)
                    else:
                        pygame.draw.circle(self.screen, color,
                                         (int(pos[0]), int(pos[1])), 8)
                        pygame.draw.circle(self.screen, (255, 255, 255),
                                         (int(pos[0]), int(pos[1])), 8, 2)

    def _draw_target(self, target: Target):
        """Draw a single target."""
        if target.popped:
            scale = 1.0 + target.pop_timer * 3
            alpha = int(255 * (1 - target.pop_timer / 0.3))
            size = int(target.size * scale)
            surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            color = (255, 255, 100, alpha) if target.target_type != 'grinch' else (100, 100, 100, alpha)
            pygame.draw.circle(surf, color, (size, size), size)
            self.screen.blit(surf, (int(target.x - size), int(target.y - size)))
            return

        sprite = self._get_sprite(target.target_type)
        if sprite:
            pulse = 1.0 + math.sin(pygame.time.get_ticks() / 200) * 0.1
            scaled = pygame.transform.scale(sprite,
                (int(sprite.get_width() * pulse), int(sprite.get_height() * pulse)))
            rect = scaled.get_rect(center=(int(target.x), int(target.y)))
            self.screen.blit(scaled, rect)

        if target.target_type in ['elf', 'santa', 'grinch']:
            progress = target.lifetime / self.LIFETIMES[target.target_type]
            bar_width = 40
            bar_height = 6
            bar_x = int(target.x - bar_width // 2)
            bar_y = int(target.y + target.size // 2 + 10)

            pygame.draw.rect(self.screen, (50, 50, 50),
                           (bar_x, bar_y, bar_width, bar_height))
            color = (50, 255, 50) if progress > 0.3 else (255, 100, 50)
            pygame.draw.rect(self.screen, color,
                           (bar_x, bar_y, int(bar_width * progress), bar_height))

    def _draw_game_ui(self):
        """Draw game UI elements."""
        theme_config = self.THEMES[self.theme]
        colors = theme_config['colors']

        # Timer bar
        timer_progress = self.game_timer / 60.0
        bar_width = self.width - 200
        bar_height = 20
        bar_x = 100
        bar_y = 20

        pygame.draw.rect(self.screen, (50, 50, 50),
                        (bar_x, bar_y, bar_width, bar_height), border_radius=10)
        bar_color = (50, 255, 50) if timer_progress > 0.3 else (255, 50, 50)
        pygame.draw.rect(self.screen, bar_color,
                        (bar_x, bar_y, int(bar_width * timer_progress), bar_height),
                        border_radius=10)

        seconds = int(self.game_timer)
        timer_text = self.font_medium.render(f"{seconds}s", True, (255, 255, 255))
        self.screen.blit(timer_text, (bar_x - 60, bar_y - 5))

        # Score
        score_text = self.font_large.render(f"Score: {self.score}", True, colors['accent'])
        self.screen.blit(score_text, (20, 60))

        # High score
        hs_text = self.font_small.render(f"Best: {self.high_scores[self.theme]}", True, (200, 200, 200))
        self.screen.blit(hs_text, (self.width - 150, 20))

        # Legend
        legend_y = self.height - 35
        bauble_name = theme_config['bauble_name']
        elf_name = theme_config['elf_name']
        santa_name = theme_config['santa_name']
        grinch_name = theme_config['grinch_name']

        legend_items = [
            (f"{bauble_name} +5", colors['accent']),
            (f"{elf_name} +50", colors['primary']),
            (f"{santa_name} +100", colors['secondary']),
            (f"{grinch_name} -10", (128, 128, 128)),
        ]
        x = 20
        for text, color in legend_items:
            rendered = self.font_small.render(text, True, color)
            self.screen.blit(rendered, (x, legend_y))
            x += 200

    def _render_results(self):
        """Render results screen."""
        theme_config = self.THEMES[self.theme]
        colors = theme_config['colors']

        # Dark overlay
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        # Title
        high_score = self.high_scores[self.theme]
        if self.score >= high_score and self.score > 0:
            title = self.font_huge.render("NEW HIGH SCORE!", True, colors['accent'])
        else:
            title = self.font_huge.render("Time's Up!", True, colors['primary'])
        self.screen.blit(title, title.get_rect(center=(self.width // 2, 80)))

        # Score breakdown
        y = 180
        bauble_name = theme_config['bauble_name']
        elf_name = theme_config['elf_name']
        santa_name = theme_config['santa_name']
        grinch_name = theme_config['grinch_name']

        breakdown = [
            (f"{bauble_name}s: {self.stats['bauble']}", f"x 5 = {self.stats['bauble'] * 5}", colors['accent']),
            (f"{elf_name}s: {self.stats['elf']}", f"x 50 = {self.stats['elf'] * 50}", colors['primary']),
            (f"{santa_name}s: {self.stats['santa']}", f"x 100 = {self.stats['santa'] * 100}", colors['secondary']),
            (f"{grinch_name}: {self.stats['grinch']}", f"x -10 = {self.stats['grinch'] * -10}", (128, 128, 128)),
        ]

        for label, points, color in breakdown:
            label_text = self.font_medium.render(label, True, color)
            points_text = self.font_medium.render(points, True, (255, 255, 255))
            self.screen.blit(label_text, (self.width // 2 - 200, y))
            self.screen.blit(points_text, (self.width // 2 + 50, y))
            y += 60

        pygame.draw.line(self.screen, (255, 255, 255),
                        (self.width // 2 - 200, y), (self.width // 2 + 200, y), 2)
        y += 20

        total_text = self.font_large.render(f"TOTAL: {self.score}", True, (255, 255, 100))
        self.screen.blit(total_text, total_text.get_rect(center=(self.width // 2, y + 30)))

        y += 100
        hs_text = self.font_medium.render(f"High Score: {high_score}", True, (200, 200, 200))
        self.screen.blit(hs_text, hs_text.get_rect(center=(self.width // 2, y)))

        y += 80
        pulse = abs(math.sin(pygame.time.get_ticks() / 500)) * 0.3 + 0.7
        color = (int(255 * pulse), int(255 * pulse), int(100 * pulse))
        again = self.font_medium.render("Press SPACE to Play Again!", True, color)
        self.screen.blit(again, again.get_rect(center=(self.width // 2, y)))

        # Back hint
        back = self.font_small.render("ESC to change theme", True, (150, 150, 150))
        self.screen.blit(back, (20, self.height - 40))

    def _cleanup(self):
        """Clean up resources."""
        self.player_detector.stop()
        pygame.quit()


def main():
    """Entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="DanceMode!")
    parser.add_argument('--width', type=int, default=1280, help='Screen width')
    parser.add_argument('--height', type=int, default=720, help='Screen height')
    parser.add_argument('--fullscreen', action='store_true', help='Fullscreen mode')

    args = parser.parse_args()

    game = DanceModeGame(
        width=args.width,
        height=args.height,
        fullscreen=args.fullscreen
    )
    game.start()


if __name__ == '__main__':
    main()
