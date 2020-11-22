#version 330

out vec4 fragment_colour;

uniform sampler2DArray texture_array_sampler;

in vec3 local_position;
in vec3 interpolated_tex_coords;
in float interpolated_shading_value;

void main(void) {
	fragment_colour = texture(texture_array_sampler, interpolated_tex_coords) * interpolated_shading_value;
}