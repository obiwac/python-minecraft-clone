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
                            
BLENDFUNC = (gl.GL_SRC_COLOR, gl.GL_ONE_MINUS_SRC_COLOR) # Possible options: 
                                                         # (gl.GL_SRC_COLOR, gl.GL_ONE_MINUS_SRC_COLOR): 
                                                         # Color blending, used by Minecraft Indev - 1.12.2,
                                                         # OR
                                                         # (gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA):
                                                         # Alpha blending, used by Minecraft Classic and 1.13 +

COLORED_LIGHTING = True