# DanceMode

A fun hand-tracking game for the holidays! Uses your laptop's camera to track your hand movements. Choose between Christmas and Chanukkah themes!

## What You Need

- A Mac, Windows, or Linux laptop
- A webcam (built-in is fine)
- Python installed on your computer

## How to Install Python (if you don't have it)

### Mac
1. Open **Terminal** (search for it in Spotlight)
2. Copy and paste this command, then press Enter:
   ```
   brew install python
   ```
   (If that doesn't work, download Python from https://www.python.org/downloads/)

### Windows
1. Go to https://www.python.org/downloads/
2. Click the big yellow "Download Python" button
3. Run the installer
4. **Important:** Check the box that says "Add Python to PATH"
5. Click "Install Now"

## How to Play

### Step 1: Download the Game
Click the green "Code" button on this page, then "Download ZIP". Unzip the folder.

Or if you know git:
```
git clone https://github.com/ikirugai/DanceMode.git
cd DanceMode
```

### Step 2: Run the Game

**Mac/Linux:** Double-click `run_game.sh` or open Terminal in the folder and type:
```
./run_game.sh
```

**Windows:** Open Command Prompt in the folder and type:
```
pip install pygame opencv-python mediapipe
python main.py
```

### Step 3: Choose Your Theme!

Use the **arrow keys** to select:
- **Christmas** - Baubles, Elves, Santa, and the Grinch with falling snowflakes
- **Chanukkah** - Sufganiyot (donuts), Stars of David, Menorahs, and Antiochus with spinning dreidels

Press **SPACE** or **1**/**2** to pick your theme!

### Step 4: Play!
1. Press **SPACE** to start
2. Wave your hands to pop the targets!
3. You have 60 seconds - get the highest score!

## Game Rules

| Christmas | Chanukkah | Points | Tips |
|-----------|-----------|--------|------|
| Bauble | Sufganiyah | +5 | Easy to hit, always there |
| Elf | Star of David | +50 | Moves around, disappears fast! |
| Santa | Menorah | +100 | Super fast, very rare - grab it! |
| Grinch | Antiochus | -10 | Stay away! |

## Controls

| Key | What it does |
|-----|--------------|
| Arrow Keys | Select theme |
| SPACE | Select / Start / Play again |
| 1 | Quick select Christmas |
| 2 | Quick select Chanukkah |
| F | Toggle fullscreen |
| ESC | Back to theme select / Quit |

## Troubleshooting

**"Camera not found"** - Make sure no other app is using your camera (close Zoom, FaceTime, etc.)

**"Python not found"** - You need to install Python first (see instructions above)

**Game is laggy** - Close other apps, or try a smaller window (don't use fullscreen)

## Have Fun!

Happy Holidays!
