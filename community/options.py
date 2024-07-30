# FAST = 0; FANCY = 1
import pyglet.gl as gl

# Render Distance (in chunks)
RENDER_DISTANCE = 4

# Field of view
FOV = 90

# --------------------------------- Performance ---------------------------------

# Indirect Rendering
INDIRECT_RENDERING = False  # Requires OpenGL 4.2+. Disable if having issues.
# Indirect rendering caches the draw command parameters in a seperate indirect command buffer,
# thus reducing the amount of data needed to supply the draw call

# Conditional Rendering with Occlusion queries
ADVANCED_OPENGL = False  # Not recommended unless using NVIDIA cards.
# Might cause more slowdowns that speedups.
# Do not expect any concrete framerate improvement.
# Max number of chunk updates per chunk every tick
CHUNK_UPDATES = 4

# Vertical Sync
VSYNC = False

# Max CPU ahead frames
MAX_CPU_AHEAD_FRAMES = 3  # Number of frames the CPU can be ahead of the GPU until waiting for it to finish rendering.
# Higher values gives higher framerate but causes framerate instability and higher frame spikes
# Lower values causes average lower framerate but gives smoother framerate
# Recommended values are between 0 and 9

# Legacy Smooth FPS
SMOOTH_FPS = False  # Legacy way to force the flushing of command buffer and forces the CPU to wait for the GPU to finish rendering.
# Incompatible Max CPU Ahead Frames (it won't be effective)
# Enable this to test whether its impact is better. Similar to Max CPU Ahead frames to 0

# --------------------------------- Quality ---------------------------------

# Ambient Occlusion and Smooth Lighting
SMOOTH_LIGHTING = True  # Smooth Lighting smoothes the light of each vertex to achieve a linear interpolation
# of light on each fragment, hence creating a smoother light effect
# It also adds ambient occlusion, to simulate light blocked by opaqua objects
# Chunk updates / building will be severely affecteds by this feature

# Better Translucency blending
FANCY_TRANSLUCENCY = True

# Minification Filter
MIPMAP_TYPE = gl.GL_NEAREST  # Linear filtering samples the texture in a bilinear way in the distance,
# however its effect is negligible and should not be used.
# Mipmaps generates lower detailed textures
# that will be sampled in high distances, thus reducing aliasing.
# Possible filters:
# No filter (GL_NEAREST)
# Linear filter (GL_LINEAR),
# Nearest mipmap (GL_NEAREST_MIPMAP_NEAREST),
# Linear mipmap (GL_NEAREST_MIPMAP_LINEAR)
# Bilinear mipmap (GL_LINEAR_MIPMAP_NEAREST)
# Trilinear mipmap (GL_LINEAR_MIPMAP_LINEAR)

# Colored Lighting
COLORED_LIGHTING = True  # Uses an alternative shader program to achieve a more colored lighting
# No performance impact should happen
# It aims to look similar to Beta 1.8+
# Disable for authentic Alpha - Beta look

# Multisample Anti-aliasing (might not work)
ANTIALIASING = 0
