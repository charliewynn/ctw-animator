# CTW Animator

Browser playground for the CTW logo **wireframe-build** animation, plus the Python tools that generated it.

**Live:** https://charliewynn.github.io/ctw-animator/

## The animation

The 127-triangle CTW solid (W = right face, T = front, C = top) builds itself:

1. **Edges first** — triangle wireframes draw on from the ground up
2. **Faces follow** — flat-shaded faces fill in behind the wireframe, starting partway through the edge build (default: 61% of the way through)

The reference render: [renders/wire-built-version.gif](renders/wire-built-version.gif)

## Web app

`index.html` + `app.js` + `style.css` — vanilla JS, Canvas 2D, no build step. It ports `tools/anim_facets_v4.py` to the browser (painter's-algorithm faces instead of a per-pixel z-buffer).

Tweakable live:

- **Timing** — total frames, edge-build frames, face-start offset (% of edge build), fps
- **Build order** — ground-up (sorted by triangle height) or random
- **Colors** — clay base, edge color, line width
- **Light** — direction XYZ sliders + ambient
- **Export** — record one full loop as WebM (`canvas.captureStream` + `MediaRecorder`)

Geometry: [ctw-tris.json](ctw-tris.json) — 127 triangles of the union solid.

## Python tools

See [tools/README.md](tools/README.md).
