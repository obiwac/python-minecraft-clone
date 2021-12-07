#version 330

out vec4 fragment_colour;

uniform sampler2DArray texture_array_sampler;

in vec3 local_position;
in vec3 interpolated_tex_coords;
in float interpolated_shading_value;

void main(void) {
	vec4 texture_colour = texture(texture_array_sampler, interpolated_tex_coords);
	if (texture_colour.a < 0.5) { // discard if texel's alpha component is 0 (texel is transparent)
		discard;
	}
	fragment_colour = texture_colour * interpolated_shading_value;
}