#version 330

layout(location = 0) in vec3 vertex_position;
layout(location = 1) in vec3 normal;
layout(location = 2) in vec3 tex_coords;

out vec3 local_position;
out vec3 interpolated_tex_coords;
out float shading;

uniform mat4 inverse_transform_matrix;
uniform mat4 matrix;
uniform float lighting;

void main(void) {
	local_position = vertex_position;

	interpolated_tex_coords = tex_coords;

	vec3 transformed_normal = (vec4(normal, 1.0) * inverse_transform_matrix).xyz;
	vec3 sunlight = vec3(0.0, 2.0, 1.0);

	vec3 xz_absolute_normal = vec3(abs(transformed_normal.x), transformed_normal.y, abs(transformed_normal.z));
	float facing = dot(normalize(xz_absolute_normal), normalize(sunlight));

	shading = max(0.4, (1. + facing) / 2) * lighting;

	gl_Position = matrix * vec4(vertex_position, 1.0);
}
