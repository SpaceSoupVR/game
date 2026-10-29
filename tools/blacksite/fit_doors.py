#!/usr/bin/env python3
"""Fit every sliding door in the blacksite scenes to its own doorway.

The kit's doorways are not all the same size: measured off the room models, the opening is 1.78 m
between the jambs under a lintel at 2.69 m, except the tall hallway (squashed to 0.8026 in Y, so
its lintel is at 2.16 m) and LIGHT_TEST_3WayTall (1.58 m between the jambs). A leaf is stretched to
its doorway: half the opening plus 4 cm into the wall, from 2 cm off the floor to 3 cm under the
lintel, and it slides its own width plus 1 cm into the wall.

    python3 game/tools/blacksite/fit_doors.py [scene ...]     (default: blacksite_1..3)

The two leaves of a doorway are told apart by id (door_NNN_l / door_NNN_r); the doorway is where
they meet. Safe to run again.
"""
import json, math, os, sys
from pathlib import Path

GAME = Path(__file__).resolve().parents[2]
PIECES = GAME.parent / "space_soup_engine/space_soup_nav/tests/data/meshes/blacksite/pieces.json"
# (half opening between the jambs, lintel height) by kit piece; anything else is the standard one.
STANDARD = (0.89, 2.69)
OPENINGS = {"HallwayTall_DoorType_A": (0.89, 2.16), "LIGHT_TEST_3WayTall_DoorType_A": (0.79, 2.69)}
MESH_W, MESH_H = 0.92, 2.55  # what slide_door_{left,right}.glb is modelled at
THICK = 0.025  # half the leaf's collider depth
WALL_LAP, FLOOR_GAP, LINTEL_GAP, EXTRA_TRAVEL = 0.04, 0.02, 0.03, 0.01

kit = {p["piece"]: p for p in json.load(open(PIECES))["pieces"]}


def yaw_of(q):
    x, y, z, w = q
    return math.atan2(2 * (w * y + x * z), 1 - 2 * (y * y + z * z))


def rot_y(yaw, v):
    c, s = math.cos(yaw), math.sin(yaw)
    return [c * v[0] + s * v[2], v[1], -s * v[0] + c * v[2]]


def kit_name(o):
    return os.path.splitext(os.path.basename(o["mesh"]["path"]))[0]


def fit(scene):
    path = GAME / "scenes" / f"{scene}.json"
    d = json.load(open(path))
    objs = d["objects"]
    pieces = [o for o in objs if o.get("mesh") and "blacksite" in o.get("tags", []) and "lamp" not in o.get("tags", []) and "door" not in o.get("tags", []) and kit_name(o) in kit]
    ways = []  # (x, z, kit name) of every doorway of every piece
    for o in pieces:
        yaw = yaw_of(o["cuboid"]["rotation"])
        for w in kit[kit_name(o)]["doorways"]:
            p = rot_y(yaw, w["position"])
            ways.append((o["cuboid"]["position"][0] + p[0], o["cuboid"]["position"][2] + p[2], kit_name(o), o["cuboid"]["position"][1] + p[1]))
    by_id = {o["id"]: o for o in objs}
    fitted = 0
    for oid, left in by_id.items():
        if not (oid.startswith("door_") and oid.endswith("_l")):
            continue
        right = by_id[oid[:-2] + "_r"]
        lp, rp = left["cuboid"]["position"], right["cuboid"]["position"]
        mx, mz = (lp[0] + rp[0]) / 2, (lp[2] + rp[2]) / 2
        owners = {n for x, z, n, _ in ways if (x - mx) ** 2 + (z - mz) ** 2 < 0.6 ** 2}
        floor = min((y for x, z, n, y in ways if (x - mx) ** 2 + (z - mz) ** 2 < 0.6 ** 2), default=lp[1] - 1.305)
        half = min(o[0] for o in (OPENINGS.get(n, STANDARD) for n in owners)) if owners else STANDARD[0]
        lintel = min(o[1] for o in (OPENINGS.get(n, STANDARD) for n in owners)) if owners else STANDARD[1]
        w = half + WALL_LAP
        h = lintel - LINTEL_GAP - FLOOR_GAP
        ax, az = rp[0] - lp[0], rp[2] - lp[2]
        n = math.hypot(ax, az)
        ax, az = ax / n, az / n
        for leaf, side in ((left, -1), (right, 1)):
            leaf["cuboid"]["position"] = [mx + ax * side * w / 2, floor + FLOOR_GAP + h / 2, mz + az * side * w / 2]
            leaf["cuboid"]["half_size"] = [w / 2, h / 2, THICK]
            leaf["mesh"]["scale"] = [w / MESH_W, h / MESH_H, 1.0]
            leaf["door"]["slide_m"] = side * (w + EXTRA_TRAVEL)
        fitted += 1
    json.dump(d, open(path, "w"), indent=2)
    print(f"{scene}: fitted {fitted} doorways")


for s in sys.argv[1:] or ["blacksite_1", "blacksite_2", "blacksite_3"]:
    fit(s)
