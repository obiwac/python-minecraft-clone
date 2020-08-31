#version 330

out vec4 fragment_colour;

uniform sampler2DArray texture_array_sampler; // create our texture array sampler uniform

in vec3 local_position;
in vec3 interpolated_tex_coords; // interpolated texture coordinates

void main(void) {
	fragment_colour = texture(texture_array_sampler, interpolated_tex_coords); // sample our texture array with the interpolated texture coordinates
}