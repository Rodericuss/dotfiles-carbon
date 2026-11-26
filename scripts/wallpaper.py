#!/usr/bin/env python3
"""Builds config/carbon/wallpaper.png: #161616 with a faint 2x grid and the four type squares."""
import sys
from pathlib import Path
import cairo
W,H=int(sys.argv[1]) if len(sys.argv)>1 else 3840, int(sys.argv[2]) if len(sys.argv)>2 else 2160
out=Path(__file__).resolve().parents[1]/'config/carbon/wallpaper.png'
def rgb(h):return tuple(int(h[i:i+2],16)/255 for i in (1,3,5))
s=cairo.ImageSurface(cairo.FORMAT_RGB24,W,H);c=cairo.Context(s)
c.set_source_rgb(*rgb('#161616'));c.paint()
u=H/1080  # one artboard pixel
step=64*u
c.set_source_rgb(*rgb('#1b1b1b'))
x=0.0
while x<W:c.rectangle(round(x),0,max(1,round(u)),H);x+=step
y=0.0
while y<H:c.rectangle(0,round(y),W,max(1,round(u)));y+=step
c.fill()
# grid crossings on every 4th line get a slightly brighter mark, like Carbon's 2x grid
c.set_source_rgb(*rgb('#262626'))
for i in range(0,int(W/step)+1,4):
    for j in range(0,int(H/step)+1,4):c.rectangle(round(i*step)-3*u,round(j*step),7*u,u);c.rectangle(round(i*step),round(j*step)-3*u,u,7*u)
c.fill()
for i,col in enumerate(('#78a9ff','#be95ff','#ff7eb6','#3ddbd9')):
    c.set_source_rgb(*rgb(col));c.rectangle(W-(64+(3-i)*20)*u-16*u,H-64*u-16*u,16*u,16*u);c.fill()
s.write_to_png(str(out));print(out)
