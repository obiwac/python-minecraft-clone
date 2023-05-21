#version 330

out vec4 fragment_colour;

uniform sampler2D texture_sampler;

in vec3 local_position;
in vec2 interpolated_tex_coords;
in float shading;

void main(void) {
	vec4 texture_colour = texture(texture_sampler, interpolated_tex_coords);
	fragment_colour = texture_colour * shading;

	if (texture_colour.a == 0.0) { // discard if texel's alpha component is 0 (texel is transparent)
		discard;
	}
}
