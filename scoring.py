"""
Scoring System
Handles current score tracking, high score persistence, and score display.
"""

import json
import os
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, asdict


@dataclass
class ScoreData:
    """Represents score information."""
    high_score: float = 0.0
    high_score_hits: int = 0
    total_games: int = 0
    total_time_played: float = 0.0


class ScoringSystem:
    """
    Manages game scoring including current score, high scores,
    and persistent storage.
    """

    def __init__(self, save_file: str = "highscore.json"):
        """
        Initialize the scoring system.

        Args:
            save_file: Path to save high scores
        """
        self.save_path = Path(save_file)

        # Current game stats
        self.current_time = 0.0
        self.current_hits = 0
        self.is_active = False

        # Persistent stats
        self.data = self._load_scores()

    def _load_scores(self) -> ScoreData:
        """Load scores from file."""
        if self.save_path.exists():
            try:
                with open(self.save_path, 'r') as f:
                    data = json.load(f)
                    return ScoreData(**data)
            except (json.JSONDecodeError, TypeError, KeyError) as e:
                print(f"Warning: Could not load scores: {e}")

        return ScoreData()

    def _save_scores(self):
        """Save scores to file."""
        try:
            with open(self.save_path, 'w') as f:
                json.dump(asdict(self.data), f, indent=2)
        except IOError as e:
            print(f"Warning: Could not save scores: {e}")

    def start_game(self):
        """Start a new game round."""
        self.current_time = 0.0
        self.current_hits = 0
        self.is_active = True

    def update(self, dt: float):
        """
        Update the current score.

        Args:
            dt: Delta time in seconds
        """
        if self.is_active:
            self.current_time += dt

    def record_hit(self):
        """Record a balloon hit."""
        if self.is_active:
            self.current_hits += 1

    def end_game(self):
        """End the current game round and update high scores."""
        if not self.is_active:
            return

        self.is_active = False

        # Update statistics
        self.data.total_games += 1
        self.data.total_time_played += self.current_time

        # Check for new high score
        if self.current_time > self.data.high_score:
            self.data.high_score = self.current_time
            self.data.high_score_hits = self.current_hits
            self._save_scores()
            return True  # New high score!

        self._save_scores()
        return False

    def get_current_score(self) -> float:
        """Get current game time in seconds."""
        return self.current_time

    def get_current_score_formatted(self) -> str:
        """Get current score as formatted string."""
        return self._format_time(self.current_time)

    def get_high_score(self) -> float:
        """Get high score in seconds."""
        return self.data.high_score

    def get_high_score_formatted(self) -> str:
        """Get high score as formatted string."""
        return self._format_time(self.data.high_score)

    def get_current_hits(self) -> int:
        """Get number of hits in current game."""
        return self.current_hits

    def get_stats(self) -> dict:
        """Get all game statistics."""
        return {
            'current_time': self.current_time,
            'current_time_formatted': self.get_current_score_formatted(),
            'current_hits': self.current_hits,
            'high_score': self.data.high_score,
            'high_score_formatted': self.get_high_score_formatted(),
            'high_score_hits': self.data.high_score_hits,
            'total_games': self.data.total_games,
            'total_time_played': self.data.total_time_played,
            'is_active': self.is_active,
        }

    def reset_high_scores(self):
        """Reset all high scores (use with caution!)."""
        self.data = ScoreData()
        self._save_scores()

    @staticmethod
    def _format_time(seconds: float) -> str:
        """Format seconds into MM:SS.ms format."""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        ms = int((seconds % 1) * 100)
        return f"{minutes:02d}:{secs:02d}.{ms:02d}"
