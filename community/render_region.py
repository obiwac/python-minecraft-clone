import chunk

# Work in Progress #

import ctypes
import pyglet.gl as gl

class RenderRegion:
    def __init__(self, chunks):
        self.chunks = chunks
        self.vao = gl.GLuint(0)
        self.vbo = gl.GLuint(0)
        self.index_counts = []
        self.index_offsets = []
        self.base_vertices = []
    def build_draw_batch():
        pass
    def draw(self):
        gl.glBindVertexArray(self.vao)
        gl.glMultiDrawElementsBaseVertex(gl.GL_TRIANGLES,
            self.index_counts, gl.GL_UNSIGNED_INT, self.index_offsets, 
            len(self.index_counts), self.base_vertices)