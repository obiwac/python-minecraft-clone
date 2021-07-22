#version 330

layout(location = 0) in vec3 vertex_position;
layout(location = 1) in vec3 tex_coords;
layout(location = 2) in float shading_value;

out vec3 local_position;
out vec3 interpolated_tex_coords;
out float interpolated_shading_value;

uniform mat4 matrix;

void main(void) {
	local_position = vertex_position;
	interpolated_tex_coords = tex_coords;
	interpolated_shading_value = shading_value;
	gl_Position = matrix * vec4(vertex_position, 1.0);
}