"""
Player Detection Module using MediaPipe Pose Detection
Detects players via webcam and tracks their body positions for game interaction.
"""

import cv2
import numpy as np
from dataclasses import dataclass
from typing import List, Optional, Tuple

# Import MediaPipe tasks API (new API for mediapipe >= 0.10.0)
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision


@dataclass
class PlayerLandmarks:
    """Represents detected landmarks for a single player."""
    # Key body parts for collision detection
    left_hand: Optional[Tuple[float, float]] = None
    right_hand: Optional[Tuple[float, float]] = None
    left_elbow: Optional[Tuple[float, float]] = None
    right_elbow: Optional[Tuple[float, float]] = None
    left_shoulder: Optional[Tuple[float, float]] = None
    right_shoulder: Optional[Tuple[float, float]] = None
    nose: Optional[Tuple[float, float]] = None
    # For avatar rendering (hips only, no legs)
    left_hip: Optional[Tuple[float, float]] = None
    right_hip: Optional[Tuple[float, float]] = None
    # Visibility flag
    is_visible: bool = False
    # Bounding box for player (x, y, width, height)
    bbox: Optional[Tuple[int, int, int, int]] = None
    # Tracking ID for stability
    track_id: int = 0

    def get_collision_points(self) -> List[Tuple[float, float]]:
        """Returns all points that can collide with the balloon."""
        points = []
        for point in [self.left_hand, self.right_hand, self.left_elbow,
                      self.right_elbow, self.nose]:
            if point is not None:
                points.append(point)
        return points

    def get_head_position(self) -> Optional[Tuple[float, float]]:
        """Returns the head/nose position for avatar face placement."""
        return self.nose


# Landmark indices for pose detection
class PoseLandmarkIndex:
    NOSE = 0
    LEFT_EYE_INNER = 1
    LEFT_EYE = 2
    LEFT_EYE_OUTER = 3
    RIGHT_EYE_INNER = 4
    RIGHT_EYE = 5
    RIGHT_EYE_OUTER = 6
    LEFT_EAR = 7
    RIGHT_EAR = 8
    MOUTH_LEFT = 9
    MOUTH_RIGHT = 10
    LEFT_SHOULDER = 11
    RIGHT_SHOULDER = 12
    LEFT_ELBOW = 13
    RIGHT_ELBOW = 14
    LEFT_WRIST = 15
    RIGHT_WRIST = 16
    LEFT_PINKY = 17
    RIGHT_PINKY = 18
    LEFT_INDEX = 19
    RIGHT_INDEX = 20
    LEFT_THUMB = 21
    RIGHT_THUMB = 22
    LEFT_HIP = 23
    RIGHT_HIP = 24
    LEFT_KNEE = 25
    RIGHT_KNEE = 26
    LEFT_ANKLE = 27
    RIGHT_ANKLE = 28
    LEFT_HEEL = 29
    RIGHT_HEEL = 30
    LEFT_FOOT_INDEX = 31
    RIGHT_FOOT_INDEX = 32


class PlayerDetector:
    """Handles webcam capture and player pose detection using MediaPipe."""

    def __init__(self, camera_index: int = 0, detection_confidence: float = 0.5,
                 tracking_confidence: float = 0.5):
        """
        Initialize the player detector.

        Args:
            camera_index: Webcam device index (0 for built-in)
            detection_confidence: Minimum confidence for pose detection
            tracking_confidence: Minimum confidence for pose tracking
        """
        self.camera_index = camera_index
        self.cap = None
        self.frame_width = 1280
        self.frame_height = 720
        self.detection_confidence = detection_confidence
        self.tracking_confidence = tracking_confidence

        # Pose landmarker will be initialized when we have model
        self.pose_landmarker = None
        self.latest_result = None

        # Store the last frame for display
        self.last_frame = None
        self.last_frame_rgb = None

        # Smoothing and stability
        self.smooth_factor = 0.3  # Lower = more smoothing
        self.previous_landmarks = {}  # Store previous positions for smoothing
        self.player_positions = []  # Track player positions for stable assignment
        self.frames_since_detection = {}  # Track how long since each player was seen

        # Detection region (percentage from edge to ignore)
        # e.g., 0.1 means ignore outer 10% on each side
        self.detection_margin = 0.1

        # Initialize the pose landmarker
        self._init_pose_landmarker()

    def _init_pose_landmarker(self):
        """Initialize MediaPipe Pose Landmarker."""
        try:
            # Create pose landmarker options
            base_options = python.BaseOptions(
                model_asset_path=self._get_model_path()
            )
            options = vision.PoseLandmarkerOptions(
                base_options=base_options,
                running_mode=vision.RunningMode.VIDEO,
                num_poses=4,  # Support up to 4 players
                min_pose_detection_confidence=self.detection_confidence,
                min_pose_presence_confidence=self.detection_confidence,
                min_tracking_confidence=self.tracking_confidence,
            )
            self.pose_landmarker = vision.PoseLandmarker.create_from_options(options)
            print("MediaPipe Pose Landmarker initialized successfully")
        except Exception as e:
            print(f"Warning: Could not initialize pose landmarker: {e}")
            self.pose_landmarker = None

    def _get_model_path(self) -> str:
        """Get or download the pose landmarker model."""
        import os
        import urllib.request

        model_dir = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(model_dir, "pose_landmarker_lite.task")

        if not os.path.exists(model_path):
            print("Downloading pose detection model...")
            url = "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task"
            try:
                urllib.request.urlretrieve(url, model_path)
                print("Model downloaded successfully!")
            except Exception as e:
                print(f"Could not download model: {e}")
                raise

        return model_path

    def start(self) -> bool:
        """Start the webcam capture. Returns True if successful."""
        self.cap = cv2.VideoCapture(self.camera_index)
        if not self.cap.isOpened():
            print(f"Error: Could not open camera {self.camera_index}")
            return False

        # Set resolution
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_height)

        # Get actual resolution (camera might not support requested)
        self.frame_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.frame_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        print(f"Camera started: {self.frame_width}x{self.frame_height}")
        return True

    def stop(self):
        """Stop the webcam capture and release resources."""
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        if self.pose_landmarker is not None:
            self.pose_landmarker.close()

    def detect_players(self, game_width: int, game_height: int) -> List[PlayerLandmarks]:
        """
        Detect players in the current webcam frame.

        Args:
            game_width: Width of the game screen (for coordinate mapping)
            game_height: Height of the game screen (for coordinate mapping)

        Returns:
            List of PlayerLandmarks (currently supports single player)
        """
        if self.cap is None or not self.cap.isOpened():
            return []

        ret, frame = self.cap.read()
        if not ret:
            return []

        # Mirror the frame so player sees themselves correctly
        frame = cv2.flip(frame, 1)

        # Convert BGR to RGB for MediaPipe
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        self.last_frame = frame
        self.last_frame_rgb = frame_rgb

        players = []

        if self.pose_landmarker is not None:
            try:
                # Create MediaPipe Image
                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)

                # Get timestamp in milliseconds
                timestamp_ms = int(cv2.getTickCount() / cv2.getTickFrequency() * 1000)

                # Detect pose
                result = self.pose_landmarker.detect_for_video(mp_image, timestamp_ms)

                if result.pose_landmarks and len(result.pose_landmarks) > 0:
                    # Process all detected poses (up to 4 players)
                    # Sort by x-position for consistent player ordering (left to right)
                    pose_data = []
                    for landmarks in result.pose_landmarks:
                        # Get center x position for sorting
                        if len(landmarks) > PoseLandmarkIndex.LEFT_SHOULDER:
                            center_x = landmarks[PoseLandmarkIndex.LEFT_SHOULDER].x
                            pose_data.append((center_x, landmarks))

                    pose_data.sort(key=lambda x: x[0])

                    for idx, (_, landmarks) in enumerate(pose_data):
                        player = self._extract_landmarks(landmarks, game_width, game_height, idx)
                        if player.is_visible and self._is_in_detection_region(player, game_width, game_height):
                            players.append(player)

            except Exception as e:
                print(f"Pose detection error: {e}")

        return players

    def _is_in_detection_region(self, player: PlayerLandmarks, game_width: int, game_height: int) -> bool:
        """Check if player's center is within the detection region."""
        # Get player center from shoulders
        if not player.left_shoulder or not player.right_shoulder:
            return False

        center_x = (player.left_shoulder[0] + player.right_shoulder[0]) / 2
        center_y = (player.left_shoulder[1] + player.right_shoulder[1]) / 2

        # Calculate bounds
        min_x = game_width * self.detection_margin
        max_x = game_width * (1 - self.detection_margin)
        min_y = game_height * self.detection_margin
        max_y = game_height * (1 - self.detection_margin)

        return min_x <= center_x <= max_x and min_y <= center_y <= max_y

    def set_detection_margin(self, margin: float):
        """Set the detection margin (0.0 to 0.4). Higher = smaller detection area."""
        self.detection_margin = max(0.0, min(0.4, margin))

    def get_detection_bounds(self, width: int, height: int) -> Tuple[int, int, int, int]:
        """Get the detection region bounds as (x, y, w, h)."""
        margin_x = int(width * self.detection_margin)
        margin_y = int(height * self.detection_margin)
        return (margin_x, margin_y, width - 2 * margin_x, height - 2 * margin_y)

    def _extract_landmarks(self, landmarks, game_width: int,
                           game_height: int, player_idx: int) -> PlayerLandmarks:
        """Extract and scale landmarks to game coordinates with smoothing."""
        player = PlayerLandmarks()
        player.track_id = player_idx

        def scale_point(idx: int, point_name: str) -> Optional[Tuple[float, float]]:
            """Scale normalized coordinates to game coordinates with smoothing."""
            if idx >= len(landmarks):
                return None
            landmark = landmarks[idx]
            if landmark.visibility < 0.6:  # Higher threshold for stability
                return None
            x = landmark.x * game_width
            y = landmark.y * game_height

            # Apply smoothing using previous position
            key = f"p{player_idx}_{point_name}"
            if key in self.previous_landmarks:
                prev_x, prev_y = self.previous_landmarks[key]
                x = prev_x + (x - prev_x) * self.smooth_factor
                y = prev_y + (y - prev_y) * self.smooth_factor

            self.previous_landmarks[key] = (x, y)
            return (x, y)

        # Extract key landmarks using indices (no legs)
        # Note: Frame is mirrored for display, so we swap left/right from MediaPipe
        # This way player's left hand (appears on left side of screen) matches left targets
        player.nose = scale_point(PoseLandmarkIndex.NOSE, 'nose')
        player.left_shoulder = scale_point(PoseLandmarkIndex.RIGHT_SHOULDER, 'l_shoulder')
        player.right_shoulder = scale_point(PoseLandmarkIndex.LEFT_SHOULDER, 'r_shoulder')
        player.left_elbow = scale_point(PoseLandmarkIndex.RIGHT_ELBOW, 'l_elbow')
        player.right_elbow = scale_point(PoseLandmarkIndex.LEFT_ELBOW, 'r_elbow')
        player.left_hand = scale_point(PoseLandmarkIndex.RIGHT_WRIST, 'l_hand')
        player.right_hand = scale_point(PoseLandmarkIndex.LEFT_WRIST, 'r_hand')
        player.left_hip = scale_point(PoseLandmarkIndex.RIGHT_HIP, 'l_hip')
        player.right_hip = scale_point(PoseLandmarkIndex.LEFT_HIP, 'r_hip')

        # Calculate bounding box if enough landmarks visible
        visible_points = []
        for attr in ['nose', 'left_shoulder', 'right_shoulder', 'left_hip',
                     'right_hip', 'left_hand', 'right_hand']:
            point = getattr(player, attr)
            if point is not None:
                visible_points.append(point)

        if len(visible_points) >= 3:
            player.is_visible = True
            xs = [p[0] for p in visible_points]
            ys = [p[1] for p in visible_points]
            min_x, max_x = min(xs), max(xs)
            min_y, max_y = min(ys), max(ys)
            padding = 20
            player.bbox = (
                int(min_x - padding),
                int(min_y - padding),
                int(max_x - min_x + 2 * padding),
                int(max_y - min_y + 2 * padding)
            )

        return player

    def get_camera_frame(self) -> Optional[np.ndarray]:
        """Get the last captured frame (RGB format) for display."""
        return self.last_frame_rgb

    def get_frame_dimensions(self) -> Tuple[int, int]:
        """Get the camera frame dimensions."""
        return (self.frame_width, self.frame_height)
