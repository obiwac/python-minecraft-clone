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
                            

COLORED_LIGHTING = False
FOV = 90
INDIRECT_RENDERING = False # Requires OpenGL 4.2+. Disable if having issues.
SMOOTH_LIGHTING = False 
FPS_DISPLAY = False # May break