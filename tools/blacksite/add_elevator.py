#!/usr/bin/env python3
"""Build the start room's elevator in the blacksite scenes: a car that runs up to the catwalk.

    python3 game/tools/blacksite/add_elevator.py [scene ...]     (default: blacksite_1..3)

All in the start piece's own coordinates (models/elevator/*.glb, ssstudio/bake/models/elevator_parts.py):
the shaft and its portal wall against the catwalk's end wall, a car that is a kinematic slider whose
rail runs up (its `door.elevator` carries the floors, the landing doors and the buttons, and the
engine's `run_elevators` does the rest), landing doors that are ordinary sliders, and the buttons,
invisible objects at the lit button positions. Safe to run again: it replaces its own objects.
"""
import json, math, sys
from pathlib import Path

GAME = Path(__file__).resolve().parents[2]
TAG = "elevator"
FLOORS = [0.0, 3.61]                 # the car's floor height at each stop: the room's floor, the catwalk's
CAB = (-3.95, 7.30)                  # the car's middle, x and z, in piece coordinates
PORTAL_Z = 6.20                      # the middle of the wall the landing doors are in
DOOR_X = -3.95
LEAF_W, LEAF_H, LEAF_T = 0.75, 2.40, 0.025
MESH_W, MESH_H = 0.92, 2.55
PANEL_X = -2.70
INVISIBLE = {"color": [0, 0, 0, 0], "style": "Wireframe", "wire_color": [0, 0, 0, 0]}
# The shaft's solid parts: x0, x1, y0, y1, z0, z1, as elevator_parts.py builds them.
TOP = 6.70
SOLIDS = {
    "pier_l": (-5.70, -4.70, 0.0, TOP, 6.10, 6.30),
    "pier_r": (-3.20, -2.20, 0.0, TOP, 6.10, 6.30),
    "mid": (-4.70, -3.20, 2.40, 3.61, 6.10, 6.30),
    "head": (-4.70, -3.20, 6.01, TOP, 6.10, 6.30),
    "wall_l": (-5.07, -4.95, 0.0, TOP, 6.30, 8.42),
    "wall_r": (-2.95, -2.83, 0.0, TOP, 6.30, 8.42),
    "back": (-5.07, -2.83, 0.0, TOP, 8.30, 8.42),
}


def qmul(a, b):
    ax, ay, az, aw = a
    bx, by, bz, bw = b
    return [aw * bx + ax * bw + ay * bz - az * by, aw * by - ax * bz + ay * bw + az * bx,
            aw * bz + ax * by - ay * bx + az * bw, aw * bw - ax * bx - ay * by - az * bz]


def quat_y(t):
    return [0.0, math.sin(t / 2), 0.0, math.cos(t / 2)]


def quat_z(t):
    return [0.0, 0.0, math.sin(t / 2), math.cos(t / 2)]


def yaw_of(q):
    x, y, z, w = q
    return math.atan2(2 * (w * y + x * z), 1 - 2 * (y * y + z * z))


def run(scene):
    path = GAME / "scenes" / f"{scene}.json"
    d = json.load(open(path))
    objs = [o for o in d["objects"] if TAG not in o.get("tags", [])]
    start = next(o for o in objs if "start" in o.get("tags", []) and o.get("mesh"))
    origin, yaw = start["cuboid"]["position"], yaw_of(start["cuboid"]["rotation"])
    c, s = math.cos(yaw), math.sin(yaw)

    def world(x, y, z):
        return [origin[0] + c * x + s * z, origin[1] + y, origin[2] - s * x + c * z]

    new = []

    def add(oid, pos, rot, half, extra=None, style=None):
        o = {"id": oid, "cuboid": {"position": pos, "half_size": half, "rotation": rot, **(style or INVISIBLE)}, "tags": ["blacksite", TAG]}
        o.update(extra or {})
        new.append(o)

    def mesh(path, rot=(0, 0, 0, 1), scale=(1.0, 1.0, 1.0)):
        return {"mesh": {"path": path, "scale": list(scale), "rotation_offset": list(rot)}}

    yawq = quat_y(yaw)
    add("elev_shaft", world(0, 0, 0), yawq, [6.0, 4.0, 9.0], mesh("models/elevator/shaft.glb"))
    for name, (x0, x1, y0, y1, z0, z1) in SOLIDS.items():
        add(f"elev_{name}", world((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), yawq, [(x1 - x0) / 2, (y1 - y0) / 2, (z1 - z0) / 2], {"rigid_body": {"mode": "Static"}})

    # the landing doors: ordinary sliders, opened and shut by the elevator
    f = [-s, 0.0, -c]                           # facing -z in piece coordinates, turned by the piece
    across = [f[2], 0.0, -f[0]]
    leaf_yaw = math.atan2(f[0], f[2])
    doors = []
    for fl, base in enumerate(FLOORS):
        pair = []
        for side, name in ((-1, "l"), (1, "r")):
            mid = world(DOOR_X, base + 0.02 + LEAF_H / 2, PORTAL_Z)
            pos = [mid[0] + across[0] * side * LEAF_W / 2, mid[1], mid[2] + across[2] * side * LEAF_W / 2]
            oid = f"elev_d{fl}_{name}"
            pair.append(oid)
            add(oid, pos, quat_y(leaf_yaw), [LEAF_W / 2, LEAF_H / 2, LEAF_T],
                {**mesh(f"models/doors/slide_door_{'left' if side < 0 else 'right'}.glb", scale=(LEAF_W / MESH_W, LEAF_H / MESH_H, 1.0)),
                 "door": {"slide_m": side * (LEAF_W + 0.01), "mass": 60.0}},
                {"color": [60, 60, 66, 255]})
        doors.append(pair)

    # the buttons: a point each, where the panel's lit button is
    buttons = []

    def button(oid, pos, **kw):
        add(oid, pos, [0, 0, 0, 1], [0.03, 0.03, 0.03])
        buttons.append({"object": oid, **kw})

    for fl, base in enumerate(FLOORS):
        add(f"elev_panel_{fl}", world(PANEL_X, base + 1.12, PORTAL_Z - 0.1 + 0.0175), quat_y(yaw + math.pi), [0.08, 0.2, 0.0175], mesh("models/elevator/panel.glb"))
        button(f"elev_btn_f{fl}_up", world(PANEL_X, base + 1.20, 6.06), floor=fl)
        button(f"elev_btn_f{fl}_down", world(PANEL_X, base + 1.04, 6.06), floor=fl)
    button("elev_btn_cab_up", world(CAB[0] + 0.90, 1.20, CAB[1] + 0.35), step=1, rides=True)
    button("elev_btn_cab_down", world(CAB[0] + 0.90, 1.04, CAB[1] + 0.35), step=-1, rides=True)

    # the car: a floor slab on a rail that runs up (turned a quarter about z), the shell its model
    add("elev_cab", world(CAB[0], -0.05, CAB[1]), qmul(yawq, quat_z(math.pi / 2)), [0.05, 0.98, 0.98],
        {**mesh("models/elevator/cab.glb", rot=quat_z(-math.pi / 2)),
         "door": {"slide_m": FLOORS[1], "mass": 500.0,
                  "elevator": {"floors": FLOORS, "doors": doors, "buttons": buttons, "speed_m_s": 1.4, "door_speed_m_s": 1.1, "press_m": 0.14}},
         "lights": [{"kind": "Point", "mode": "Realtime", "color": [255, 226, 180, 255], "intensity": 14.0, "range": 4.5, "enabled": True}]},
        {"color": [40, 40, 44, 255], "style": "Solid", "wire_color": [0, 0, 0, 0]})

    d["objects"] = objs + new
    json.dump(d, open(path, "w"), indent=2)
    print(f"{scene}: elevator at {world(CAB[0], 0, CAB[1])}, {len(new)} objects")


for sc in sys.argv[1:] or ["blacksite_1", "blacksite_2", "blacksite_3"]:
    run(sc)
