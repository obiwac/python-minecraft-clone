# FAST = 0; FANCY = 1
import pyglet.gl as gl


FANCY_TRANSLUCENCY = 1
MIPMAP_TYPE = gl.GL_NEAREST # Possible filters: 
                            # No filter (GL_NEAREST)
                            # Linear filter (GL_LINEAR),
                            # Nearest mipmap (GL_NEAREST_MIPMAP_NEAREST),
                            # Linear mipmap (GL_NEAREST_MIPMAP_LINEAR)
                            # Bilinear mipmap (GL_LINEAR_MIPMAP_NEAREST)
                            # Trilinear mipmap (GL_LINEAR_MIPMAP_LINEAR)
                            
COLORED_LIGHTING = True
MAX_PRERENDERED_FRAMES = 3 # Number of frames the CPU can skip rendering waiting the GPU to finish rendering. 
                           # Higher values gives higher framerate but causes framerate instability and higher frame spikes
                           # Lower values causes average lower framerate but gives smoother framerate
                           # Recommended values are between 0 and 9
FAST_SKYLIGHT = True # Faster but with more glitches
FOV = 90
INDIRECT_RENDERING = False # Requires OpenGL 4.2+. Disable if having issues.
SMOOTH_LIGHTING = True 
FPS_DISPLAY = True # May break
ADVANCED_OPENGL = False # Occlusion culling. Not recommended unless using NVIDIA cards. 
                        # Might cause more slowdowns that speedups.
                        # Do not expect any concrete framerate improvement.
CHUNK_UPDATES = 1
ANTIALIASING = 0
VSYNC = False
