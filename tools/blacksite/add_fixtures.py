#!/usr/bin/env python3
"""Hang a caged industrial light on every ceiling lamp and a red lamp over every door that shines down.

    python3 game/tools/blacksite/add_fixtures.py [scene ...]     (default: blacksite_1..3)

Lights: models/lights/caged_light (Poly Haven, CC0) hangs by its chain from the lamp's old spot; the
lamp's light moves down into the cage and takes a sickly cold green, a little dimmer. The old white
cuboid is hidden. Door lamps: models/lights/red_lamp on both faces of each doorway's wall, a hand
above the lintel (the tall hallway's lintel is lower; the lamp follows it), and one red spot light
at the doorway pointing down, which lights the floor on both sides. Run fit_doors.py first; this
reads the leaves it placed. Safe to run again: it replaces its own objects.
"""
import json, math
from pathlib import Path

GAME = Path(__file__).resolve().parents[2]
TAG = "scary_fixture"
LIGHT_MESH = "models/lights/caged_light/caged_light.glb"
RED_MESH = "models/lights/red_lamp/red_lamp.glb"
CHAIN_ABOVE = 0.12   # the chain's top, over the lamp's old spot
BULB_DROP = 0.62     # from the chain's top down to the tubes
SLAB = 0.125         # half the wall slab where two pieces meet
RED_ABOVE_LINTEL = 0.2
SICK = [190, 215, 190, 255]
DIM = 0.85
RED_LIGHT = {"kind": "Spot", "mode": "Realtime", "color": [255, 24, 16, 255], "intensity": 40.0, "range": 6.5,
             "cone_angle_deg": 140.0, "inner_cone_angle_deg": 50.0, "enabled": True}


def quat(yaw):
    return [0.0, math.sin(yaw / 2), 0.0, math.cos(yaw / 2)]


def yaw_of(q):
    x, y, z, w = q
    return math.atan2(2 * (w * y + x * z), 1 - 2 * (y * y + z * z))


def mesh_object(oid, mesh, pos, yaw, half):
    return {
        "id": oid,
        "cuboid": {"position": pos, "half_size": half, "rotation": quat(yaw), "color": [40, 40, 44, 255]},
        "mesh": {"path": mesh, "scale": [1.0, 1.0, 1.0], "rotation_offset": [0.0, 0.0, 0.0, 1.0]},
        "tags": ["blacksite", TAG],
    }


def run(scene):
    path = GAME / "scenes" / f"{scene}.json"
    d = json.load(open(path))
    objs = [o for o in d["objects"] if TAG not in o.get("tags", [])]
    by_id = {o["id"]: o for o in objs}
    new = []

    # lights
    lamps = [o for o in objs if "lamp" in o.get("tags", []) and not o["id"].endswith(("_fill", "_low"))]
    for lamp in lamps:
        piece = by_id.get(lamp["id"].rsplit("/", 1)[0])
        yaw = yaw_of(piece["cuboid"]["rotation"]) if piece else 0.0
        group = [o for o in objs if o["id"] in (lamp["id"], lamp["id"] + "_fill")]
        top = lamp["cuboid"]["position"][1] + (0.0 if "hung" in lamp["tags"] else CHAIN_ABOVE)
        at = lamp["cuboid"]["position"]
        if "hung" not in lamp["tags"]:
            for o in group:
                o["cuboid"]["position"][1] = top - BULB_DROP
                o["tags"].append("hung")
                for light in o.get("lights", []):
                    light["color"] = SICK
                    light["intensity"] = round(light["intensity"] * DIM, 1)
            lamp["hidden"] = True
        new.append(mesh_object(lamp["id"] + "_fixture", LIGHT_MESH, [at[0], top, at[2]], yaw, [0.58, 0.375, 0.16]))

    # red lamps over the doors
    for oid, left in by_id.items():
        if not (oid.startswith("door_") and oid.endswith("_l")):
            continue
        right = by_id[oid[:-2] + "_r"]
        lp, rp = left["cuboid"]["position"], right["cuboid"]["position"]
        mx, mz = (lp[0] + rp[0]) / 2, (lp[2] + rp[2]) / 2
        ax, az = rp[0] - lp[0], rp[2] - lp[2]
        n = math.hypot(ax, az)
        fx, fz = -az / n, ax / n
        lintel = lp[1] + left["cuboid"]["half_size"][1] + 0.03  # fit_doors leaves 3 cm under it
        y = lintel + RED_ABOVE_LINTEL
        yaw = math.atan2(fx, fz)
        for side, tag in ((1, "a"), (-1, "b")):
            new.append(mesh_object(f"{oid[:-2]}_red_{tag}", RED_MESH, [mx + fx * SLAB * side, y, mz + fz * SLAB * side], yaw + (0 if side > 0 else math.pi), [0.13, 0.07, 0.1]))
        new.append({
            "id": f"{oid[:-2]}_redlight",
            "cuboid": {"position": [mx, y - 0.1, mz], "half_size": [0.01, 0.01, 0.01], "rotation": [-0.7071068, 0.0, 0.0, 0.7071068], "color": [0, 0, 0, 0]},
            "hidden": True,
            "lights": [dict(RED_LIGHT)],
            "tags": ["blacksite", TAG],
        })

    d["objects"] = objs + new
    json.dump(d, open(path, "w"), indent=2)
    print(f"{scene}: {len(lamps)} lights hung, {sum(o['id'].endswith('_redlight') for o in new)} red door lamps")


import sys
for s in sys.argv[1:] or ["blacksite_1", "blacksite_2", "blacksite_3"]:
    run(s)
