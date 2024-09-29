# Script to create pixel mosaics
# Uses Fansub Block font to draw

# Requirements
# pip install clipboard pillow

import os
import glob
import clipboard
import math
from PIL import Image

# if path is a directory, the script will get
# the last modified (newest) image file
IMAGE_LOCATION="./" 
# Put the entire drawing into one line
# Y overlap is not possible with this enabled
AS_SINGLE_EVENT = False
SCALE_NEAREST = False
X_OVERLAP = -1
Y_OVERLAP = -1 # only works when AS_SINGLE_EVENT is False
OVERRIDE_STYLE = "Sign"
X_SCALE = 103.25

image_file_path = ""
if os.path.isdir(IMAGE_LOCATION):
    files = []
    for file_type in ["*.png", "*.jpg", "*.jpeg", "*.webp"]:
        files.extend(glob.glob(os.path.join(IMAGE_LOCATION, file_type)))
    if files:
        image_file_path = max(files, key=os.path.getmtime)
    else:
        exit()
        print('No image!')
elif os.path.isfile(IMAGE_LOCATION):
    image_file_path = IMAGE_LOCATION
print("Image: ", image_file_path)

clip_line = input("Dialogue line with rect clip:\n> ")
_, start_time, end_time, style, _, _, _, _, _, text = clip_line.split(',',9)
coords = text.split('\\clip(')[-1].split(')')[0].split(',')
if len(coords) != 4:
    print('invalid line!')
    exit()
coords = [int(round(float(x))) for x in coords]
x1,y1,x2,y2 = coords

if OVERRIDE_STYLE:
    style = OVERRIDE_STYLE

pil_image = Image.open(image_file_path)
img_cropped = pil_image.crop(coords)
w, h = img_cropped.size

px_w = float(input("Block width in px:\n> "))
px_h = float(input("Block height in px:\n> "))

scale_size = (math.ceil(w/px_w), math.ceil(h/px_h))
img_scaled = img_cropped.resize(scale_size, Image.Resampling.BOX)
sw, sh = scale_size

overlap_scaled = X_OVERLAP*(px_h/px_w)

if AS_SINGLE_EVENT:
    out_text = [
        "{",
        f"\\pos({x1},{y1})\\fsp{X_OVERLAP}\\fnFansub Block\\an7",
        f"\\fs{px_w-X_OVERLAP}\\fscx{X_SCALE}\\fscy{round((px_h/(px_w-X_OVERLAP))*100,3)}",
        f"\\clip({x1},{y1},{x2},{y2})",
        "}",
    ]
    for y in range(sh):
        for x in range(sw):
            if SCALE_NEAREST:
                s_x = min(int(round(x*px_w+px_w/2)), w-1)
                s_y = min(int(round(y*px_h+px_h/2)), h-1)
                sample_point = (s_x, s_y)
                color = img_cropped.getpixel(sample_point)
            else:
                color = img_scaled.getpixel((x,y))
            r,g,b = color
            out_text.append("{")
            # out_text.append(f"\\1c&H{b:02X}{g:02X}{r:02X}&")
            out_text.append(f"\\cH{b:02X}{g:02X}{r:02X}")
            out_text.append("}A")
        out_text.append("\\N")

    out_line = f"Dialogue: 0,{start_time},{end_time},{style},,0,0,0,,{"".join(out_text)}"
else:
    out_text = []
    for y in range(sh):
        line_text = [
            "{",
            f"\\pos({x1},{y1+(y*px_h)})\\fsp{X_OVERLAP}\\fnFansub Block\\an7",
            f"\\fs{px_w-X_OVERLAP}\\fscx{X_SCALE}\\fscy{round((px_h*((px_h-Y_OVERLAP)/px_h)/(px_w-X_OVERLAP))*100,3)}",
            f"\\clip({x1},{y1},{x2},{y2})",
            "}"
        ]
        for x in range(sw):
            if SCALE_NEAREST:
                s_x = min(int(round(x*px_w+px_w/2)), w-1)
                s_y = min(int(round(y*px_h+px_h/2)), h-1)
                sample_point = (s_x, s_y)
                color = img_cropped.getpixel(sample_point)
            else:
                color = img_scaled.getpixel((x,y))
            r,g,b = color
            line_text.append("{")
            line_text.append(f"\\cH{b:02X}{g:02X}{r:02X}")
            line_text.append("}A")
        out_text.append(
            f"Dialogue: 0,{start_time},{end_time},{style},,0,0,0,,{"".join(line_text)}"
        )
    out_line = "\n".join(out_text)

print(out_line)
clipboard.copy(out_line)
print("Copied result to clipboard")