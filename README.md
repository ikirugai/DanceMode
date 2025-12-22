# KeepyUppy!

A fun, motion-controlled balloon game inspired by the classic "keep the balloon in the air" game! Uses your webcam to detect your body movements so you can play just like a Kinect or Wii game.

## Features

- **Motion Control**: Uses your webcam and MediaPipe pose detection to track your body movements
- **Cartoon Graphics**: Bright, colorful Bluey-inspired art style (kid-friendly!)
- **Physics-Based Gameplay**: Realistic balloon physics with gravity and random wind gusts
- **Scoring System**: Track your time and compete for high scores (persisted between sessions)
- **Easy to Play**: Just wave your hands to hit the balloon and keep it from touching the ground!

## Quick Start

### Option 1: Using the Launcher Script (Recommended)

```bash
# Make the script executable (first time only)
chmod +x run_game.sh

# Run the game
./run_game.sh
```

The launcher script will automatically:
- Create a virtual environment
- Install all dependencies
- Start the game

### Option 2: Manual Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the game
python main.py
```

## Controls

| Key | Action |
|-----|--------|
| **SPACE** | Start game / Play again |
| **ESC** | Pause / Resume / Quit |
| **R** | Restart game |

**Physical Controls**: Wave your hands in front of the webcam to hit the balloon!

## Command Line Options

```bash
python main.py --help

Options:
  --width WIDTH      Screen width (default: 1280)
  --height HEIGHT    Screen height (default: 720)
  --fullscreen       Run in fullscreen mode
```

## How to Play

1. **Start the Game**: Press SPACE on the title screen
2. **Get Ready**: A 3-second countdown will begin
3. **Keep it Up!**: Use your hands to hit the balloon and prevent it from touching the ground
4. **Watch for Wind**: Random wind gusts will push the balloon around - be ready!
5. **Beat Your Score**: Try to keep the balloon up for as long as possible

## Requirements

- macOS (tested on macOS 14+)
- Python 3.8+
- Webcam (built-in or external)
- The following Python packages:
  - pygame >= 2.5.0
  - opencv-python >= 4.8.0
  - mediapipe >= 0.10.0
  - numpy >= 1.24.0

## Camera Permissions

On first run, macOS will ask for camera permissions. You must grant access for the game to detect your movements.

If you accidentally denied access:
1. Go to **System Settings > Privacy & Security > Camera**
2. Find your terminal app (Terminal, iTerm2, etc.) or Python
3. Enable camera access

## Troubleshooting

### "Camera not detected" message
- Make sure your webcam is connected
- Grant camera permissions (see above)
- Close other apps that might be using the camera

### Game runs slowly
- Close other applications
- Try a smaller window size: `python main.py --width 800 --height 600`
- Make sure you have enough lighting for good pose detection

### Dependencies fail to install
```bash
# Try installing each package individually
pip install pygame
pip install opencv-python
pip install mediapipe
pip install numpy
```

### MediaPipe installation issues on M1/M2 Macs
```bash
# Install with Rosetta compatibility if needed
arch -x86_64 pip install mediapipe
```

## Project Structure

```
KeepyUppy/
├── main.py              # Entry point
├── game.py              # Main game loop and state management
├── balloon.py           # Balloon physics engine
├── player_detection.py  # MediaPipe pose detection
├── avatar.py            # Cartoon avatar rendering
├── scoring.py           # Score tracking and persistence
├── assets_generator.py  # Programmatic asset generation
├── requirements.txt     # Python dependencies
├── run_game.sh          # Launcher script
└── README.md            # This file
```

## Credits

- Built with [Pygame](https://www.pygame.org/)
- Pose detection powered by [MediaPipe](https://mediapipe.dev/)
- Inspired by the art style of [Bluey](https://www.bluey.tv/) (not affiliated)

## License

MIT License - Feel free to modify and share!

---

Have fun keeping that balloon up! 🎈
