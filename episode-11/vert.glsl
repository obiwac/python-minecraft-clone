#version 330

layout(location = 0) in vec3 vertex_position;
layout(location = 1) in vec2 texture_pointer;
layout(location = 2) in float shading_value;


out vec3 local_position;
out vec3 interpolated_tex_coords;
out float interpolated_shading_value;

uniform mat4 matrix;

vec2 texture_UV[4] = {
	vec2(0.0, 1.0),
	vec2(0.0, 0.0),
	vec2(1.0, 0.0),
	vec2(1.0, 1.0)
};

void main(void) {
	local_position = vertex_position;
	interpolated_tex_coords = vec3(texture_UV[int(texture_pointer[0])], texture_pointer[1]);
	interpolated_shading_value = shading_value;
	gl_Position = matrix * vec4(vertex_position, 1.0);
}