#version 330

out vec4 fragment_colour;

in vec3 local_position;

void main(void) {
	fragment_colour = vec4(local_position / 2.0 + 0.5, 1.0);
}