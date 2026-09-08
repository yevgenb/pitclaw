#!/usr/bin/env python3
"""Render actual STL triangles with a CPU depth buffer; no OpenGL required.

Requires numpy, trimesh and Pillow. Electronics are omitted except for the
explicitly labeled nominal display glass witness in the assembled preview.
This creates review images, not slicer toolpaths.
"""
from pathlib import Path
import hashlib
import json
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import trimesh

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'enclosure/print/carrier-r7'
BG = (245, 247, 249)
INK = '#243441'
ORANGE = (229, 134, 51)
GREY = (106, 125, 143)
PALE = (191, 201, 201)


def font(size):
    for p in ('/System/Library/Fonts/Supplemental/Arial.ttf',
              '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'):
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default(size=size)


def mesh(name):
    return trimesh.load(OUT / name, force='mesh', process=False)


def top_assembled():
    m = mesh('carrier-top.stl')
    # Inverse of the source's face-down print transform.
    m.vertices *= [1, -1, -1]
    m.vertices += [0, 0, 44.9]
    return m


def rotated(scene):
    result = []
    for m, color in scene:
        m = m.copy()
        m.vertices = m.vertices[:, [1, 0, 2]] * [-1, 1, 1]
        result.append((m, color))
    return result


def render(scene, size, eye):
    w, h = size
    forward = np.asarray(eye, dtype=float)
    forward /= np.linalg.norm(forward)
    right = np.cross([0, 0, 1], forward)
    right /= np.linalg.norm(right)
    up = np.cross(forward, right)
    basis = np.array([right, up, forward])
    projected = [m.vertices @ basis.T for m, _ in scene]
    all_xy = np.vstack(projected)[:, :2]
    lo, hi = all_xy.min(axis=0), all_xy.max(axis=0)
    center = (lo + hi) / 2
    scale = min((w - 60) / (hi[0] - lo[0]), (h - 50) / (hi[1] - lo[1]))
    pixels = np.full((h, w, 3), BG, dtype=np.uint8)
    depth = np.full((h, w), -np.inf)
    light = np.array([-0.4, -0.3, 0.85])
    light /= np.linalg.norm(light)
    for (m, color), p in zip(scene, projected):
        vertices = p.copy()
        vertices[:, 0] = (p[:, 0] - center[0]) * scale + w / 2
        vertices[:, 1] = -(p[:, 1] - center[1]) * scale + h / 2
        for ids in m.faces:
            a, b, c = vertices[ids]
            determinant = (b[1]-c[1])*(a[0]-c[0]) + (c[0]-b[0])*(a[1]-c[1])
            if abs(determinant) < 1e-8:
                continue
            x0 = max(0, int(np.floor(min(a[0], b[0], c[0]))))
            x1 = min(w-1, int(np.ceil(max(a[0], b[0], c[0]))))
            y0 = max(0, int(np.floor(min(a[1], b[1], c[1]))))
            y1 = min(h-1, int(np.ceil(max(a[1], b[1], c[1]))))
            if x1 < x0 or y1 < y0:
                continue
            ys, xs = np.mgrid[y0:y1+1, x0:x1+1].astype(float)
            xs += 0.5
            ys += 0.5
            u = ((b[1]-c[1])*(xs-c[0]) + (c[0]-b[0])*(ys-c[1])) / determinant
            v = ((c[1]-a[1])*(xs-c[0]) + (a[0]-c[0])*(ys-c[1])) / determinant
            t = 1-u-v
            z = u*a[2] + v*b[2] + t*c[2]
            old = depth[y0:y1+1, x0:x1+1]
            mask = (u >= -1e-8) & (v >= -1e-8) & (t >= -1e-8) & (z > old)
            if not mask.any():
                continue
            normal = np.cross(p[ids[1]]-p[ids[0]], p[ids[2]]-p[ids[0]])
            normal /= max(np.linalg.norm(normal), 1e-12)
            if normal[2] < 0:
                normal *= -1
            shade = 0.56 + 0.44 * max(float(normal @ light), 0)
            pixels[y0:y1+1, x0:x1+1][mask] = np.clip(np.array(color)*shade, 0, 255)
            old[mask] = z[mask]
    return Image.fromarray(pixels)


def titled(scene, name, subtitle, filename, eye=(-1, -1.4, 1.4)):
    canvas = Image.new('RGB', (1500, 1100), BG)
    canvas.paste(render(scene, (1460, 885), eye), (20, 135))
    d = ImageDraw.Draw(canvas)
    d.text((50, 35), name, font=font(42), fill=INK)
    d.text((52, 90), subtitle, font=font(24), fill=INK)
    d.text((52, 1048), 'CAD fit prototype • r7 • dimensions in mm • physical fit pending', font=font(22), fill=INK)
    canvas.save(OUT / filename)


def main():
    bottom = mesh('carrier-bottom.stl')
    top = top_assembled()
    retainer = mesh('carrier-retainer.stl')
    retainer.apply_translation([0, 0, 30.1])
    glass = trimesh.creation.box([60, 92, 1.45])
    glass.apply_translation([0, 0, 43.4-1.45/2])
    active = trimesh.creation.box([49.56, 74.04, 0.03])
    active.apply_translation([0, 0, 43.415])
    assembled = [(bottom, GREY), (top, ORANGE), (retainer, PALE),
                 (glass, (44, 55, 64)), (active, (42, 105, 134))]
    titled(rotated(assembled), 'PitClaw • landscape carrier case',
           '104 × 86 × 44.9   |   Actual shell STLs; nominal display glass witness', 'preview-assembled.png')
    upper = top.copy()
    upper.apply_translation([0, 0, 40])
    ring = retainer.copy()
    ring.apply_translation([0, 0, 18])
    titled(rotated([(bottom, GREY), (ring, PALE), (upper, ORANGE)]),
           'Two outer halves + internal display retainer',
           'Actual STL meshes in exploded assembly positions; electronics omitted', 'preview-exploded.png')
    titled([(mesh('fit-coupon.stl'), GREY)], 'Power-end coupon • separate fitted openings',
           'RJ45 16.75 × 14.51   |   Barrel 10 × 12.1   |   USB recess 20 × 10 × 2',
           'preview-power-face.png', eye=(0.22, 1, 0.12))
    canvas = Image.new('RGB', (1500, 1110), BG)
    d = ImageDraw.Draw(canvas)
    d.text((40, 30), 'Print files • 0.4 mm nozzle', font=font(40), fill=INK)
    d.text((42, 87), 'All five STLs start at Z = 0. Print the two coupons before the full case.', font=font(23), fill=INK)
    cards = [
        ('carrier-top.stl', 'Top • face down', '86 × 104 × 19.3', ORANGE),
        ('carrier-bottom.stl', 'Bottom • open side up', '86 × 104 × 27.6', GREY),
        ('carrier-retainer.stl', 'Internal retainer • flat', '80 × 96 × 2.5', PALE),
        ('fit-coupon.stl', 'Power-end fit coupon', '86 × 22 × 27.6', GREY),
        ('insert-coupon.stl', 'M3 insert coupon', '4.0 / 4.1 / 4.2 mm pilots', ORANGE),
    ]
    for i, (filename, title, dimension, color) in enumerate(cards):
        x, y = 25+(i%3)*490, 145+(i//3)*450
        canvas.paste(render([(mesh(filename), color)], (470, 325), (1, 1, 1.4)), (x, y+58))
        d.text((x+12, y), title, font=font(24), fill=INK)
        d.text((x+12, y+34), dimension, font=font(21), fill=INK)
        d.text((x+12, y+393), filename, font=font(20), fill=INK)
    d.text((1020, 665), '100% scale • millimeters', font=font(25), fill=INK)
    d.text((1020, 713), '0.2 mm layer starting point', font=font(23), fill=INK)
    d.text((1020, 755), 'Inspect bridges in the slicer.', font=font(23), fill=INK)
    d.text((1020, 797), 'Use README for assembly.', font=font(23), fill=INK)
    d.text((40, 1060), 'Exact exported meshes • display is omitted from print files • colors are illustrative', font=font(22), fill=INK)
    canvas.save(OUT / 'preview-print-parts.png')
    manifest = {'renderer': 'CPU orthographic triangle rasterizer with per-pixel depth buffer',
                'renderer_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                'mesh_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.glob('*.stl')},
                'notes': 'Actual exported meshes. Assembled image adds labeled nominal display glass only. No toolpaths.',
                'images': ['preview-assembled.png', 'preview-exploded.png', 'preview-power-face.png', 'preview-print-parts.png']}
    (OUT / 'preview-manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')


if __name__ == '__main__':
    main()
