# Train library

Models the Train tab's Scatter tool places over terrain. One folder per kind:

    trees/  bushes/  rocks/  grass/

Drop a `.glb` in a folder and it is used the next time you paint (press
"Refresh library" in the Scatter panel). Model origin = where it sits on the
ground: base of the trunk at (0, 0, 0), y up, real-world metres.

Optional `index.json` in a folder tunes each model (anything not listed gets
weight 1, scale 0.9-1.1, max slope 30 degrees):

    { "models": [ { "file": "oak_big_1.glb", "weight": 2, "scale": [0.9, 1.1], "max_slope": 30 } ] }

`weight` is how often it is picked relative to the others; `max_slope` is
the steepest ground (degrees) it will stand on.

trees/ holds the 17 oaks from the "oak trees pack" (LOD1 of each, split out
of the original pack; it also has LOD0/LOD2, billboards and season
materials if more detail is ever wanted).
