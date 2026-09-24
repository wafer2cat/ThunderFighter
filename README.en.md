# Thunder Fighter

[中文](README.md)

A vertical-scrolling shooter built with Python's standard-library `tkinter`. No installation of pygame or any other third-party dependency is required.

## Launch

Run the following command in the project directory:

```bash
python main.py
```

## Controls

- `WASD` / Arrow keys: Move the fighter
- `SPACE` / `J`: Fire
- `P`: Pause / resume
- `L`: Switch the interface language between Chinese and English
- `ENTER` / `SPACE`: Start or restart the game
- `ESC`: Exit

Switching languages immediately updates the main menu, HUD, wave notifications, pause screen, and game-over screen. The current game state is preserved.

## Features

- Procedurally generated starfield background and continuous enemy waves
- Three enemy types: Scout, Heavy, and Serpentine
- Enemies may drop green energy cores; collect them to upgrade up to a three-shot spread
- A boss appears every five waves with a dedicated health bar
- Lives, score, temporary invincibility, particle explosions, screen shake, and a pause screen
