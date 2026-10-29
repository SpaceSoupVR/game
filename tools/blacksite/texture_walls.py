#!/usr/bin/env python3
"""Give the blacksite room glbs a concrete texture.

The kit meshes carry only POSITION and NORMAL, so this box-projects a TEXCOORD_0 onto each vertex
(the world axis its normal points along picks the plane) and swaps the flat RoomWall colour for a
tiled base-colour image. Input is the flat-coloured copy in tools/blacksite/flat, so it can be re-run.

    python3 game/tools/blacksite/texture_walls.py [TILE_M]

TILE_M is how many metres one repeat of the image covers (default 2.5). The scene scales these
models by 0.36 (Y by 0.289 for HallwayTall_DoorType_A), which is undone here so tiles are square
in the world.
"""
import json, struct, sys
from array import array
from pathlib import Path

GAME = Path(__file__).resolve().parents[2]
ROOT = GAME.parent
SRC = GAME / "tools/blacksite/flat"
DST = GAME / "models/blacksite"
IMG = ROOT / "ssstudio/bake/models/third_party/polyhaven/concrete_wall_006.jpg"
METAL = ROOT / "ssstudio/bake/models/third_party/polyhaven/metal_plate_02.jpg"
METAL_TINT = [1.3, 1.36, 1.5]
TILE = float(sys.argv[1]) if len(sys.argv) > 1 else 2.5
SCALE = 0.36
# Poly Haven's photo is light and warm; this pulls it toward cooler, darker poured cement.
TINT = [0.78, 0.80, 0.84, 1.0]


def pad4(b, fill=b"\0"):
    return b + fill * (-len(b) % 4)


def tinted_image():
    """The renderer takes the image as is (baseColorFactor is ignored beside a texture), so the tint is baked in."""
    import io
    from PIL import Image
    im = Image.open(IMG).convert("RGB")
    r, g, b = (im.getchannel(i).point(lambda v, k=k: min(255, int(v * k))) for i, k in enumerate(TINT[:3]))
    out = io.BytesIO()
    Image.merge("RGB", (r, g, b)).save(out, "JPEG", quality=90)
    return out.getvalue()


def metal_image():
    """Gunmetal for the keycard scanners: the same steel plate as the doors, darker and cooler."""
    import io
    from PIL import Image
    im = Image.open(METAL).convert("RGB")
    r, g, b = (im.getchannel(i).point(lambda v, k=k: min(255, int(v * k))) for i, k in enumerate(METAL_TINT))
    out = io.BytesIO()
    Image.merge("RGB", (r, g, b)).save(out, "JPEG", quality=90)
    return out.getvalue()


def in_scanner(v, doorways):
    """Is this (scaled, metres) point inside a keycard scanner's box beside a doorway?
    The scanners are 1.0 x 0.4 x 0.12 m boxes on the wall face, 0.93-1.16 m to one side of the opening."""
    for dx, dz in doorways:
        a, d = (v[0] - dx, v[2] - dz) if abs(dz) > abs(dx) else (v[2] - dz, v[0] - dx)
        if 0.85 <= abs(a) <= 1.3 and 0.8 <= v[1] <= 1.55 and abs(d) <= 0.5:
            return True
    return False


def split_scanners(doc, binary, prim, mesh, doorways, sy, material):
    """Move the triangles inside a scanner box into their own primitive with `material`.
    Returns the binary chunk with the new index data appended."""
    acc = doc["accessors"][prim["indices"]]
    view = doc["bufferViews"][acc["bufferView"]]
    code, size = ("H", 2) if acc["componentType"] == 5123 else ("I", 4)
    idx = array(code)
    idx.frombytes(binary[view["byteOffset"]:view["byteOffset"] + acc["count"] * size])
    pacc = doc["accessors"][prim["attributes"]["POSITION"]]
    pview = doc["bufferViews"][pacc["bufferView"]]
    pos = array("f")
    pos.frombytes(binary[pview["byteOffset"]:pview["byteOffset"] + pacc["count"] * 12])
    inside = {}

    def at(i):
        if i not in inside:
            inside[i] = in_scanner((pos[3 * i] * SCALE, pos[3 * i + 1] * sy, pos[3 * i + 2] * SCALE), doorways)
        return inside[i]

    rest, scan = array(code), array(code)
    for t in range(0, len(idx), 3):
        tri = idx[t:t + 3]
        (scan if all(at(i) for i in tri) else rest).extend(tri)
    if not scan:
        return binary
    for target, indices in ((None, rest), (material, scan)):
        data = indices.tobytes()
        doc["bufferViews"].append({"buffer": 0, "byteOffset": len(binary), "byteLength": len(data), "target": 34963})
        binary += pad4(data)
        doc["accessors"].append({"bufferView": len(doc["bufferViews"]) - 1, "componentType": acc["componentType"], "count": len(indices), "type": "SCALAR"})
        if target is None:
            prim["indices"] = len(doc["accessors"]) - 1
        else:
            mesh["primitives"].append({**prim, "indices": len(doc["accessors"]) - 1, "material": target})
    print(f"  {len(scan) // 3} scanner triangles in metal")
    return binary


def convert(path):
    glb = path.read_bytes()
    jl = struct.unpack("<I", glb[12:16])[0]
    doc = json.loads(glb[20:20 + jl])
    binary = glb[20 + jl + 8:]
    sy = 0.28894516825675964 if path.name == "HallwayTall_DoorType_A.glb" else SCALE
    img = tinted_image()

    for mesh in doc["meshes"]:
        for prim in mesh["primitives"]:
            acc = doc["accessors"][prim["attributes"]["POSITION"]]
            nacc = doc["accessors"][prim["attributes"]["NORMAL"]]
            pv, nv = doc["bufferViews"][acc["bufferView"]], doc["bufferViews"][nacc["bufferView"]]
            pos = array("f"); pos.frombytes(binary[pv["byteOffset"]:pv["byteOffset"] + acc["count"] * 12])
            nrm = array("f"); nrm.frombytes(binary[nv["byteOffset"]:nv["byteOffset"] + nacc["count"] * 12])
            uv = array("f")
            for i in range(acc["count"]):
                x, y, z = pos[3 * i] * SCALE, pos[3 * i + 1] * sy, pos[3 * i + 2] * SCALE
                nx, ny, nz = abs(nrm[3 * i]), abs(nrm[3 * i + 1]), abs(nrm[3 * i + 2])
                if ny >= nx and ny >= nz:
                    u, v = x, z
                elif nx >= nz:
                    u, v = z, -y
                else:
                    u, v = x, -y
                uv.extend((u / TILE, v / TILE))
            data = uv.tobytes()
            doc["bufferViews"].append({"buffer": 0, "byteOffset": len(binary), "byteLength": len(data), "target": 34962})
            binary += pad4(data)
            doc["accessors"].append({"bufferView": len(doc["bufferViews"]) - 1, "componentType": 5126,
                                     "count": acc["count"], "type": "VEC2"})
            prim["attributes"]["TEXCOORD_0"] = len(doc["accessors"]) - 1

    doc["bufferViews"].append({"buffer": 0, "byteOffset": len(binary), "byteLength": len(img)})
    binary += pad4(img)
    metal = metal_image()
    doc["bufferViews"].append({"buffer": 0, "byteOffset": len(binary), "byteLength": len(metal)})
    binary += pad4(metal)
    doc["images"] = [
        {"bufferView": len(doc["bufferViews"]) - 2, "mimeType": "image/jpeg", "name": "concrete"},
        {"bufferView": len(doc["bufferViews"]) - 1, "mimeType": "image/jpeg", "name": "gunmetal"},
    ]
    doc["samplers"] = [{"magFilter": 9729, "minFilter": 9987, "wrapS": 10497, "wrapT": 10497}]
    doc["textures"] = [{"source": 0, "sampler": 0}, {"source": 1, "sampler": 0}]
    doorways = [(n["translation"][0] * SCALE, n["translation"][2] * SCALE) for n in doc["nodes"] if "Door" in n.get("name", "") and "translation" in n]
    doc["materials"].append({
        "name": "ScannerMetal", "doubleSided": True,
        "pbrMetallicRoughness": {"baseColorTexture": {"index": 1}, "baseColorFactor": [1, 1, 1, 1], "metallicFactor": 0.9, "roughnessFactor": 0.45},
    })
    scanner_material = len(doc["materials"]) - 1
    for mesh in doc["meshes"]:
        for prim in list(mesh["primitives"]):
            binary = split_scanners(doc, binary, prim, mesh, doorways, sy, scanner_material)
    for m in doc["materials"][:scanner_material]:
        pbr = m.setdefault("pbrMetallicRoughness", {})
        pbr["baseColorTexture"] = {"index": 0}
        pbr["baseColorFactor"] = [1.0, 1.0, 1.0, 1.0]
        pbr["roughnessFactor"] = 0.95
        pbr["metallicFactor"] = 0.0
    doc["buffers"][0]["byteLength"] = len(binary)

    js = pad4(json.dumps(doc, separators=(",", ":")).encode(), b" ")
    out = b"glTF" + struct.pack("<II", 2, 12 + 8 + len(js) + 8 + len(binary))
    out += struct.pack("<I", len(js)) + b"JSON" + js + struct.pack("<I", len(binary)) + b"BIN\0" + binary
    (DST / path.name).write_bytes(out)


for p in sorted(SRC.glob("*.glb")):
    if p.name.startswith("DoorType_A_NO_PATH"):
        continue
    convert(p)
    print("textured", p.name)
