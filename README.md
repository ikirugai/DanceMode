# Christmas Popper!

A festive hand-tracking game where you pop baubles, catch elves and Santa, and avoid the Grinch!

## How to Play

1. Run `./run_game.sh`
2. Press **SPACE** to start
3. Use your hands to pop targets on screen!
4. You have **60 seconds** to get the highest score!

## Targets

| Target | Points | Behavior |
|--------|--------|----------|
| Bauble | +5 | Stationary golden ornaments |
| Elf | +50 | Moves around, disappears after 3 seconds |
| Santa | +100 | Fast! Twice the speed of elves, only 3 seconds |
| Grinch | -10 | Avoid him! Moves like elves |

## Tips

- Baubles are easy but low points - rack them up!
- Elves are worth catching - watch for the green with red hat
- Santa is rare and FAST - be quick!
- The Grinch wears Santa's stolen hat - don't touch him!

## Controls

| Key | Action |
|-----|--------|
| SPACE | Start / Play Again |
| ESC | Quit |

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

## Scoring

At the end of 60 seconds, you'll see a breakdown:
- How many of each target you popped
- Points from each type
- Your total score
- Whether you beat your high score!

Merry Christmas!
