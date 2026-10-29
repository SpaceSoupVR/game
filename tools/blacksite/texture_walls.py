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
    doc["images"] = [{"bufferView": len(doc["bufferViews"]) - 1, "mimeType": "image/jpeg", "name": "concrete"}]
    doc["samplers"] = [{"magFilter": 9729, "minFilter": 9987, "wrapS": 10497, "wrapT": 10497}]
    doc["textures"] = [{"source": 0, "sampler": 0}]
    for m in doc["materials"]:
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
