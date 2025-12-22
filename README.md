# DanceMode!

An interactive dance game where you follow on-screen dance moves using your body! Uses webcam motion tracking to detect your hand positions.

## Features

- **5 Kid-Friendly Dances**: YMCA, Baby Shark, Hokey Pokey, Macarena, Freeze Dance
- **Motion Tracking**: Uses MediaPipe pose detection via webcam
- **Colorful Dancers**: Fun stick-figure avatars that follow your movements
- **Scoring System**: Points for hitting moves, streak bonuses
- **Up to 4 Players**: Multiple people can dance together

## How to Play

1. Run `./run_game.sh`
2. Press **SPACE** to start
3. Use **LEFT/RIGHT** arrows to select a dance
4. Press **SPACE** to begin
5. Move your hands to the target circles before time runs out!
6. Get points for each move you hit

## Controls

| Key | Action |
|-----|--------|
| SPACE | Start / Select / Continue |
| LEFT/RIGHT | Choose dance |
| ESC | Pause / Quit |
| R | Replay dance |
| Q (in camera window) | Hide camera preview |

## Requirements

- macOS 12+ (or Linux/Windows with Python 3.8+)
- Webcam
- Python 3.8+

## Installation

```bash
# Clone the repo
git clone https://github.com/ikirugai/DanceMode.git
cd DanceMode

# Run the game (auto-installs dependencies)
./run_game.sh
```

## Dance Moves

### YMCA (Easy)
Make the letters with your arms!

### Baby Shark (Easy)
Chomping hand movements for each shark family member.

### Hokey Pokey (Easy)
Put your hands in, out, and shake them all about!

### Macarena (Medium)
Classic arm movements - arms out, flip, shoulders, head.

### Freeze Dance (Medium)
Strike random poses - T-pose, airplane, star, and more!

## Scoring

- **100 points** per move hit
- **50 bonus points** per streak level
- Hit moves within 2 seconds to score
- Build streaks for higher scores!

## Ratings

| Accuracy | Rating |
|----------|--------|
| 90%+ | SUPERSTAR! |
| 70%+ | Great Moves! |
| 50%+ | Good Try! |
| <50% | Keep Practicing! |
