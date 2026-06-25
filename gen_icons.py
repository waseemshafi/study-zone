#!/usr/bin/env python3
"""Generate PWA icons (pure standard library, no Pillow needed)."""
import zlib, struct, math, os

C1 = (124, 92, 255)   # #7c5cff
C2 = (255, 110, 199)  # #ff6ec7
GOLD = (255, 207, 63) # #ffcf3f

def write_png(path, w, h, rgba):
    def chunk(typ, data):
        return (struct.pack(">I", len(data)) + typ + data +
                struct.pack(">I", zlib.crc32(typ + data) & 0xffffffff))
    raw = bytearray()
    for y in range(h):
        raw.append(0)
        raw += rgba[y * w * 4:(y + 1) * w * 4]
    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n")
        f.write(chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0)))
        f.write(chunk(b"IDAT", zlib.compress(bytes(raw), 9)))
        f.write(chunk(b"IEND", b""))

def star_points(cx, cy, R, rot=-math.pi/2, ratio=0.42):
    pts = []
    for i in range(10):
        ang = rot + i * math.pi / 5
        rr = R if i % 2 == 0 else R * ratio
        pts.append((cx + rr * math.cos(ang), cy + rr * math.sin(ang)))
    return pts

def in_poly(px, py, poly):
    inside = False
    n = len(poly)
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if ((yi > py) != (yj > py)) and (px < (xj - xi) * (py - yi) / (yj - yi) + xi):
            inside = not inside
        j = i
    return inside

def make(size, star_scale, path, transparent_bg=False):
    SS = 3                      # supersample for smooth edges
    W = H = size * SS
    cx = cy = W / 2.0
    Rout = (W * 0.5) * star_scale
    white_star = star_points(cx, cy, Rout)
    gold_star = star_points(cx, cy, Rout * 0.88)
    # bounding box for star tests
    minx = int(min(p[0] for p in white_star)) - 2
    maxx = int(max(p[0] for p in white_star)) + 2
    miny = int(min(p[1] for p in white_star)) - 2
    maxy = int(max(p[1] for p in white_star)) + 2
    # sparkles (little diamonds)
    sparkles = [(W*0.78, H*0.26, W*0.05), (W*0.24, H*0.74, W*0.038)]
    buf = bytearray(W * H * 4)
    for y in range(H):
        for x in range(W):
            i = (y * W + x) * 4
            # background gradient
            t = (x + y) / (2.0 * W)
            r = int(C1[0] + (C2[0] - C1[0]) * t)
            g = int(C1[1] + (C2[1] - C1[1]) * t)
            b = int(C1[2] + (C2[2] - C1[2]) * t)
            a = 255
            if transparent_bg:
                a = 0
            # sparkles
            for sx, sy, sr in sparkles:
                if abs(x - sx) / sr + abs(y - sy) / sr < 1:
                    r, g, b, a = 255, 255, 255, 255
            # star
            if minx <= x <= maxx and miny <= y <= maxy:
                if in_poly(x, y, white_star):
                    r, g, b, a = 255, 255, 255, 255
                if in_poly(x, y, gold_star):
                    r, g, b, a = GOLD[0], GOLD[1], GOLD[2], 255
            buf[i] = r; buf[i+1] = g; buf[i+2] = b; buf[i+3] = a
    # downsample SSxSS -> size
    out = bytearray(size * size * 4)
    for y in range(size):
        for x in range(size):
            ar = ag = ab = aa = 0
            for dy in range(SS):
                for dx in range(SS):
                    j = ((y*SS+dy) * W + (x*SS+dx)) * 4
                    ar += buf[j]; ag += buf[j+1]; ab += buf[j+2]; aa += buf[j+3]
            n = SS*SS
            k = (y*size + x)*4
            out[k] = ar//n; out[k+1] = ag//n; out[k+2] = ab//n; out[k+3] = aa//n
    write_png(path, size, size, out)
    print("wrote", path)

here = os.path.dirname(os.path.abspath(__file__))
make(512, 0.78, os.path.join(here, "icon-512.png"))
make(192, 0.78, os.path.join(here, "icon-192.png"))
make(512, 0.62, os.path.join(here, "icon-maskable.png"))  # extra padding for safe zone
make(180, 0.78, os.path.join(here, "apple-touch-icon.png"))
print("done")
