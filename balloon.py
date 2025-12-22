"""
Balloon Physics Engine
Handles balloon movement, gravity, wind, and collision detection.
"""

import math
import random
from dataclasses import dataclass, field
from typing import Tuple, List, Optional


@dataclass
class Wind:
    """Represents wind force affecting the balloon."""
    direction: float = 0.0  # Angle in radians (0 = right, PI/2 = down)
    strength: float = 0.0   # Force magnitude
    duration: float = 0.0   # Remaining duration in seconds
    max_duration: float = 0.0


class BalloonPhysics:
    """
    Handles all physics for the balloon including gravity, wind,
    air resistance, and collision responses.
    """

    def __init__(self, screen_width: int, screen_height: int):
        """
        Initialize balloon physics.

        Args:
            screen_width: Game screen width
            screen_height: Game screen height
        """
        self.screen_width = screen_width
        self.screen_height = screen_height

        # Balloon properties
        self.radius = 50
        self.x = screen_width / 2
        self.y = screen_height / 3  # Start in upper third
        self.vx = 0.0  # Velocity x
        self.vy = 0.0  # Velocity y

        # Physics constants (tuned for fun, floaty gameplay)
        self.gravity = 80.0  # Pixels per second^2 (slow fall)
        self.air_resistance = 0.98  # Velocity multiplier per frame
        self.bounce_damping = 0.7  # Energy retained on wall bounce
        self.max_velocity = 400.0  # Max speed in any direction

        # Hit response
        self.hit_force = 350.0  # Force applied when hit by player
        self.hit_upward_bias = 1.3  # Multiplier for upward force

        # Wind system
        self.current_wind: Optional[Wind] = None
        self.wind_spawn_timer = 0.0
        self.wind_spawn_interval_min = 3.0  # Min seconds between gusts
        self.wind_spawn_interval_max = 8.0  # Max seconds between gusts
        self.next_wind_time = random.uniform(
            self.wind_spawn_interval_min, self.wind_spawn_interval_max)

        # State
        self.is_popped = False
        self.wobble_angle = 0.0  # For visual wobble effect
        self.wobble_speed = 3.0

        # Ground level (where balloon pops)
        self.ground_y = screen_height - 60  # Leave room for ground graphic

    def reset(self):
        """Reset balloon to starting position."""
        self.x = self.screen_width / 2
        self.y = self.screen_height / 3
        self.vx = random.uniform(-50, 50)  # Slight random start
        self.vy = 0.0
        self.is_popped = False
        self.current_wind = None
        self.next_wind_time = random.uniform(
            self.wind_spawn_interval_min, self.wind_spawn_interval_max)

    def update(self, dt: float):
        """
        Update balloon physics.

        Args:
            dt: Delta time in seconds
        """
        if self.is_popped:
            return

        # Apply gravity
        self.vy += self.gravity * dt

        # Update wind
        self._update_wind(dt)

        # Apply wind force
        if self.current_wind and self.current_wind.duration > 0:
            wind_fx = math.cos(self.current_wind.direction) * self.current_wind.strength
            wind_fy = math.sin(self.current_wind.direction) * self.current_wind.strength
            self.vx += wind_fx * dt
            self.vy += wind_fy * dt

        # Apply air resistance
        self.vx *= self.air_resistance
        self.vy *= self.air_resistance

        # Clamp velocity
        self.vx = max(-self.max_velocity, min(self.max_velocity, self.vx))
        self.vy = max(-self.max_velocity, min(self.max_velocity, self.vy))

        # Update position
        self.x += self.vx * dt
        self.y += self.vy * dt

        # Wall collisions
        self._handle_wall_collisions()

        # Check for ground collision (pop!)
        if self.y + self.radius >= self.ground_y:
            self.is_popped = True
            self.y = self.ground_y - self.radius

        # Update wobble for visual effect
        self.wobble_angle += self.wobble_speed * dt
        if self.wobble_angle > math.pi * 2:
            self.wobble_angle -= math.pi * 2

    def _update_wind(self, dt: float):
        """Handle wind gust spawning and updating."""
        # Decrease current wind duration
        if self.current_wind:
            self.current_wind.duration -= dt
            if self.current_wind.duration <= 0:
                self.current_wind = None

        # Check if we should spawn new wind
        self.wind_spawn_timer += dt
        if self.wind_spawn_timer >= self.next_wind_time:
            self._spawn_wind_gust()
            self.wind_spawn_timer = 0
            self.next_wind_time = random.uniform(
                self.wind_spawn_interval_min, self.wind_spawn_interval_max)

    def _spawn_wind_gust(self):
        """Create a new wind gust."""
        # Random direction (mostly horizontal with slight vertical)
        base_angle = random.choice([0, math.pi])  # Left or right
        angle_variation = random.uniform(-0.3, 0.3)  # Slight up/down
        direction = base_angle + angle_variation

        # Random strength
        strength = random.uniform(100, 300)

        # Random duration
        duration = random.uniform(1.0, 3.0)

        self.current_wind = Wind(
            direction=direction,
            strength=strength,
            duration=duration,
            max_duration=duration
        )

    def _handle_wall_collisions(self):
        """Handle collisions with screen edges."""
        # Left wall
        if self.x - self.radius < 0:
            self.x = self.radius
            self.vx = abs(self.vx) * self.bounce_damping

        # Right wall
        if self.x + self.radius > self.screen_width:
            self.x = self.screen_width - self.radius
            self.vx = -abs(self.vx) * self.bounce_damping

        # Ceiling
        if self.y - self.radius < 0:
            self.y = self.radius
            self.vy = abs(self.vy) * self.bounce_damping

    def check_collision(self, point: Tuple[float, float],
                       collision_radius: float = 30) -> bool:
        """
        Check if a point collides with the balloon.

        Args:
            point: (x, y) position to check
            collision_radius: Radius around the point for collision

        Returns:
            True if collision detected
        """
        if self.is_popped:
            return False

        dx = point[0] - self.x
        dy = point[1] - self.y
        distance = math.sqrt(dx * dx + dy * dy)

        return distance < (self.radius + collision_radius)

    def apply_hit(self, hit_point: Tuple[float, float],
                  player_velocity: Tuple[float, float] = (0, 0)):
        """
        Apply force to balloon from a hit.

        Args:
            hit_point: Where the hit originated from
            player_velocity: Velocity of the hitting object (for extra force)
        """
        if self.is_popped:
            return

        # Calculate direction from hit point to balloon center
        dx = self.x - hit_point[0]
        dy = self.y - hit_point[1]
        distance = math.sqrt(dx * dx + dy * dy)

        if distance < 0.1:
            # Avoid division by zero, push up
            dx, dy = 0, -1
            distance = 1

        # Normalize direction
        dx /= distance
        dy /= distance

        # Apply upward bias (we want balloon to go UP mostly)
        dy = min(dy, -0.3)  # Ensure some upward component
        dy *= self.hit_upward_bias

        # Re-normalize after bias
        length = math.sqrt(dx * dx + dy * dy)
        dx /= length
        dy /= length

        # Calculate force based on proximity (closer = stronger)
        proximity_factor = 1.0 - min(distance / (self.radius * 2), 1.0)
        force = self.hit_force * (0.5 + 0.5 * proximity_factor)

        # Add player velocity influence
        self.vx += dx * force + player_velocity[0] * 0.3
        self.vy += dy * force + player_velocity[1] * 0.3

    def get_position(self) -> Tuple[float, float]:
        """Get current balloon center position."""
        return (self.x, self.y)

    def get_render_info(self) -> dict:
        """Get information needed for rendering the balloon."""
        return {
            'x': self.x,
            'y': self.y,
            'radius': self.radius,
            'wobble': math.sin(self.wobble_angle) * 3,  # Slight wobble
            'is_popped': self.is_popped,
            'wind_active': self.current_wind is not None and self.current_wind.duration > 0,
            'wind_direction': self.current_wind.direction if self.current_wind else 0,
            'wind_strength': self.current_wind.strength if self.current_wind else 0,
        }

    def get_wind_indicator(self) -> Optional[Tuple[float, float, float]]:
        """
        Get wind indicator info for UI.

        Returns:
            (direction, strength, remaining_ratio) or None if no wind
        """
        if self.current_wind and self.current_wind.duration > 0:
            remaining_ratio = self.current_wind.duration / self.current_wind.max_duration
            return (
                self.current_wind.direction,
                self.current_wind.strength,
                remaining_ratio
            )
        return None
