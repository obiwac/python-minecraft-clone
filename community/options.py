# FAST = 0; FANCY = 1
import pyglet.gl as gl


TRANSLUCENT_BLENDING = 1
MIPMAP_TYPE = gl.GL_NEAREST # Possible filters: 
                            # Nearest filter (GL_NEAREST)
                            # Linear filter (GL_LINEAR),
                            # Nearest mipmap (GL_NEAREST_MIPMAP_NEAREST),
                            # Linear mipmap (GL_NEAREST_MIPMAP_LINEAR)
                            # Bilinear mipmap (GL_LINEAR_MIPMAP_NEAREST)
                            # Trilinear mipmap (GL_LINEAR_MIPMAP_LINEAR)
