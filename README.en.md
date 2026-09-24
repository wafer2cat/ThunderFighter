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

## Items and progression

- `MASK`: A one-hit protective mask. It lasts for up to 10 seconds, disappears after blocking one hit, and only its aura flashes during the final 3 seconds.
- `ROCKET`: Lasts for 10 seconds. It adds rocket attacks alongside normal bullets; rockets deal heavy damage and create area explosions.
- `ENERGY`: Restores one point of `SHIELD`, up to the maximum of 5. The fighter starts each run with full 5/5 `SHIELD`.
- Enemy EXP rewards are Scout/Zigzag/Tank: 6/10/15; Bosses grant 100 EXP. Each power level uses its own requirement of 100, 250, 450, or 700 EXP, and EXP resets after every upgrade.
- After reaching power level 5, every additional 250 EXP directly grants one random `MASK`, `ROCKET`, or `ENERGY` reward.
- Normal enemies have a 6% total item drop chance, split evenly across the three items. Every defeated Boss drops one random item.

## Game content

- Procedurally generated starfield background and continuous enemy waves
- Three enemy types: Scout, Heavy, and Serpentine
- Denser enemy spawns, with lower firing frequency for normal enemies and Bosses
- Permanent experience-based power upgrades up to a five-shot spread
- A Boss appears every five waves with a dedicated health bar
- Shield, score, temporary invincibility, particle explosions, screen shake, and pause support

## Enemy pacing

- Normal enemy spawn interval: `max(0.22, 0.70 - wave * 0.025)` seconds.
- Normal enemies wait 2.0–4.0 seconds before their first shot, then 1.8–3.6 seconds between shots.
- Boss bullet patterns fire every 0.95 seconds.

## Development and verification

```bash
python -m py_compile main.py
python main.py
```
