#version 330

layout(location = 0) in vec3 a_Position;
layout(location = 1) in vec2 a_TextureFetcher;
layout(location = 2) in float a_LightMultiplier;


out vec3 v_Position;
out vec3 v_TexCoords;
out float v_LightMultiplier;

uniform mat4 u_ModelViewProjMatrix;

const vec2 texture_UV[4] = vec2[4](
	vec2(0.0, 1.0),
	vec2(0.0, 0.0),
	vec2(1.0, 0.0),
	vec2(1.0, 1.0)
);

void main(void) {
	v_Position = a_Position;
	v_TexCoords = vec3(texture_UV[int(a_TextureFetcher[0])], a_TextureFetcher[1]);
	v_LightMultiplier = a_LightMultiplier;
	gl_Position = u_ModelViewProjMatrix * vec4(a_Position, 1.0);
}