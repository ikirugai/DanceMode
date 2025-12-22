"""
Dance Target System
Manages dance moves, target positions, and timing for the dance game.
"""

import math
import random
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict
from enum import Enum


class Hand(Enum):
    LEFT = "left"
    RIGHT = "right"
    BOTH = "both"


@dataclass
class DanceMove:
    """A single dance move with target positions."""
    name: str
    # Target positions as percentages of screen (0.0 to 1.0)
    # None means hand can be anywhere (not tracked for this move)
    left_hand_target: Optional[Tuple[float, float]] = None
    right_hand_target: Optional[Tuple[float, float]] = None
    duration: float = 2.0  # Seconds to complete this move
    description: str = ""


@dataclass
class DanceSequence:
    """A choreographed sequence of dance moves."""
    name: str
    moves: List[DanceMove]
    tempo_bpm: int = 120  # Beats per minute
    difficulty: int = 1  # 1-3 difficulty rating


class DanceLibrary:
    """Library of kid-friendly dance sequences."""

    @staticmethod
    def get_ymca() -> DanceSequence:
        """YMCA - Arms make letter shapes."""
        moves = [
            DanceMove("Y", left_hand_target=(0.3, 0.15), right_hand_target=(0.7, 0.15),
                     description="Arms up in a Y shape!"),
            DanceMove("M", left_hand_target=(0.25, 0.4), right_hand_target=(0.75, 0.4),
                     description="Hands on shoulders!"),
            DanceMove("C", left_hand_target=(0.2, 0.3), right_hand_target=(0.5, 0.5),
                     description="Curve to the left!"),
            DanceMove("A", left_hand_target=(0.35, 0.2), right_hand_target=(0.65, 0.2),
                     description="Hands together above head!"),
        ]
        return DanceSequence("YMCA", moves, tempo_bpm=110, difficulty=1)

    @staticmethod
    def get_macarena() -> DanceSequence:
        """Macarena - Classic hand movements."""
        moves = [
            DanceMove("Arms Out Right", left_hand_target=(0.3, 0.5), right_hand_target=(0.8, 0.5),
                     description="Right arm straight out!"),
            DanceMove("Arms Out Left", left_hand_target=(0.2, 0.5), right_hand_target=(0.7, 0.5),
                     description="Left arm straight out!"),
            DanceMove("Flip Right", left_hand_target=(0.3, 0.45), right_hand_target=(0.8, 0.45),
                     description="Flip right hand up!"),
            DanceMove("Flip Left", left_hand_target=(0.2, 0.45), right_hand_target=(0.7, 0.45),
                     description="Flip left hand up!"),
            DanceMove("Right to Left Shoulder", left_hand_target=(0.4, 0.35), right_hand_target=(0.35, 0.35),
                     description="Right hand to left shoulder!"),
            DanceMove("Left to Right Shoulder", left_hand_target=(0.65, 0.35), right_hand_target=(0.6, 0.35),
                     description="Left hand to right shoulder!"),
            DanceMove("Right to Head", left_hand_target=(0.4, 0.35), right_hand_target=(0.55, 0.2),
                     description="Right hand behind head!"),
            DanceMove("Left to Head", left_hand_target=(0.45, 0.2), right_hand_target=(0.6, 0.35),
                     description="Left hand behind head!"),
        ]
        return DanceSequence("Macarena", moves, tempo_bpm=100, difficulty=2)

    @staticmethod
    def get_baby_shark() -> DanceSequence:
        """Baby Shark - Chomping hand movements."""
        moves = [
            DanceMove("Baby Chomp", left_hand_target=(0.4, 0.5), right_hand_target=(0.6, 0.5),
                     description="Small chomps with fingers!"),
            DanceMove("Mommy Chomp", left_hand_target=(0.35, 0.45), right_hand_target=(0.65, 0.45),
                     description="Bigger chomps!"),
            DanceMove("Daddy Chomp", left_hand_target=(0.3, 0.4), right_hand_target=(0.7, 0.4),
                     description="Big daddy chomps!"),
            DanceMove("Grandma Chomp", left_hand_target=(0.35, 0.5), right_hand_target=(0.65, 0.5),
                     description="Gentle grandma chomps!"),
            DanceMove("Swim Away", left_hand_target=(0.2, 0.5), right_hand_target=(0.8, 0.5),
                     description="Swim swim swim!"),
        ]
        return DanceSequence("Baby Shark", moves, tempo_bpm=115, difficulty=1)

    @staticmethod
    def get_hokey_pokey() -> DanceSequence:
        """Hokey Pokey - In and out movements."""
        moves = [
            DanceMove("Right In", left_hand_target=None, right_hand_target=(0.6, 0.5),
                     description="Right hand in!"),
            DanceMove("Right Out", left_hand_target=None, right_hand_target=(0.85, 0.5),
                     description="Right hand out!"),
            DanceMove("Right Shake", left_hand_target=None, right_hand_target=(0.7, 0.4),
                     description="Shake it all about!"),
            DanceMove("Left In", left_hand_target=(0.4, 0.5), right_hand_target=None,
                     description="Left hand in!"),
            DanceMove("Left Out", left_hand_target=(0.15, 0.5), right_hand_target=None,
                     description="Left hand out!"),
            DanceMove("Left Shake", left_hand_target=(0.3, 0.4), right_hand_target=None,
                     description="Shake it all about!"),
            DanceMove("Both Hands Up", left_hand_target=(0.3, 0.2), right_hand_target=(0.7, 0.2),
                     description="Hands up high!"),
        ]
        return DanceSequence("Hokey Pokey", moves, tempo_bpm=120, difficulty=1)

    @staticmethod
    def get_freeze_dance() -> DanceSequence:
        """Freeze Dance - Random poses to hold."""
        moves = [
            DanceMove("T-Pose", left_hand_target=(0.15, 0.5), right_hand_target=(0.85, 0.5),
                     description="Arms straight out!"),
            DanceMove("Hands Up", left_hand_target=(0.3, 0.15), right_hand_target=(0.7, 0.15),
                     description="Reach for the sky!"),
            DanceMove("Airplane", left_hand_target=(0.1, 0.45), right_hand_target=(0.9, 0.55),
                     description="Tilt like an airplane!"),
            DanceMove("Robot", left_hand_target=(0.35, 0.4), right_hand_target=(0.65, 0.55),
                     description="Robot arms!"),
            DanceMove("Star", left_hand_target=(0.2, 0.25), right_hand_target=(0.8, 0.25),
                     description="Make a star shape!"),
            DanceMove("Low Five", left_hand_target=(0.3, 0.7), right_hand_target=(0.7, 0.7),
                     description="Hands down low!"),
        ]
        return DanceSequence("Freeze Dance", moves, tempo_bpm=130, difficulty=2)

    @staticmethod
    def get_all_sequences() -> List[DanceSequence]:
        """Get all available dance sequences."""
        return [
            DanceLibrary.get_ymca(),
            DanceLibrary.get_baby_shark(),
            DanceLibrary.get_hokey_pokey(),
            DanceLibrary.get_macarena(),
            DanceLibrary.get_freeze_dance(),
        ]


class DanceTargetManager:
    """Manages the current dance sequence and target matching."""

    def __init__(self, screen_width: int, screen_height: int):
        self.screen_width = screen_width
        self.screen_height = screen_height

        # Current dance state
        self.current_sequence: Optional[DanceSequence] = None
        self.current_move_index: int = 0
        self.move_timer: float = 0.0
        self.move_timeout: float = 5.0  # Seconds to hit the target (kid-friendly)

        # Target hit detection
        self.hit_radius: float = 80  # Pixels - reasonable radius for hitting targets
        self.left_hand_hit: bool = False
        self.right_hand_hit: bool = False
        self.left_hit_time: float = 0.0  # When left was hit
        self.right_hit_time: float = 0.0  # When right was hit

        # Timing
        self.min_display_time: float = 3.0  # Minimum time to show targets
        self.celebration_time: float = 1.0  # Time to celebrate after both hit
        self.celebrating: bool = False
        self.celebration_timer: float = 0.0

        # Visual feedback
        self.target_pulse: float = 0.0
        self.success_flash: float = 0.0
        self.miss_flash: float = 0.0

        # Scoring
        self.moves_completed: int = 0
        self.moves_missed: int = 0
        self.current_streak: int = 0
        self.best_streak: int = 0

        # Sequence looping
        self.loop_count: int = 0
        self.max_loops: int = 2  # How many times to repeat the dance

    def start_sequence(self, sequence: DanceSequence):
        """Start a new dance sequence."""
        self.current_sequence = sequence
        self.current_move_index = 0
        self.move_timer = 0.0
        self.left_hand_hit = False
        self.right_hand_hit = False
        self.moves_completed = 0
        self.moves_missed = 0
        self.current_streak = 0
        self.loop_count = 0

    def start_random_sequence(self):
        """Start a random dance sequence."""
        sequences = DanceLibrary.get_all_sequences()
        self.start_sequence(random.choice(sequences))

    def get_current_move(self) -> Optional[DanceMove]:
        """Get the current dance move."""
        if self.current_sequence and self.current_move_index < len(self.current_sequence.moves):
            return self.current_sequence.moves[self.current_move_index]
        return None

    def get_target_positions(self) -> Tuple[Optional[Tuple[int, int]], Optional[Tuple[int, int]]]:
        """Get current target positions in screen coordinates."""
        move = self.get_current_move()
        if not move:
            return None, None

        left_target = None
        right_target = None

        if move.left_hand_target:
            left_target = (
                int(move.left_hand_target[0] * self.screen_width),
                int(move.left_hand_target[1] * self.screen_height)
            )

        if move.right_hand_target:
            right_target = (
                int(move.right_hand_target[0] * self.screen_width),
                int(move.right_hand_target[1] * self.screen_height)
            )

        return left_target, right_target

    def check_hand_hit(self, hand_pos: Tuple[float, float], target_pos: Tuple[int, int]) -> bool:
        """Check if a hand position is close enough to the target."""
        if not hand_pos or not target_pos:
            return False

        dx = hand_pos[0] - target_pos[0]
        dy = hand_pos[1] - target_pos[1]
        distance = math.sqrt(dx * dx + dy * dy)

        return distance <= self.hit_radius

    def update(self, dt: float, left_hand: Optional[Tuple[float, float]],
               right_hand: Optional[Tuple[float, float]]) -> Dict:
        """
        Update the dance target system.

        Returns dict with events: {'hit': bool, 'miss': bool, 'complete': bool, 'pop': bool}
        """
        events = {'hit': False, 'miss': False, 'complete': False, 'sequence_complete': False, 'pop': False}

        if not self.current_sequence:
            return events

        # Update visual effects
        self.target_pulse += dt * 3
        if self.success_flash > 0:
            self.success_flash -= dt * 2
        if self.miss_flash > 0:
            self.miss_flash -= dt * 2

        # Update move timer
        self.move_timer += dt

        # If celebrating, wait for celebration to finish
        if self.celebrating:
            self.celebration_timer += dt
            if self.celebration_timer >= self.celebration_time:
                # Celebration done, advance to next move
                self._next_move()
                events['complete'] = True
            return events

        # Get current targets
        left_target, right_target = self.get_target_positions()

        # Check for hits
        if left_target and not self.left_hand_hit:
            if self.check_hand_hit(left_hand, left_target):
                self.left_hand_hit = True
                self.left_hit_time = self.move_timer
                events['pop'] = True  # Trigger pop effect

        if right_target and not self.right_hand_hit:
            if self.check_hand_hit(right_hand, right_target):
                self.right_hand_hit = True
                self.right_hit_time = self.move_timer
                events['pop'] = True  # Trigger pop effect

        # Check if move is complete (all required targets hit)
        left_done = (left_target is None) or self.left_hand_hit
        right_done = (right_target is None) or self.right_hand_hit

        # Need minimum display time before advancing
        can_advance = self.move_timer >= self.min_display_time

        if left_done and right_done and can_advance:
            # Move completed successfully! Start celebration
            events['hit'] = True
            self.moves_completed += 1
            self.current_streak += 1
            self.best_streak = max(self.best_streak, self.current_streak)
            self.success_flash = 1.0
            self.celebrating = True
            self.celebration_timer = 0.0

        elif self.move_timer >= self.move_timeout:
            # Time's up - missed this move
            events['miss'] = True
            self.moves_missed += 1
            self.current_streak = 0
            self.miss_flash = 1.0
            self._next_move()

        # Check if entire sequence is complete
        if self.current_move_index >= len(self.current_sequence.moves):
            self.loop_count += 1
            if self.loop_count >= self.max_loops:
                events['sequence_complete'] = True
            else:
                # Loop the sequence
                self.current_move_index = 0

        return events

    def _next_move(self):
        """Advance to the next move."""
        self.current_move_index += 1
        self.move_timer = 0.0
        self.left_hand_hit = False
        self.right_hand_hit = False
        self.left_hit_time = 0.0
        self.right_hit_time = 0.0
        self.celebrating = False
        self.celebration_timer = 0.0

    def get_time_remaining(self) -> float:
        """Get time remaining for current move."""
        return max(0, self.move_timeout - self.move_timer)

    def get_time_progress(self) -> float:
        """Get progress through current move time (0.0 to 1.0)."""
        return min(1.0, self.move_timer / self.move_timeout)

    def get_score(self) -> int:
        """Calculate current score."""
        base_points = self.moves_completed * 100
        streak_bonus = self.best_streak * 50
        return base_points + streak_bonus

    def get_stats(self) -> Dict:
        """Get current game stats."""
        total_moves = self.moves_completed + self.moves_missed
        accuracy = (self.moves_completed / total_moves * 100) if total_moves > 0 else 0

        return {
            'score': self.get_score(),
            'moves_hit': self.moves_completed,
            'moves_missed': self.moves_missed,
            'accuracy': accuracy,
            'current_streak': self.current_streak,
            'best_streak': self.best_streak,
            'dance_name': self.current_sequence.name if self.current_sequence else "",
        }

    def is_sequence_complete(self) -> bool:
        """Check if the current sequence is fully complete."""
        if not self.current_sequence:
            return True
        return self.loop_count >= self.max_loops
