import json, numpy as np, math
from PIL import Image, ImageDraw
tris_raw=[np.array(t,float) for t in json.load(open('/tmp/ctw-tris.json'))]
def vkey(v): return (round(float(v[0]),6),round(float(v[1]),6),round(float(v[2]),6))
vd={}; verts0=[]; idxs=[]
for t in tris_raw:
    cur=[]
    for v in t:
        k=vkey(v)
        if k not in vd:
            vd[k]=len(verts0); verts0.append(np.array(v,float))
        cur.append(vd[k])
    idxs.append(tuple(cur))
verts0=np.array(verts0)
W=H=600
cx,cy=300,320
s=56
COS30=math.cos(math.pi/6); SIN30=math.sin(math.pi/6)
light=np.array([-0.5,0.75,-0.4]); light/=np.linalg.norm(light)
ambient=0.62; diffuse_w=0.38
base=np.array([210,175,132],float)
def compute_face_ns(verts):
    fns=[]
    for (i0,i1,i2) in idxs:
        A,B,C=verts[i0],verts[i1],verts[i2]
        n=np.cross(B-A,C-A); l=np.linalg.norm(n)
        fns.append(n/l if l>1e-12 else np.array([0.,0.,1.]))
    return np.array(fns)
verts=verts0
fns=compute_face_ns(verts)
xs=verts[:,0]; ys=verts[:,1]; zs=verts[:,2]
sx=cx+(xs-zs)*COS30*s
sy=cy-(ys-(xs+zs)*SIN30)*s
depth=xs+ys+zs
tri_avg_y=[(verts[i0,1]+verts[i1,1]+verts[i2,1])/3 for (i0,i1,i2) in idxs]
order=np.argsort(tri_avg_y)
nframes=48
edge_total=36
face_start=22  # 3/4 of 36
face_total=nframes-face_start  # 21
frames=[]
for fi in range(nframes):
    # edges
    if fi<edge_total:
        n_edges=int(len(idxs)*(fi+1)/edge_total)
    else:
        n_edges=len(idxs)
    # faces
    if fi<face_start:
        n_faces=0
    else:
        n_faces=int(len(idxs)*(fi-face_start+1)/face_total)
    n_edges=min(n_edges,len(idxs)); n_faces=min(n_faces,len(idxs))
    edge_set=set(order[:n_edges].tolist())
    face_set=set(order[:n_faces].tolist())
    # start with transparent
    img=Image.new('RGBA',(W,H),(0,0,0,0))
    # render faces first (so edges draw on top)
    if n_faces>0:
        fimg=np.zeros((H,W,4),dtype=np.uint8)
        zbuf=np.full((H,W),-1e9,dtype=np.float32)
        for fii in face_set:
            i0,i1,i2=idxs[fii]
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
            dd=w0*d0+w1*d1+w2*d2
            sub=zbuf[miny:maxy+1,minx:maxx+1]
            upd=mask&(dd>sub)
            if not np.any(upd): continue
            fn=fns[fii]
            diff=max(0,float(np.dot(fn,light)))
            shade=ambient+diffuse_w*diff
            col=np.clip(base*shade,0,255).astype(np.uint8)
            reg=fimg[miny:maxy+1,minx:maxx+1]
            reg[upd,0]=col[0]; reg[upd,1]=col[1]; reg[upd,2]=col[2]; reg[upd,3]=255
            sub[upd]=dd[upd]
        fimg_pil=Image.fromarray(fimg,mode='RGBA')
        img=Image.alpha_composite(img, fimg_pil)
    d=ImageDraw.Draw(img)
    for fii in edge_set:
        i0,i1,i2=idxs[fii]
        pts=[(sx[i0],sy[i0]),(sx[i1],sy[i1]),(sx[i2],sy[i2])]
        # if face already filled, draw edge fainter
        if fii in face_set:
            d.line([pts[0],pts[1],pts[2],pts[0]],fill=(110,80,55,120),width=1)
        else:
            d.line([pts[0],pts[1],pts[2],pts[0]],fill=(110,80,55,255),width=2)
    frames.append(img)
    print(f"frame {fi+1}/{nframes} edges {n_edges} faces {n_faces}")
frames[0].save('/home/hatch/workspace/w-shape-editor/renders/anim-build-facets-v4.gif',save_all=True,append_images=frames[1:],duration=85,loop=0,disposal=2)
print("saved v3")
