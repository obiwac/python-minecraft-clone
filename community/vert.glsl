#version 330

#define CHUNK_WIDTH 16
#define CHUNK_LENGTH 16

uniform ivec2 u_ChunkPosition;
uniform mat4 u_ModelViewProjMatrix;
uniform float u_Daylight;

layout(location = 0) in vec3 a_LocalPosition;
layout(location = 1) in float a_TextureFetcher;
layout(location = 2) in float a_Shading;
layout(location = 3) in float a_Light;

out vec3 v_Position;
out vec3 v_TexCoords;
out float v_Shading;
out float v_Light;

const vec2 texture_UV[4] = vec2[4](
	vec2(0.0, 1.0),
	vec2(0.0, 0.0),
	vec2(1.0, 0.0),
	vec2(1.0, 1.0)
);

void main(void) {
	v_Position = vec3(u_ChunkPosition.x * CHUNK_WIDTH + a_LocalPosition.x, 
						a_LocalPosition.y, 
						u_ChunkPosition.y * CHUNK_LENGTH + a_LocalPosition.z);
	v_TexCoords = vec3(texture_UV[int(a_TextureFetcher) % 4], int(a_TextureFetcher) / 4);
	v_Shading = a_Shading;
	v_Light = max(int(a_Light) & 15, (int(a_Light) >> 4) * u_Daylight); // First one is Blocklight, Second one is Skylight
	gl_Position = u_ModelViewProjMatrix * vec4(v_Position, 1.0);
}