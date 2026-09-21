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

def project_pts(verts):
    xs=verts[:,0]; ys=verts[:,1]; zs=verts[:,2]
    sx=cx+(xs-zs)*COS30*s
    sy=cy-(ys-(xs+zs)*SIN30)*s
    depth=xs+ys+zs
    return sx,sy,depth

def clip_poly_y(poly, thresh):
    # poly: list of 3D points, keep y<=thresh
    if not poly: return []
    newp=[]
    n=len(poly)
    for i in range(n):
        cur=poly[i]; prev=poly[i-1]
        cur_in=cur[1]<=thresh+1e-9
        prev_in=prev[1]<=thresh+1e-9
        if cur_in:
            if not prev_in:
                t=(thresh-prev[1])/((cur[1]-prev[1])+1e-12)
                inter=prev+t*(cur-prev)
                newp.append(inter)
            newp.append(cur)
        elif prev_in:
            t=(thresh-prev[1])/((cur[1]-prev[1])+1e-12)
            inter=prev+t*(cur-prev)
            newp.append(inter)
    return newp

verts=verts0
fns=compute_face_ns(verts)
# build plate grid at y=0
plate_y=0

frames=[]
nframes=48
for fi in range(nframes):
    # ease in-out for thresh 0->5, hold at end
    t_raw=fi/(nframes-1)
    # ease: smoothstep
    t=t_raw*t_raw*(3-2*t_raw)
    thresh=0.05+4.95*t
    # clip and collect tris
    clipped_tris=[]  # list of (tri_verts_3d, fn)
    for fii,(i0,i1,i2) in enumerate(idxs):
        v0,v1,v2=verts[i0],verts[i1],verts[i2]
        poly=clip_poly_y([v0,v1,v2], thresh)
        if len(poly)<3: continue
        fn=fns[fii]
        # triangulate
        for k in range(1,len(poly)-1):
            clipped_tris.append((poly[0],poly[k],poly[k+1],fn))
    # render
    img=np.zeros((H,W,4),dtype=np.uint8)
    zbuf=np.full((H,W),-1e9,dtype=np.float32)
    # draw build plate first (as background)
    # plate: rectangle in 3D at y=0, x 0..5, z 0..5, draw as flat
    # We'll draw it in PIL after 3D for simplicity
    for (p0,p1,p2,fn) in clipped_tris:
        # project
        pts=np.array([p0,p1,p2])
        xs=pts[:,0]; ys=pts[:,1]; zs=pts[:,2]
        sx_=cx+(xs-zs)*COS30*s
        sy_=cy-(ys-(xs+zs)*SIN30)*s
        d_=xs+ys+zs
        x0,y0=sx_[0],sy_[0]; x1,y1=sx_[1],sy_[1]; x2,y2=sx_[2],sy_[2]
        d0,d1,d2=d_[0],d_[1],d_[2]
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
        diff=max(0,float(np.dot(fn,light)))
        shade=ambient+diffuse_w*diff
        col=np.clip(base*shade,0,255).astype(np.uint8)
        reg=img[miny:maxy+1,minx:maxx+1]
        reg[upd,0]=col[0]; reg[upd,1]=col[1]; reg[upd,2]=col[2]; reg[upd,3]=255
        sub[upd]=d[upd]
    pil=Image.fromarray(img,mode='RGBA')
    d=ImageDraw.Draw(pil)
    # build plate: draw iso grid
    # plate corners
    def proj(x,y,z): return (cx+(x-z)*COS30*s, cy-(y-(x+z)*SIN30)*s)
    # draw plate as dark slab
    c000=proj( -0.5,0,-0.5); c500=proj(5.5,0,-0.5); c550=proj(5.5,0,5.5); c050=proj(-0.5,0,5.5)
    d.polygon([c000,c500,c550,c050],fill=(50,50,55,255),outline=(80,80,85,255))
    # grid lines
    for gx in np.linspace(0,5,6):
        a=proj(gx,0,0); b=proj(gx,0,5)
        d.line([a,b],fill=(70,70,75,255),width=1)
    for gz in np.linspace(0,5,6):
        a=proj(0,0,gz); b=proj(5,0,gz)
        d.line([a,b],fill=(70,70,75,255),width=1)
    # we need to composite 3D on top of plate -> we drew plate after, so redo: draw plate first then 3D
    # quick fix: create plate bg then alpha composite 3D
    plate_img=Image.new('RGBA',(W,H),(0,0,0,0))
    pd=ImageDraw.Draw(plate_img)
    pd.polygon([c000,c500,c550,c050],fill=(50,50,55,255),outline=(80,80,85,255))
    for gx in np.linspace(0,5,6):
        a=proj(gx,0,0); b=proj(gx,0,5); pd.line([a,b],fill=(70,70,75,255),width=1)
    for gz in np.linspace(0,5,6):
        a=proj(0,0,gz); b=proj(5,0,gz); pd.line([a,b],fill=(70,70,75,255),width=1)
    pil=Image.alpha_composite(plate_img, pil)
    d=ImageDraw.Draw(pil)
    # print head: a glowing bar at thresh
    # project a line across at y=thresh
    hx0,hy0=proj(-0.5,thresh,-0.5); hx1,hy1=proj(5.5,thresh,-0.5); hx2,hy2=proj(5.5,thresh,5.5); hx3,hy3=proj(-0.5,thresh,5.5)
    # draw translucent plane
    d.polygon([(hx0,hy0),(hx1,hy1),(hx2,hy2),(hx3,hy3)],fill=(100,180,255,40))
    # laser line at front edge
    d.line([(hx0,hy0),(hx1,hy1)],fill=(120,200,255,220),width=3)
    d.line([(hx1,hy1),(hx2,hy2)],fill=(120,200,255,140),width=2)
    # nozzle: small rect at center of front edge, moving with sin
    nx=(hx0+hx1)/2 + 40*math.sin(fi*0.3)
    ny=(hy0+hy1)/2
    d.rectangle([nx-12,ny-18,nx+12,ny+2],fill=(30,30,35,255),outline=(120,200,255,255))
    d.rectangle([nx-4,ny+2,nx+4,ny+8],fill=(120,200,255,255))
    frames.append(pil)
    print(f"frame {fi+1}/{nframes}")

frames[0].save('/home/hatch/workspace/w-shape-editor/renders/anim-build-layers-v2.gif',save_all=True,append_images=frames[1:],duration=80,loop=0,disposal=2)
print("saved v2")
