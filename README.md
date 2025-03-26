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

> *Beta versions will not be included in the official release list once the project enters the indev or stable release phase.*

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

You can start a discussion in the repository, and if your idea is approved, it might be added to the game. Of course, you'll receive credit for your *contribution*!

## Bug Reports

Found a bug or facing issues? Report them **as soon as possible!**

We aim to keep Maze Runners *bug-free*. If your reported issue is not resolved in upcoming updates, you can:

1. Start a discussion about it.

2. Contribute by fixing it yourself and submitting a pull request.

---

# Contribution 
> A guide to contributing to the project. (Coming soon!)