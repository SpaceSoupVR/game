# Terrain layer textures

A colour map and a normal map per material layer, named by the ROLE the shader
gives the layer rather than by what it depicts. Replacing what "rock" looks like
is a file swap and touches no code. The slots are fixed and not rearrangeable:

| Colour | Normal | Layer |
|---|---|---|
| `ground.jpg`   | `ground_n.jpg`   | 0 — ground |
| `rock.jpg`     | `rock_n.jpg`     | 1 — rock |
| `high.jpg`     | `high_n.jpg`     | 2 — high ground |
| `sediment.jpg` | `sediment_n.jpg` | 3 — sediment |

Normal maps are **OpenGL convention** (`NormalGL`, green is +Y). ambientCG ships
both; a DirectX map loads without complaint and lights every bump from the
opposite side, which reads as "the lighting is wrong" rather than "the wrong
file is installed". A missing normal map is fine — that layer simply lights as
though it were smooth.

**`sources.json` records where each one came from** and is written by the
installer. It is the authority; this file deliberately does not repeat its
contents, because a hand-maintained copy of generated data goes stale and then
misinforms every future reader.

## Licence

All from <https://ambientcg.com> under **Creative Commons CC0 1.0 Universal** —
commercial use permitted without restriction, attribution not required. The
provenance record exists for our own traceability, not because the licence asks
for it. See <https://docs.ambientcg.com/license/>.

## Why only these, and only colour

A starter set is committed so the engine renders properly out of the box, and
because the deploy pushes `game/` to the headset wholesale — a texture the
headset cannot see is not a texture. It is deliberately small:

- **Colour and normal only.** The shader reads those two. Roughness, ambient
  occlusion and displacement would be megabytes of files nothing looks at.
- **1K, not 2K or 4K.** These tile across a whole map and the Quest is not a
  fast machine.

That keeps all eight files around 2.2MB. Going further does not scale: a full
PBR set at 2K is 40MB+, git keeps every version of a binary forever, and
replacing one texture doubles its cost in history.

## Installing or replacing one

Use the editor: **Material panel → Texture for "<layer>"** → search → Install.
It fetches from ambientCG, keeps the colour map, recompresses it, and updates
`sources.json`. Restart the headset app to see the change.

Or drop a 1024x1024 image over the file by hand — keep the filename, nothing
references the ambientCG ids.

## Getting the other maps later

Roughness, ambient occlusion and displacement are in the originals if the shader
ever grows to read them:

```
curl -L -o Rock063.zip "https://ambientcg.com/get?file=Rock063_1K-JPG.zip"
```

Swap the asset id — `sources.json` has the ids for what is installed.
