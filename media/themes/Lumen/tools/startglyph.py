# Original Lumen start glyph: a four-point spark in accent blue. Not derived from any logo.
from PIL import Image, ImageDraw
import sys, math
def glyph(size):
    S=size*8; im=Image.new('RGBA',(S,S),(0,0,0,0))
    # gradient fill
    grad=Image.new('RGBA',(S,S))
    for y in range(S):
        for x in range(S):
            t=(x+y)/(2*S)
            c=(int(16+(60-16)*t), int(110+(190-110)*t), int(220+(250-220)*t),255)
            grad.putpixel((x,y),c)
    mask=Image.new('L',(S,S),0); d=ImageDraw.Draw(mask)
    c=S/2; r=S*0.47; w=S*0.13
    pts=[]
    for i in range(16):
        a=i*math.pi/8 - math.pi/2
        rad = r if i%4==0 else (w*1.25 if i%2==0 else w*0.9)
        pts.append((c+rad*math.cos(a), c+rad*math.sin(a)))
    d.polygon(pts, fill=255)
    d.ellipse((c-w*1.6,c-w*1.6,c+w*1.6,c+w*1.6), fill=255)
    im.paste(grad,(0,0),mask)
    return im.resize((size,size),Image.LANCZOS)
if __name__=='__main__':
    size=int(sys.argv[2]) if len(sys.argv)>2 else 24
    g=glyph(size)
    g.save(sys.argv[1])

def save_premul_bmp(im, path):
    """32bpp BI_RGB bottom-up BMP with premultiplied alpha (what explorer's start image uses)."""
    import struct
    im=im.convert('RGBA'); w,h=im.size; rows=[]
    for y in range(h-1,-1,-1):
        r=bytearray()
        for x in range(w):
            R,G,B,A=im.getpixel((x,y))
            r+=bytes((B*A//255,G*A//255,R*A//255,A))
        rows.append(bytes(r))
    data=b''.join(rows)
    hdr=struct.pack('<2sIHHI',b'BM',54+len(data),0,0,54)+struct.pack('<IiiHHIIiiII',40,w,h,1,32,0,len(data),3780,3780,0,0)
    open(path,'wb').write(hdr+data)
