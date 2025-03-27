# NOT FINISHED

This branch is still **IN DEVELOPMENT** and may contain incomplete code. 

> **you have been informed**

# Maze Runners

A game where you try to beat an endless number of mazes.

## BETA Releases

Beta releases will be stored as different branches, but may be *deleted*. The source code for these versions can be found in the `source` folder.

The game is currently compiled as Beta 0.2 (version 0.0.2).

### Version Naming Convention

Versions follow this naming structure:

`type.version.patch`

type:

- beta (0.x.x) - Beta versions

- indev (-1.x.x and beyond) - In-development versions

- release (1.x.x and beyond) - Stable releases

Examples:
- Beta 0.2 (0.0.2)
- indev 0.4 (-1.0.4)
- release 1.0 (1.1.0)

> *Beta versions and/or branches might not be included in the final release list once the project moves to the indev or stable phase.*

## Source

Maze Runners is written in **Python** and primarily developed using **VS Code**, though other editors should work fine.

Please read the license carefully before using or modifying the code.

### No splash screen?

The game is compiled using `auto-py-to-exe`, which includes a *built-in splash screen* feature.

Splash screen functions are present in the source code but are disabled by default as comments:

```python

import pyi_splash 

# ...

pyi_splash.close()

```

### Download

To download the `main branch`, run the following command:
```bash

git clone https://github.com/studio-a-productions/maze_runners.git

```

## Want to Suggest Features?

We welcome feature suggestions!

You can Suggest Features in 2 ways:

1.  **Quick and Easy:**
    
    Go to '`Issues`' in the repository and write your suggestion.

2.  **Community:**

    You can start a `Discussion` in the repository, where everyone can give you their own thoughts on the feature. **Note:** `Discussions` may take longer to be reviewed compared to direct issue submissions.

And if your idea is approved, it might be added to the game. Of course, you'll receive credit for your *contribution*!

## Bug Reports

Found a bug or facing issues? Report it in the '`Issues`' tab as soon as possible!

We aim to keep Maze Runners *bug-free*. If your reported issue is not resolved in upcoming updates and doesn't have the `wontfix` label, you can:

1. Start a discussion about it.

2. Contribute by fixing it yourself and submitting a pull request.

## Roadmap

>Maze Runners roadmap for the BETA releases

### BETA 0.3

In `Beta 0.3`, we wanted to focus on adding more powerups and features to the game. For this update, we've fixed the `Divine Eyes` powerup.

Also we've deployed a new, handy powerup: `Angelic Shield`, which should spawn everywhere except the `small` levels.

# Contribution 
> A guide to contributing to the project. (Coming soon!)