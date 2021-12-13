# python-minecraft-clone
Source code for each episode of my Minecraft clone in Python YouTube tutorial series.

## Introduction
Click on the thumbnail below to watch the introduction video:

[<img alt = "Introduction" src = "https://i.imgur.com/gMBuSJb.png" width = 25% />](https://youtu.be/YgvNuY8Iq6Q?list=PL6_bLxRDFzoKjaa3qCGkwR5L_ouSreaVP)

## Prerequisites
Here is the setup video for Windows 10:

[<img alt = "Setup: Windows 10" src = "https://i.imgur.com/VVQrYbG.png" width = 25% />](https://youtu.be/lrAIYPlvMZw?list=PL6_bLxRDFzoKjaa3qCGkwR5L_ouSreaVP)

and for Debian-based Linux distros:

[<img alt = "Setup: Linux" src = "https://i.imgur.com/9rZiv4B.png" width = 25% />](https://youtu.be/TtkTkfwwefA?list=PL6_bLxRDFzoKjaa3qCGkwR5L_ouSreaVP)

The `pyglet` module is a necessary dependency for all episodes, and the `nbtlib` and `base36` modules are necessary dependencies for all episodes starting with 11. You can install them with PIP by issuing:

```shell
$ pip install --user pyglet nbtlib base36
```

## Running
Run the following command in the directory of any episode to run the result from that episode:

```shell
$ python3 main.py
```

## Community

The `community` directory is for experiments & contributions made by other people on the latest tutorial's code (see PR #29).
It more generally extends the project with functionality I've yet to cover in a tutorial or that I don't intend on covering at all.
Characteristic contributions are contributions which *add* something to the code.
Contributions which *fix* something are still merged on the source of all episodes.

## List of projects based on this

- **Nim implementation:** https://github.com/phargobikcin/nim-minecraft-clone
- **Java implementation:** https://github.com/StartForKillerMC/JavaMinecraft
- **C++ implementation:** https://github.com/Jukitsu/CppMinecraft-clone
- **Lighting test:** https://github.com/Jukitsu/python-minecraft-clone-ep10-lighting
