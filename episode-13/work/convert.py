import sys
import json
import math
import glm # from pyglm

name = sys.argv[1]

f = open(f"work/models/{name}.json")
data, = json.load(f).values()
f.close()

x_res = data["texturewidth"]
y_res = data["textureheight"]

bones = data["bones"]

PIXEL_SIZE = 1 / 16

def map_vertices(*vertices):
	return [*map(lambda x: x * PIXEL_SIZE, vertices)]

def map_tex_coords(*tex_coords):
	*u, = map(lambda u:     u / x_res, tex_coords[0::2])
	*v, = map(lambda v: 1 - v / y_res, tex_coords[1::2])

	return sum(map(list, zip(u, v, [0] * len(u))), [])

vertices   = []
tex_coords = []
shading_values = []

def process_cube(cube):
	x, y, z    = cube["origin"]
	pivot      = cube["pivot"]
	rotation   = cube["rotation"]
	sx, sy, sz = cube["size"]
	u, v       = cube["uv"] # note that UV's start from the top-left (because... well... just because... idk)

	# snap rotation, because our dataset is a bit weird

	*rotation, = map(lambda x: round(x / 90) * 90, rotation)

	# construct transformation matrix based on pivot & rotation

	matrix = glm.translate(glm.mat4(), glm.vec3(pivot))
	matrix = glm.rotate(matrix, -math.radians(rotation[0]), glm.vec3(1, 0, 0))
	matrix = glm.rotate(matrix, -math.radians(rotation[1]), glm.vec3(0, 1, 0))
	matrix = glm.rotate(matrix, -math.radians(rotation[2]), glm.vec3(0, 0, 1))
	matrix = glm.translate(matrix, glm.vec3([-x for x in pivot]))

	def transform(*vector):
		return (*(matrix * glm.vec3(vector)),)

	# front/back faces

	vertices.append(map_vertices(
		*transform(x,      y,      z),
		*transform(x,      y + sy, z),
		*transform(x + sx, y + sy, z),
		*transform(x + sx, y,      z),
	))

	tex_coords.append(map_tex_coords(
		u + sz,      v + sz + sy,
		u + sz,      v + sz,
		u + sz + sx, v + sz,
		u + sz + sx, v + sz + sy,
	))

	vertices.append(map_vertices(
		*transform(x + sx, y,      z + sz),
		*transform(x + sx, y + sy, z + sz),
		*transform(x,      y + sy, z + sz),
		*transform(x,      y,      z + sz),
	))

	tex_coords.append(map_tex_coords(
		u + sz + sx + sz,      v + sz + sy,
		u + sz + sx + sz,      v + sz,
		u + sz + sx + sz + sx, v + sz,
		u + sz + sx + sz + sx, v + sz + sy,
	))

	# top/bottom faces

	vertices.append(map_vertices(
		*transform(x,      y + sy, z     ),
		*transform(x,      y + sy, z + sz),
		*transform(x + sx, y + sy, z + sz),
		*transform(x + sx, y + sy, z     ),
	))

	tex_coords.append(map_tex_coords(
		u + sz,      v + sz,
		u + sz,      v,
		u + sz + sx, v,
		u + sz + sx, v + sz,
	))

	vertices.append(map_vertices(
		*transform(x + sx, y, z     ),
		*transform(x + sx, y, z + sz),
		*transform(x,      y, z + sz),
		*transform(x,      y, z     ),
	))

	tex_coords.append(map_tex_coords(
		u + sz + sx,      v + sz,
		u + sz + sx,      v,
		u + sz + sx + sx, v,
		u + sz + sx + sx, v + sz,
	))

	# left/right faces

	vertices.append(map_vertices(
		*transform(x + sx, y,      z     ),
		*transform(x + sx, y + sy, z     ),
		*transform(x + sx, y + sy, z + sz),
		*transform(x + sx, y,      z + sz),
	))

	tex_coords.append(map_tex_coords(
		u + sz + sx,      v + sz + sy,
		u + sz + sx,      v + sz,
		u + sz + sx + sz, v + sz,
		u + sz + sx + sz, v + sz + sy,
	))

	vertices.append(map_vertices(
		*transform(x, y,      z + sz),
		*transform(x, y + sy, z + sz),
		*transform(x, y + sy, z     ),
		*transform(x, y,      z     ),
	))

	tex_coords.append(map_tex_coords(
		u,      v + sz + sy,
		u,      v + sz,
		u + sz, v + sz,
		u + sz, v + sz + sy,
	))

	for _ in range(6):
		shading_values.append([1.0, 1.0, 1.0, 1.0])

def process_bone(bone):
	cubes = bone["cubes"]

	for cube in cubes:
		process_cube(cube)

# process the model

for bone in bones:
	process_bone(bone)

# output model

out = f"""
transparent = True
is_cube = False
glass = False

colliders = []

vertex_positions = {vertices}
tex_coords = {tex_coords}
shading_values = {shading_values}
"""

with open(f"models/{name}.py", "w") as f:
	f.write(out)