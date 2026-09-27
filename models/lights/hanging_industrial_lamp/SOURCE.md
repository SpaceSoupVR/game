# Hanging Industrial Lamp

- **Source:** Poly Haven — https://polyhaven.com/a/hanging_industrial_lamp
- **Licence:** CC0 1.0 (public domain). No attribution required; recorded here so
  provenance is not lost the next time someone asks whether we can ship it.
- **Downloaded:** 2026-09-03, glTF at 1k textures.

## Why this one

It carries an **emissive texture**, which is the property that matters: the
whole lamp is a single material with `emissiveFactor [1,1,1]`, and the texture
is black everywhere except the bulb. That is how a real fixture says which part
glows, and honouring only the factor lights the entire housing white -- a bug
this asset is what exposed.

## Geometry, measured from the glTF

- Hangs DOWNWARD from its origin: y from +0.015 (mount) to -1.340 (base).
- Glass/bulb primitive spans y -1.329 .. -1.037, so the emitter centre is
  about y = -1.18.
- Widest at 0.55 m across.

## Socket

`bulb`, at (0, -1.18, 0), rotated so its forward axis points straight DOWN.

A socket rather than a per-instance offset: where the bulb sits inside the
housing is a property of the MESH, so every placement of this lamp gets the
light in the right place with nothing typed per instance. The socket's forward
axis is what aims a spot -- see `space_soup_engine::scene_light::resolve_light_pose`.

## Intended light kind

**Spot**, pointing down. A caged pendant throws a cone at the floor; a Point
light here would light the ceiling it is hanging from through its own shade.
