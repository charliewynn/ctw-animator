/* CTW Animator — Canvas 2D port of tools/anim_facets_v4.py
 * Isometric projection, flat shading, ground-up wireframe-then-faces build.
 */
'use strict';

const COS30 = Math.cos(Math.PI / 6), SIN30 = Math.sin(Math.PI / 6);
const W = 600, H = 600, CX = 300, CY = 320, S = 56;

const P = {
  totalFrames: 48,
  edgeFrames: 36,
  faceStartPct: 61,   // faces start at this % of the edge build
  fps: 12,
  base: [210, 175, 132],
  edge: [110, 80, 55],
  light: [-0.5, 0.75, -0.4],
  ambient: 0.62,
  diffuse: 0.38,
  order: 'ground',
  lineWidth: 2,
};

let verts = [], faces = [], faceN = [], proj = [], depth = [], orderIdx = [];
let fi = 0, playing = true, timer = null, recording = false, recorded = 0, recorder = null;

const canvas = document.getElementById('stage');
const ctx = canvas.getContext('2d');

function sub(a, b) { return [a[0]-b[0], a[1]-b[1], a[2]-b[2]]; }
function cross(a, b) {
  return [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]];
}
function norm(v) {
  const l = Math.hypot(v[0], v[1], v[2]) || 1;
  return [v[0]/l, v[1]/l, v[2]/l];
}
function dot(a, b) { return a[0]*b[0] + a[1]*b[1] + a[2]*b[2]; }
function hexRgb(h) {
  return [parseInt(h.slice(1,3),16), parseInt(h.slice(3,5),16), parseInt(h.slice(5,7),16)];
}
function rgba(c, a) { return `rgba(${c[0]|0},${c[1]|0},${c[2]|0},${a})`; }

function buildGeometry(tris) {
  // weld vertices
  const map = new Map(); verts = []; faces = [];
  const key = v => v.map(n => n.toFixed(6)).join(',');
  for (const t of tris) {
    const idx = [];
    for (const v of t) {
      const k = key(v);
      if (!map.has(k)) { map.set(k, verts.length); verts.push(v); }
      idx.push(map.get(k));
    }
    faces.push(idx);
  }
  // face normals
  faceN = faces.map(([i0,i1,i2]) =>
    norm(cross(sub(verts[i1], verts[i0]), sub(verts[i2], verts[i0]))));
  // project
  proj = verts.map(([x,y,z]) => [CX + (x - z) * COS30 * S, CY - (y - (x + z) * SIN30) * S]);
  depth = verts.map(([x,y,z]) => x + y + z);
  computeOrder();
}

function computeOrder() {
  const avgY = faces.map(([i0,i1,i2]) => (verts[i0][1] + verts[i1][1] + verts[i2][1]) / 3);
  orderIdx = faces.map((_, i) => i);
  if (P.order === 'ground') {
    orderIdx.sort((a,b) => avgY[a] - avgY[b]);
  } else {
    for (let i = orderIdx.length - 1; i > 0; i--) {
      const j = (Math.random() * (i + 1)) | 0;
      [orderIdx[i], orderIdx[j]] = [orderIdx[j], orderIdx[i]];
    }
  }
}

function frameCounts() {
  const N = faces.length;
  const edgeTotal = Math.min(P.edgeFrames, P.totalFrames);
  const faceStart = Math.round(edgeTotal * P.faceStartPct / 100);
  const faceTotal = Math.max(1, P.totalFrames - faceStart);
  const nEdges = fi < edgeTotal ? Math.min(N, Math.floor(N * (fi + 1) / edgeTotal)) : N;
  const nFaces = fi < faceStart ? 0 : Math.min(N, Math.floor(N * (fi - faceStart + 1) / faceTotal));
  return { nEdges, nFaces };
}

function render() {
  ctx.clearRect(0, 0, W, H);
  const { nEdges, nFaces } = frameCounts();
  const edgeSet = new Set(orderIdx.slice(0, nEdges));
  const faceSet = new Set(orderIdx.slice(0, nFaces));
  const L = norm(P.light);

  // faces, painter's algorithm (far first = smaller x+y+z)
  if (nFaces > 0) {
    const list = orderIdx.slice(0, nFaces).sort((a, b) => {
      const da = (depth[faces[a][0]] + depth[faces[a][1]] + depth[faces[a][2]]) / 3;
      const db = (depth[faces[b][0]] + depth[faces[b][1]] + depth[faces[b][2]]) / 3;
      return da - db;
    });
    for (const f of list) {
      const [i0, i1, i2] = faces[f];
      const d = Math.max(0, dot(faceN[f], L));
      const shade = P.ambient + P.diffuse * d;
      const c = P.base.map(v => Math.min(255, v * shade));
      ctx.fillStyle = rgba(c, 1);
      ctx.beginPath();
      ctx.moveTo(proj[i0][0], proj[i0][1]);
      ctx.lineTo(proj[i1][0], proj[i1][1]);
      ctx.lineTo(proj[i2][0], proj[i2][1]);
      ctx.closePath();
      ctx.fill();
    }
  }
  // edges
  ctx.lineJoin = 'round';
  for (const f of edgeSet) {
    const [i0, i1, i2] = faces[f];
    const filled = faceSet.has(f);
    ctx.strokeStyle = rgba(P.edge, filled ? 120/255 : 1);
    ctx.lineWidth = filled ? 1 : P.lineWidth;
    ctx.beginPath();
    ctx.moveTo(proj[i0][0], proj[i0][1]);
    ctx.lineTo(proj[i1][0], proj[i1][1]);
    ctx.lineTo(proj[i2][0], proj[i2][1]);
    ctx.closePath();
    ctx.stroke();
  }
  document.getElementById('frame-label').textContent =
    `frame ${fi + 1} / ${P.totalFrames} · ${nEdges} edges · ${nFaces} faces`;
}

function tick() {
  render();
  if (recording) {
    recorded++;
    if (recorded >= P.totalFrames) stopRecording();
  }
  fi = (fi + 1) % P.totalFrames;
}

function startLoop() {
  stopLoop();
  timer = setInterval(tick, 1000 / P.fps);
}
function stopLoop() { if (timer) clearInterval(timer); timer = null; }

function bindSlider(id, vid, fmt, apply) {
  const el = document.getElementById(id), lab = document.getElementById(vid);
  el.addEventListener('input', () => {
    const v = +el.value;
    lab.textContent = fmt(v);
    apply(v);
    if (P.edgeFrames > P.totalFrames) { P.edgeFrames = P.totalFrames; }
    if (!playing) render();
  });
}

function initUI() {
  const btn = document.getElementById('btn-play');
  btn.addEventListener('click', () => {
    playing = !playing;
    btn.textContent = playing ? '⏸ Pause' : '▶ Play';
    if (playing) startLoop(); else stopLoop();
  });
  document.getElementById('btn-restart').addEventListener('click', () => { fi = 0; render(); });
  document.getElementById('btn-export').addEventListener('click', exportVideo);

  bindSlider('s-total', 'v-total', v => v, v => P.totalFrames = v);
  bindSlider('s-edge', 'v-edge', v => v, v => P.edgeFrames = Math.min(v, P.totalFrames));
  bindSlider('s-facestart', 'v-facestart', v => v, v => P.faceStartPct = v);
  bindSlider('s-fps', 'v-fps', v => v, v => { P.fps = v; if (playing) startLoop(); });
  bindSlider('s-lw', 'v-lw', v => v, v => P.lineWidth = v);
  bindSlider('s-lx', 'v-lx', v => (v/100).toFixed(2), v => P.light[0] = v/100);
  bindSlider('s-ly', 'v-ly', v => (v/100).toFixed(2), v => P.light[1] = v/100);
  bindSlider('s-lz', 'v-lz', v => (v/100).toFixed(2), v => P.light[2] = v/100);
  bindSlider('s-amb', 'v-amb', v => (v/100).toFixed(2), v => P.ambient = v/100);

  document.getElementById('c-base').addEventListener('input', e => { P.base = hexRgb(e.target.value); if (!playing) render(); });
  document.getElementById('c-edge').addEventListener('input', e => { P.edge = hexRgb(e.target.value); if (!playing) render(); });

  document.querySelectorAll('input[name=order]').forEach(r =>
    r.addEventListener('change', () => { P.order = document.querySelector('input[name=order]:checked').value; computeOrder(); if (!playing) render(); }));
}

function exportVideo() {
  const linkBox = document.getElementById('export-link');
  if (!('MediaRecorder' in window) || !canvas.captureStream) {
    linkBox.textContent = 'Video export not supported in this browser.';
    return;
  }
  const btn = document.getElementById('btn-export');
  btn.disabled = true;
  linkBox.textContent = 'Recording…';
  const stream = canvas.captureStream(P.fps);
  const chunks = [];
  recorder = new MediaRecorder(stream, { mimeType: 'video/webm' });
  recorder.ondataavailable = e => { if (e.data.size) chunks.push(e.data); };
  recorder.onstop = () => {
    const url = URL.createObjectURL(new Blob(chunks, { type: 'video/webm' }));
    linkBox.innerHTML = `<a href="${url}" download="ctw-build.webm">Download ctw-build.webm</a>`;
    btn.disabled = false;
  };
  fi = 0; recorded = 0; recording = true;
  if (!playing) { playing = true; document.getElementById('btn-play').textContent = '⏸ Pause'; startLoop(); }
  recorder.start();
}
function stopRecording() {
  recording = false;
  if (recorder && recorder.state !== 'inactive') recorder.stop();
}

fetch('ctw-tris.json')
  .then(r => r.json())
  .then(tris => {
    buildGeometry(tris);
    initUI();
    render();
    startLoop();
  })
  .catch(err => {
    document.querySelector('.stage').insertAdjacentHTML('beforeend',
      `<p class="hint">Failed to load ctw-tris.json: ${err}</p>`);
  });
