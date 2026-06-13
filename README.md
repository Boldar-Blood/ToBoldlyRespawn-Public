# To Boldly Respawn: A Co-Op Space Disaster

A humorous, legally safe arcade space-shooter RPG prototype built in Python 3.11+ with Panda3D.

Current public preview: **0.2.0a1**.

## Gameplay premise

You are not charging heroically into space combat. You are fleeing a corporate fleet while firing backward, dodging pursuers, grabbing emergency supplies, and trying to survive long enough to push the pursuing dreadnought away.

Core controls:

- **Arrow Keys / WASD**: Move.
- **Spacebar**: Fire rear-mounted lasers.
- **C**: Fire a missile when available.
- **B**: Use a smart bomb when available.
- **Enter**: Start or advance menus and story screens.
- **Number Keys 1-9**: Pick story choices when available.
- **R**: Restart.
- **P**: Pause.
- **F1**: Toggle the progression log.

## Included in this public snapshot

This repository contains the public runtime/source snapshot:

- game source under `src/`
- gameplay data and public assets under `data/`
- package metadata and setup files
- public README, changelog, and licensing information

Development-only planning notes, local caches, build output, and private maintenance files are intentionally excluded from this public snapshot.

## Install and run from source

Use Python 3.11 or later.

```bash
python -m pip install --upgrade pip
python -m pip install -e .
python -m space_demo.main
```

For a headless smoke run:

```bash
python -m space_demo.main --headless
```

## Packaged releases

Packaged preview builds are attached to GitHub Releases when available. This repository is the public source/runtime mirror.

## Asset and licensing notes

Graphics are constructed from project-local procedural fallbacks, Panda3D primitives, or original curated PNG assets placed under `data/sprites/`. Do not add third-party franchise logos, protected ship silhouettes, copyrighted music, fan art, or other protected assets. Keep parody and humor original, generic, and legally safe.
