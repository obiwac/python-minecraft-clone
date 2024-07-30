# MCPY

Source code for each episode of my Minecraft clone in Python YouTube tutorial series.

![Screenshot from the community directory](eyecandy/creeper.png)

## Introduction

Click on the thumbnail below to watch the introduction video:

[<img alt = "Introduction" src = "https://i.imgur.com/gMBuSJb.png" width = 25% />](https://youtu.be/YgvNuY8Iq6Q?list=PL6_bLxRDFzoKjaa3qCGkwR5L_ouSreaVP)

## Prerequisites

Here is the setup video for Windows 10:

[<img alt = "Setup: Windows 10" src = "https://i.imgur.com/VVQrYbG.png" width = 25% />](https://youtu.be/lrAIYPlvMZw?list=PL6_bLxRDFzoKjaa3qCGkwR5L_ouSreaVP)

And for Debian-based Linux distros:

[<img alt = "Setup: Linux" src = "https://i.imgur.com/9rZiv4B.png" width = 25% />](https://youtu.be/TtkTkfwwefA?list=PL6_bLxRDFzoKjaa3qCGkwR5L_ouSreaVP)

The `pyglet` module is a necessary dependency for all episodes, the `nbtlib` & `base36` modules are necessary dependencies for all episodes starting with 11, and the `pyglm` module is necessary for the `community` directory. You can install them with PIP by issuing:

```console
pip install --user pyglet nbtlib base36 pyglm
```

Optionally (and this is the recommended for episodes 13 and above as well as the `community` directory), you can use [Poetry](https://python-poetry.org/) for dependency and virtual environment management:

```console
poetry install --no-root --with dev
```

## Running

Run the following command in the directory of any episode to run the result from that episode:

```console
python3 main.py
```

This tutorial requires Python version 3.8 minimum (#56, with only a few changes though, it can run on versions much lower).

If you are using Poetry, you can run the following command:

```console
poetry run python main.py
```

## Episodes

Here is a list of all the episodes and a brief description of what each one of them covers:

- Intro/EP0: These videos just present the project and the series and show how to set up the environment on Linux and Windows for subsequent episodes.
- EP1: In this episode, we create a window and set up an OpenGL context with Pyglet to draw a simple colour to the screen.
- EP2: This episode covers vertex buffers (VAO/VBO) and indices, which we use to draw a quadrilateral to the screen.
- EP3: Vertex and fragment shaders are introduced in this episode, which we use to colour in our quadrilateral with a colour gradient.
- EP4: We make the scene 3D by introducing projection matrices. The result of this episode is a square rotating in 3D space.
- EP5: In this episode, we introduce textures, texture arrays, and texture coordinates to our project, which we use to create our first block model. We also enable depth testing.
- EP6: We take care of input handling and the camera in this episode, which allows us to move around the cube in 3D space.
- EP7: Very quick episode to shade our block differently for each face, to help with depth perception and distinguish it with texturally similar blocks surrounding it.
- EP8: We introduce the concept of chunks and chunk mesh generation in this episode, which allows us to render a large number of blocks efficiently.
- EP9: In this episode, we add blocks with different block models than the cubes we've been working with so far. It also covers discarding fragments for transparency and texture filtering.
- EP10: This episode introduces maybe the most important feature of Minecraft; block breaking and placing.
- EP11: Until now, changes to the world could not be saved and loaded later. This episode introduces the NBT format and the `nbtlib` module to save and load world chunks.
- EP12a: Before this episode we could just phase through blocks. Collisions are introduced in this episode, which prevents this.
- EP12b: The player until now was also not affected by gravity or any kind of physics-based movement. This episode introduces gravity, jumping, and proper physics-based movement.

The following episodes have been planned, but the videos for them have not been made:

- EP13a: The code has gotten a little crusty. This episode restructures the codebase, adds a `pyproject.toml` file and switches to Poetry for better dependency management, and adds a formatter and a linter as well as a CI setup to check all this.
- EP13b: Loading big save files took a long time before this. This episode covers profiling and optimization techniques and rewrites a lot of the chunk loading code in Cython to speed it up dramatically.
- EP14: This episode adds mobs, which are non-player entities in the world which can move around on their own. This will probably be split into multiple parts, notably one for adding the mobs themselves (which will probably include player interactions and a basic combat system), pathfinding and AI, animations, and finally lighting (maybe with shadows too?).
- EP15: This is not totally confirmed yet but I'd like this episode to cover basic 2D UI elements such as a reticle, and maybe even a GUI system with a hotbar and whatnot.

Here is a wishlist of other episodes I'd like to make in the future after the aforementioned ones are completed, but that I don't have a clear plan for yet:

- Sky boxes.
- Partial transparency for water.
- More advanced shaders such as wavy water and leaves, reflections, and bloom.
- Networked multiplayer, possibly compatible with other Minecraft clients?
- Split screen multiplayer with scissoring? Thought that's maybe not worth making a video on, but I think it would be cool to have that in `community`.
- (Infinite) terrain generation.

Feel free to send me suggestions for future episodes you'd like to see!

## Community

The `community` directory is for experiments & contributions made by other people on the latest tutorial's code (see PR [#29](https://github.com/obiwac/python-minecraft-clone/pull/29)).
It more generally extends the project with functionality I've yet to cover in a tutorial or that I don't intend on covering at all.
Characteristic contributions are contributions which *add* something to the code.
Contributions which *fix* something are still merged on the source of all episodes.

The community has several features and options that can be toggled in `options.py`:
- Render Distance: At what distance (in chunks) should chunks stop being rendered
- FOV: Camera field of view

- Indirect Rendering: Alternative way of rendering that has less overhead but is only supported on devices supporting OpenGL 4.2
- Advanced OpenGL: Rudimentary occlusion culling using hardware occlusion queries, however it is not performant and will cause pipeline stalls and decrease performance on most hardware - mostly for testing if it improves framerate
- Chunk Updates: Chunk updates per chunk every tick - 1 gives the best performance and best framerate, however, as Python is an slow language, 1 may increase chunk building time by an ludicrous amount
- Vsync: Vertical sync, may yield smoother framerate but bigger frame times and input lag
- Max CPU Ahead frames: Number of frames that the CPU can go ahead of a frame before syncing with the GPU by waiting for it to complete the execution of the command buffer, using `glClientWaitSync()`
- Smooth FPS: Legacy CPU/GPU sync by forcing the flushing and completion of command buffer using `glFinish()`, not recommended - similar to setting Max CPU Ahead Frames to 0. Mostly for testing whether it makes any difference with `glClientWaitSync()`

- Smooth lighting: Smoothes the light of each vertex to achieve a linear interpolation of light on each fragment, hence creating a smoother light effect - it also adds ambient occlusion, to simulate light blocked by opaque objects (chunk update/build time will be severely affected by this feature)
- Fancy translucency: Better translucency blending, avoid weird looking artefacts - disable on low-end hardware
- Mipmap (minification filtering): Texture filtering used on higher distances. Default is `GL_NEAREST` (no filtering) (more info in `options.py`)
- Colored lighting: Uses an alternative shader program to achieve a more colored lighting; it aims to look similar to Beta 1.8+ (no performance loss should be incurred)
- Antialiasing: Experimental feature

## List of projects based on this

- **Nim implementation:** https://github.com/phargobikcin/nim-minecraft-clone
- **Java implementation:** https://github.com/StartForKillerMC/JavaMinecraft
- **C++ implementation:** https://github.com/Jukitsu/CppMinecraft-clone
- **Odin implementation:** https://github.com/anthony-63/lvo
- **Lua implementation:** https://github.com/brennop/lunarcraft
- **Javascript implementation:** https://github.com/drakeerv/js-minecraft-clone ([Demo](https://drakeerv.github.io/js-minecraft-clone/))
