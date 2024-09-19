# very stinky code ewwww

import json
import cv2
import potrace
import pysubs2
import ass_tag_parser

from assdrawing import ASSDrawing

# -------- SETTINGS START ------------

INPUT_VIDEO_PATH = './bad apple.webm'
INPUT_ASS_PATH = 'bad_apple_ass_font.ass'
OUTPUT_ASS_PATH = 'test.ass'
TRIM_EVENTS = False
TRIM_EVENTS_PAD_MS = 0
SORT_EVENTS = True
IMAGE_DIM_MULT = .35  # scales image before vectorizing
# reduces detail without adding jitter
BLUR_AMOUNT = 4

# start: 34
# apple: 450
# stars: 530-770
# lyrics start: 843
# petals: 2070
# sun: 2947
# some people say this may be inaccurate. it worked fine for me
# may vary with video files
START_FRAME = None
END_FRAME = None
VIDEO_OFFSET_MS = 0

# do shape stuff for video
MAKE_SHAPE = True
# very funny but very efficient
# generates font data to be used with svgs2ttf.py (requires fontforge)
GENERATE_FONT = False
SKIP_SVG_GEN = False  # skips svg generation for font
# codepoints to use during font data creation
# - cjk unified ideographs
# - hangul syllables
# - private use area
UNICODE_RANGES = [(0x4e00,0x9fff), (0xac00,0xd7af), (0xe000,0xf8ff)]
FONT_DATA_OUTPUT_PATH = "./bad_apple_font.json"
FONT_SVG_INPUT_FOLDER = "./folder_of_svgs"
FONT_NAME = "WhenTheAppleIsBad"
FONT_VERSION = "001.069"
FONT_COPYRIGHT = "Copyright (c) 2024 by ur mom"
FONT_EM_SIZE = 1000  # keep this if you don't need more resolution
# will generate .ttf and .woff2 files
FONT_OUTPUT_NAME = "BadAppleFont"

# i used this to make draw commands (for shapes, not clips) 
# use a max of 3 digits
# shape is scaled to final size in the subtitle file using the 
# style scalex and scaley
# this doesn't do anything when generating svgs for font
SHAPE_SCALE = 1

# reduces detail of clip vectors by downscaling
# this is applied with IMG_DIM_MULT
CLIP_DIM_MULT = .75  
# the source video had two pixels of black on the top and bottom
CROP_Y1 = None
CROP_Y2 = None
# ignores the dialogue line's existing clip, which is used as
# bounds for the clip
# helps with aligning video with clips
IGNORE_CLIP_BOUNDS = False
# applied to the image before vectorization
RASTER_CLIP_SHIFT_X = 0
RASTER_CLIP_SHIFT_Y = 0
RASTER_CLIP_PAD_X = 0
RASTER_CLIP_PAD_Y = 0
RASTER_CLIP_SCALE_X = 1
RASTER_CLIP_SCALE_Y = 1
# applied after vectorization
VECTOR_CLIP_SHIFT_X = 0
VECTOR_CLIP_SHIFT_Y = 0

# used for different shades of grey
THRESH_PALETTE = [
    {
        'threshold': 51,
        'style': 'Col2',
        'layer': 1
    },
    {
        'threshold': 182,
        'style': 'Col3',
        'layer': 2
    },
]

DEFAULT_THRESHOLD = 117
# used for clip to set thresholds for frame ranges
THRESH_FRAME_RANGES = [
    {
        'threshold': 240,
        'range': range(2744,2829)
    },
    {
        'threshold': 180,
        'range': range(2938,3142)
    },
    {
        'threshold': 205,
        'range': range(3293,3315)
    }
]

# pixel blob size for determining whether a layer (color) should
# exist in a frame. minor space savings
ERODE_KSIZE = 4

# scaling algorithm when resizing images
RESIZE_INTERPOLATION = cv2.INTER_CUBIC

# the clipping thing
# this is related to shapes and not clips
# instead of vectorizing the entire frame for a color shade,
# we can do some processing to only vectorize visible areas
# created as an attempt to further simplify vectors
# in practice it used up more space 
# so don't use it
DO_THE_CLIPPING_THING = False
COLOR_LAYER_CLIP_KSIZE = 15

# -------- SETTINGS END ------------

cap = cv2.VideoCapture(INPUT_VIDEO_PATH)
print(cap.get(cv2.CAP_PROP_FPS))


def to_svg(bw_image, destination):
    bm = potrace.Bitmap(bw_image)
    plist = bm.trace()

    with open(destination, "w") as fp:
        fp.write(
            f'''<svg version="1.1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{1000}" height="{1000}" viewBox="0 0 {bw_image.shape[1]/IMAGE_DIM_MULT} {bw_image.shape[0]/IMAGE_DIM_MULT}">''')
        parts = []
        i = 1/IMAGE_DIM_MULT
        for curve in plist:
            fs = curve.start_point
            parts.append(f"M{fs.x*i},{fs.y*i}")
            for segment in curve.segments:
                if segment.is_corner:
                    a = segment.c
                    b = segment.end_point
                    parts.append(f"L{a.x*i},{a.y*i}L{b.x*i},{b.y*i}")
                else:
                    a = segment.c1
                    b = segment.c2
                    c = segment.end_point
                    parts.append(f"C{a.x*i},{a.y*i} {b.x*i},{b.y*i} {c.x*i},{c.y*i}")
            parts.append("z")
        fp.write(f'<path stroke="none" fill="black" fill-rule="evenodd" d="{"".join(parts)}"/>')
        fp.write("</svg>")


def to_ass(bw_image, dim_mult=1):
    bm = potrace.Bitmap(bw_image)
    plist = bm.trace(
        turdsize=1,
        opttolerance=.2
    )
    d = ASSDrawing()

    for curve in plist:
        fs = curve.start_point
        d.append_move(fs.x, fs.y)
        for segment in curve.segments:
            if segment.is_corner:
                a = segment.c
                b = segment.end_point
                d.append_line(a.x,a.y)
                d.append_line(b.x,b.y)
            else:
                a = segment.c1
                b = segment.c2
                c = segment.end_point
                d.append_bezier(a.x, a.y, b.x, b.y, c.x, c.y)
    d.scale(1/IMAGE_DIM_MULT)
    d.scale(1/dim_mult)
    return d


# Check if thresholded frame has enough content to be vectorized
# Takes thresh_a and thresh_b, applies thresholds to frame and compares them
def check_frame(frame, thresh_a, thresh_b):
    ret,thresh1 = cv2.threshold(frame,thresh_a,255,cv2.THRESH_BINARY)
    ret,thresh2 = cv2.threshold(frame,thresh_b,255,cv2.THRESH_BINARY)
    together = cv2.bitwise_and(cv2.bitwise_not(thresh2),thresh1)
    eroded = cv2.erode(together,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(ERODE_KSIZE,ERODE_KSIZE)))
    return eroded.any()


# Prepare frame for vectorization
def prepare_frame(frame, x1=0, y1=0, x2=None, y2=None, frame_num=-1, threshold=None, scalex=1,scaley=1, dim_mult=1):
    x1 = int(x1/scalex)
    y1 = int(y1/scaley)+CROP_Y1
    if x2:
        x2 = int(x2/scalex)
    if y2:
        y2 = int(y2/scaley)+CROP_Y2
    else:
        y2 = CROP_Y2

    if not threshold:
        threshold = DEFAULT_THRESHOLD
        for f_range in THRESH_FRAME_RANGES:
            if frame_num in f_range['range']:
                threshold = f_range['threshold']
    mframe = frame[y1:y2, x1:x2]
    mframe = cv2.cvtColor(mframe, cv2.COLOR_BGR2GRAY)
    ret, mframe = cv2.threshold(mframe,threshold,255,cv2.THRESH_BINARY)
    if BLUR_AMOUNT > 0:
        mframe = cv2.blur(mframe, (BLUR_AMOUNT,BLUR_AMOUNT))
    mframe = cv2.resize(
        mframe, 
        (int(mframe.shape[1]*IMAGE_DIM_MULT*dim_mult*scalex),int(mframe.shape[0]*IMAGE_DIM_MULT*dim_mult*scaley)),
        interpolation=RESIZE_INTERPOLATION
    )
    ret, mframe = cv2.threshold(mframe,127,255,cv2.THRESH_BINARY)

    # cv2.imshow('frame_prep', frame_thresh)
    # cv2.waitKey(100)
    return mframe


# Reduces a frame to only important (visible) areas to be vectorized
def clip_frame(frame, upper_frame):
    frame_diff = cv2.bitwise_and(cv2.bitwise_not(upper_frame), frame)
    dilated = cv2.dilate(frame_diff,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(COLOR_LAYER_CLIP_KSIZE,COLOR_LAYER_CLIP_KSIZE)))
    clipped = cv2.bitwise_and(frame, dilated)
    final = cv2.bitwise_or(clipped, frame_diff)
    return final


subs = pysubs2.load(INPUT_ASS_PATH)

event_list = list(subs.events)
event_list_filtered = filter(lambda x: x.type == 'Dialogue', event_list)
event_list = sorted(event_list_filtered, key=lambda x: x.start)
event_list_i = 0


if START_FRAME:
    cap.set(cv2.CAP_PROP_POS_FRAMES, START_FRAME-1)
    cap.read()  # make POS_MSEC accurate
    video_time = cap.get(cv2.CAP_PROP_POS_MSEC) + VIDEO_OFFSET_MS
    while event_list_i < len(event_list):
        if event_list[event_list_i].start >= video_time:
            break
        event_list_i += 1
    if TRIM_EVENTS:
        subs.events = list(filter(lambda x: x.start >= video_time - TRIM_EVENTS_PAD_MS, subs.events))


if GENERATE_FONT:
    glyph_codepoint = UNICODE_RANGES[0][0]
    font_data = {
        "props": {
            "ascent": 96,
            "descent": 32,
            "em": FONT_EM_SIZE,
            "encoding": "UnicodeFull",
            "lang": "English (US)",
            "family": FONT_NAME,
            "style": "Regular",
            "familyname": FONT_NAME,
            "fontname": FONT_NAME,
            "fullname": FONT_NAME
        },
        "sfnt_names": [
            [
                "English (US)",
                "Copyright",
                FONT_COPYRIGHT
            ],
            [
                "English (US)",
                "Family",
                FONT_NAME
            ],
            [
                "English (US)",
                "SubFamily",
                "Regular"
            ],
            [
                "English (US)",
                "UniqueID",
                "ayayayayaya"
            ],
            [
                "English (US)",
                "Fullname",
                FONT_NAME
            ],
            [
                "English (US)",
                "Version",
                f"Version {FONT_VERSION}"
            ],
            [
                "English (US)",
                "PostScriptName",
                FONT_NAME
            ]
        ],
        "input": FONT_SVG_INPUT_FOLDER,
        "output": [
            f"{FONT_OUTPUT_NAME}.ttf",
            f"{FONT_OUTPUT_NAME}.woff2"
        ],
        "glyphs": {}
    }


frame = None
ret = None
next_ret = None
video_time = 0
frame_duration = 0
next_frame = 0
next_frame_time = 0
while cap.isOpened():
    frame_num = int(cap.get(cv2.CAP_PROP_POS_FRAMES) - 1)
    if END_FRAME and cap.get(cv2.CAP_PROP_POS_FRAMES) - 1 > END_FRAME:
        print('made it to end frame')
        break

    if next_ret is not None:
        ret = next_ret
        frame = next_frame
        video_time = next_frame_time
    next_ret, next_frame = cap.read()
    next_frame_time = cap.get(cv2.CAP_PROP_POS_MSEC) + VIDEO_OFFSET_MS
    if ret is None:
        continue
    frame_duration = next_frame_time - video_time

    if not ret:
        print('end of file')
        break
    # cv2.imshow('full_frame',frame)

    ass_events = []
    while event_list_i < len(event_list):
        if event_list[event_list_i].start < video_time:
            ass_events.append(event_list[event_list_i])
        else:
            break
        event_list_i += 1

    for event in ass_events:
        parsed = ass_tag_parser.parse_ass(event.text)
        for i, part in enumerate(parsed):
            if type(part) == ass_tag_parser.AssTagClipRectangle:
                if not IGNORE_CLIP_BOUNDS:
                    pframe = prepare_frame(
                        frame,
                        part.x1-RASTER_CLIP_SHIFT_X,
                        part.y1-RASTER_CLIP_SHIFT_Y,
                        part.x2-RASTER_CLIP_SHIFT_X + RASTER_CLIP_PAD_X,
                        part.y2-RASTER_CLIP_SHIFT_Y + RASTER_CLIP_PAD_Y,
                        frame_num,
                        scalex=RASTER_CLIP_SCALE_X,
                        scaley=RASTER_CLIP_SCALE_Y,
                        dim_mult=CLIP_DIM_MULT
                    )
                    drawing = to_ass(pframe,CLIP_DIM_MULT).translate(
                        part.x1+VECTOR_CLIP_SHIFT_X,
                        part.y1+VECTOR_CLIP_SHIFT_Y
                    )
                else:
                    pframe = prepare_frame(
                        frame,
                        x1=-RASTER_CLIP_SHIFT_X,
                        y1=-RASTER_CLIP_SHIFT_Y,
                        frame_num=frame_num,
                        scalex=RASTER_CLIP_SCALE_X,
                        scaley=RASTER_CLIP_SCALE_Y,
                        dim_mult=CLIP_DIM_MULT
                    )
                    drawing = to_ass(pframe,CLIP_DIM_MULT).translate(VECTOR_CLIP_SHIFT_X,VECTOR_CLIP_SHIFT_Y)

                if not drawing.is_empty():
                    if part.inverse:
                        parsed[i] = ass_tag_parser.AssTagComment(drawing.get_iclip())
                    else:
                        parsed[i] = ass_tag_parser.AssTagComment(drawing.get_clip())
                else:
                    part.x1 += VECTOR_CLIP_SHIFT_X
                    part.x2 += VECTOR_CLIP_SHIFT_X
                    part.y1 += VECTOR_CLIP_SHIFT_Y
                    part.y2 += VECTOR_CLIP_SHIFT_Y
                    part.inverse = not part.inverse
                # print(drawing.get_string())

        event.text = ass_tag_parser.ass_composer.compose_ass(parsed)
        # event.start = video_time
        # event.end = next_frame_time


    if MAKE_SHAPE:
        layers = []
        for pal in THRESH_PALETTE:
            layers.append(prepare_frame(frame,threshold=pal['threshold']))

        for idx, pal in enumerate(THRESH_PALETTE):
            if idx < len(THRESH_PALETTE)-1:
                next_pal = THRESH_PALETTE[idx+1]
                if not check_frame(frame,pal['threshold'],next_pal['threshold']-1):
                    print('i saved space')
                    continue
            pframe = layers[idx]
            
            if not GENERATE_FONT:
                if DO_THE_CLIPPING_THING and idx < len(layers)-1:
                    clipped_frame = clip_frame(layers[idx], layers[idx+1])
                    clipped_ass = to_ass(cv2.bitwise_not(clipped_frame))
                    frame_ass = to_ass(cv2.bitwise_not(pframe))
                    if len(clipped_ass.get_string()) < len(frame_ass.get_string()):
                        frame_ass = clipped_ass
                        print('clipped layer')
                else:
                    frame_ass = to_ass(cv2.bitwise_not(pframe))
                ass_line = pysubs2.SSAEvent()
                ass_line.type = "Dialogue"
                ass_line.start = video_time - frame_duration/2
                ass_line.end = next_frame_time - frame_duration/2
                ass_line.layer = pal['layer']
                ass_line.style = pal['style']
                ass_line.text = frame_ass.scale(SHAPE_SCALE).get_drawing()
                subs.append(ass_line)
            else:
                filename = f"{frame_num}-{pal['style']}.svg"
                filepath = FONT_SVG_INPUT_FOLDER + "/" + filename
                if not SKIP_SVG_GEN:
                    to_svg(cv2.bitwise_not(pframe), filepath)
                ass_line = pysubs2.SSAEvent()
                ass_line.type = "Dialogue"
                ass_line.start = video_time - frame_duration/2
                ass_line.end = next_frame_time - frame_duration/2
                ass_line.layer = pal['layer']
                ass_line.style = pal['style']
                ass_line.text = chr(glyph_codepoint)
                subs.append(ass_line)

                font_data['glyphs'][f'0x{glyph_codepoint:x}'] = {
                    "src": filename,
                    "width": 1000
                }

                glyph_codepoint += 1
                for unicode_range in UNICODE_RANGES:
                    a, b = unicode_range
                    if glyph_codepoint >= a and glyph_codepoint >= b:
                        pass
                    elif glyph_codepoint >= a and glyph_codepoint <= b:
                        break
                    elif glyph_codepoint < a:
                        glyph_codepoint = a


    # print(ass_events)
    # cv2.imshow('frame',frame_thresh)
    print(frame_num)
    # if cv2.waitKey(1) & 0xFF == ord('q'):
    #     break

    frame_num += 1


if TRIM_EVENTS:
    subs.events = list(filter(lambda x: x.start < video_time + TRIM_EVENTS_PAD_MS, subs.events))

cap.release()
cv2.destroyAllWindows()

if SORT_EVENTS:
    subs.events.sort(key=lambda x: x.start)
subs.save(OUTPUT_ASS_PATH)

if GENERATE_FONT:
    with open(FONT_DATA_OUTPUT_PATH,"w") as f:
        json.dump(font_data,f)