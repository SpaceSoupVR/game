# Industrial Wall Sconce

- **Source:** Poly Haven — https://polyhaven.com/a/industrial_wall_sconce (by Ulan Cabanilla)
- **Licence:** CC0 1.0 (public domain). No attribution required; recorded for provenance.
- **Downloaded:** 2026-09-24, glTF at 1k textures, through the editor's model library.

## Changed from the download

The bulb material (`industrial_wall_sconce_bulb`) ships with NO emissive, so the
engine would draw the glass dark however bright the light is. It now carries
`emissiveFactor [1.0, 0.86, 0.62]` -- a warm tungsten white -- which the renderer
drives by the light's intensity (`scene_light::emissive_drive`). Nothing else
was edited.

## Geometry, measured from the glTF

- Mounts on a wall at its BACK PLATE: z from -0.001 (wall) to +0.25 (front).
  The fixture projects along +Z, so rotate the object so +Z points out of the wall.
- 0.15 m wide, 0.34 m tall, the node sits 0.151 m above the origin.
- Bulb primitive spans x -0.033..0.029, y 0.057..0.157, z 0.161..0.222 in
  model space, so the emitter centre is about (0, 0.107, 0.19).

## Socket

`bulb` at (0, 0.107, 0.19), unrotated.

## Intended light kind

**Point.** An open sconce throws light up the wall, down the wall and into the
room; a spot would leave the wall above it dark, which reads as a light with no
source.
