import json, numpy as np, math
from PIL import Image
tris_raw=[np.array(t,float) for t in json.load(open('/tmp/ctw-tris.json'))]
def vkey(v): return (round(float(v[0]),6),round(float(v[1]),6),round(float(v[2]),6))
vd={}; verts=[]; idxs=[]
for t in tris_raw:
    cur=[]
    for v in t:
        k=vkey(v)
        if k not in vd:
            vd[k]=len(verts); verts.append(np.array(v,float))
        cur.append(vd[k])
    idxs.append(tuple(cur))
verts=np.array(verts)
face_ns=[]
for (i0,i1,i2) in idxs:
    A,B,C=verts[i0],verts[i1],verts[i2]
    n=np.cross(B-A,C-A); l=np.linalg.norm(n)
    face_ns.append(n/l if l>1e-12 else np.array([0.,0.,1.]))
face_ns=np.array(face_ns)
W=H=1400
cx,cy=700,760
s=132
COS30=math.cos(math.pi/6); SIN30=math.sin(math.pi/6)
xs=verts[:,0]; ys=verts[:,1]; zs=verts[:,2]
sx=cx+(xs-zs)*COS30*s
sy=cy-(ys-(xs+zs)*SIN30)*s
depth=xs+ys+zs
img=np.zeros((H,W,4),dtype=np.uint8)
zbuf=np.full((H,W),-1e9,dtype=np.float32)
light=np.array([-0.5,0.75,-0.4]); light/=np.linalg.norm(light)
ambient=0.60; diffuse_w=0.40
base=np.array([210,175,132],float)
for fi,(i0,i1,i2) in enumerate(idxs):
    x0,y0=sx[i0],sy[i0]; x1,y1=sx[i1],sy[i1]; x2,y2=sx[i2],sy[i2]
    d0,d1,d2=depth[i0],depth[i1],depth[i2]
    minx=int(max(0,math.floor(min(x0,x1,x2)))); maxx=int(min(W-1,math.ceil(max(x0,x1,x2))))
    miny=int(max(0,math.floor(min(y0,y1,y2)))); maxy=int(min(H-1,math.ceil(max(y0,y1,y2))))
    if maxx<minx or maxy<miny: continue
    den=(y1-y2)*(x0-x2)+(x2-x1)*(y0-y2)
    if abs(den)<1e-9: continue
    xsr=np.arange(minx,maxx+1); ysr=np.arange(miny,maxy+1)
    xx,yy=np.meshgrid(xsr,ysr)
    w0=((y1-y2)*(xx-x2)+(x2-x1)*(yy-y2))/den
    w1=((y2-y0)*(xx-x2)+(x0-x2)*(yy-y2))/den
    w2=1-w0-w1
    mask=(w0>=-1e-6)&(w1>=-1e-6)&(w2>=-1e-6)
    if not np.any(mask): continue
    d=w0*d0+w1*d1+w2*d2
    sub=zbuf[miny:maxy+1,minx:maxx+1]
    upd=mask&(d>sub)
    if not np.any(upd): continue
    fn=face_ns[fi]
    diff=max(0,float(fn.dot(light)))
    shade=ambient+diffuse_w*diff
    col=np.clip(base*shade,0,255)
    reg=img[miny:maxy+1,minx:maxx+1]
    reg[upd,0]=col[0]; reg[upd,1]=col[1]; reg[upd,2]=col[2]; reg[upd,3]=255
    sub[upd]=d[upd]
Image.fromarray(img,mode='RGBA').save('/home/hatch/workspace/w-shape-editor/renders/ctw-logo-pure-v1-transparent.png')
print("saved pure transparent")
bg=np.zeros((H,W,3),dtype=np.uint8)
for y in range(H):
    tt=y/(H-1)
    r=int(95+tt*(200-95)); g=int(105+tt*(195-105)); b=int(120+tt*(185-120))
    bg[y,:,0]=r; bg[y,:,1]=g; bg[y,:,2]=b
alpha=img[:,:,3:4].astype(float)/255
comp=(img[:,:,:3].astype(float)*alpha + bg.astype(float)*(1-alpha)).astype(np.uint8)
Image.fromarray(comp).save('/home/hatch/workspace/w-shape-editor/renders/ctw-logo-pure-v1-studio.png')
print("saved pure studio")
