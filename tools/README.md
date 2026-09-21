# Python tools

Original rasterizer + animation scripts used to develop the CTW logo renders.
They run locally with `numpy`, `Pillow` (and `scipy` for the clay grain in `logo_clay_v5.py`).
The built solid they read is `../ctw-tris.json` (127 triangles; copy it to `/tmp/ctw-tris.json` or edit the path).

- **`anim_facets_v4.py`** — the *wire built version*. Isometric projection, flat shading, 127 tris sorted ground-up by average Y. Edges draw on over 36 frames; faces start filling at frame 22 (earlier than 3/4 through the edge build) and overlap. Output: `anim-build-facets-v4.gif`.
- **`anim_layers_v2.py`** — alternate "3D-print" build: triangles clipped at a rising Y plane, with build plate, grid, laser plane and a sweeping nozzle. Output: `anim-build-layers-v2.gif`.
- **`logo_pure.py`** — flat-shaded isometric still of the pure (no-roundover) solid, transparent + studio-background PNGs.
- **`logo_clay_v5.py`** — clay-material still: matte base color, multi-scale grain noise, shader-based 1/4 roundovers on convex edges only (C–W interior seam excluded). Output: `ctw-logo-clay-v5-*.png`.

The browser app in `../` ports `anim_facets_v4.py` to Canvas 2D.
