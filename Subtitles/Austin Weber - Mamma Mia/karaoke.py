# THIS SCRIPT ASSUMES \an1 ON ALL LINES
# NO MULTI-HIGHLIGHT SUPPORT

from pyonfx import *
import re

io = Ass("./mamma mia austin weber.ass")
meta, styles, lines = io.get_data()

VISIBLE_LINES = 2
MAX_GAP_MS = 2000
LEAD_IN_MS = 1500
START_LEAD_IN_MS = 2500

MAX_LINGER_LENGTH = 1000
LINE_VERT_PADDING = 60
RIGHT_MARGIN = 0

BLUR = 1.125

CLIP_MARGIN = 10

indexlines = []
for line in lines:
    orgline = line
    line = line.copy()
    if orgline.effect != "kara":
        continue

    wordindex = []
    for word in orgline.words:
        wordindex.append({
            "word": word,
            "syls": []
        })
    for syl in orgline.syls:
        wordindex[syl.word_i]['syls'].append(syl)

    indexlines.append({
        "line": line,
        "words": wordindex,
    })

countdown_lines = []
for line in lines:
    orgline = line
    line = line.copy()
    if orgline.effect.lower() == "countdown":
        countdown_lines.append(line)
    else:
        continue

for line_mod in indexlines:
    line: Line = line_mod['line']
    last_word = line_mod['words'][-1]
    last_syl = last_word['syls'][-1]

    last_syl.end_time = line.duration
    last_syl.duration = line.duration - last_syl.start_time
    last_word['word'].end_time = line.duration
    last_word['word'].duration = line.duration - last_word['word'].start_time


split_indexlines = []
for line_mod in indexlines:
    orgline = line_mod['line']
    line = orgline.copy()
    lyrics_width = meta.play_res_x - line.styleref.margin_l - line.styleref.margin_r - RIGHT_MARGIN

    start_x = orgline.left
    word_buf = []
    for word_mod in line_mod['words']:
        word = word_mod['word']
        if (word.right - start_x >= lyrics_width) or ("\n" in word.text):
            split_indexlines.append({
                "line": line.copy(),
                "words": word_buf
            })
            start_x = word.right
            word_buf = []
        word_buf.append(word_mod)

    split_indexlines.append({
        "line": line.copy(),
        "words": word_buf
    })

for line_mod in split_indexlines:
    syl_buf = []
    for word in line_mod['words']:
        syl_buf.extend(word['syls'])
    line_mod['syls'] = syl_buf

for line_mod in split_indexlines:
    line: Line = line_mod['line']
    shift_x = line_mod['words'][0]['word'].left - line.left
    for word_mod in line_mod['words']:
        word: Word = word_mod['word']
        word.left -= shift_x
        word.right -= shift_x
        word.center -= shift_x
        for syl in word_mod['syls']:
            syl: Syllable
            syl.left -= shift_x
            syl.right -= shift_x
            syl.center -= shift_x
    line.right = line_mod['words'][-1]['word'].right
    line.center = (line.left + line.right) / 2
    line.width = line.right - line.left

LB = "{"
RB = "}"
for idx, line_mod in enumerate(split_indexlines):
    line: Line = line_mod['line']
    line_mod_next = None
    line_next: Line = None
    if idx+1 < len(split_indexlines):
        line_mod_next = split_indexlines[idx+1]
        line_next = line_mod_next['line']
    text_split = []

    start_time_shift = line_mod['syls'][0].start_time
    line.start_time += start_time_shift

    for word_mod in line_mod['words']:
        for syl in word_mod['syls']:
            syl: Syllable
            syl.start_time -= start_time_shift
            syl.end_time -= start_time_shift
            text_split.append(" " * syl.prespace)
            text_split.append(syl.text)
            text_split.append(" " * syl.postspace)

    line.end_time = line.start_time + line_mod['syls'][-1].end_time

    end_shift = MAX_LINGER_LENGTH
    if line_mod_next:
        # end_shift = min(MAX_LINGER_LENGTH, line_mod_next['syls'][0].duration)
        end_shift = line_mod_next['syls'][0].duration
    line.end_time += end_shift
    line.text = "".join(text_split)


# Transforms in place
def transform_line(line_mod, x, y):
    line: Line = line_mod['line']
    line.left += x
    line.center += x
    line.right += x
    line.top += y
    line.middle += y
    line.bottom += y
    for word_mod in line_mod['words']:
        word: Word = word_mod['word']
        word.left += x
        word.center += x
        word.right += x
        word.top += y
        word.middle += y
        word.bottom += y
        for syl in word_mod['syls']:
            syl: Syllable
            syl.left += x
            syl.center += x
            syl.right += x
            syl.top += y
            syl.middle += y
            syl.bottom += y

current_line_pos = 0
for idx, line_mod in enumerate(split_indexlines):
    line: Line = line_mod['line']
    line_mod_next = None
    line_next: Line = None
    if idx+1 < len(split_indexlines):
        line_mod_next = split_indexlines[idx+1]
        line_next = line_mod_next['line']

    line_mod['row'] = current_line_pos
    x_right_align = (meta.play_res_x - line.styleref.margin_r) - line.width - line.left
    shift_x = Utils.interpolate(current_line_pos/(VISIBLE_LINES-1), 0, x_right_align)
    y_shift = -(VISIBLE_LINES-current_line_pos-1)*(line.ascent+LINE_VERT_PADDING)

    transform_line(line_mod, shift_x, y_shift)

    current_line_pos += 1
    current_line_pos %= VISIBLE_LINES

    if line_next and line_next.start_time - line.end_time > MAX_GAP_MS:
        current_line_pos = 0

for line_mod in split_indexlines:
    line = line_mod['line']
    line.text = f"{LB}\\pos({line.left},{line.bottom}){RB}{line.text}"

# By line
for line_mod in split_indexlines:
    line: Line = line_mod['line'].copy()
    cl = CLIP_MARGIN

    bg_sung_line_text_split = []
    bg_unsung_line_text_split = []
    fg_sung_line_text_split = []
    fg_unsung_line_text_split = []
    addtext = [
        LB,
        f"\\pos({line.left},{line.bottom})",
        f"\\clip({line.left-cl},{line.top-cl},{line.left},{line.bottom+cl})",
        # f"\\c&HFF0000&\\3c&HFFFFFF&",
        # RB
    ]
    bg_sung_line_text_split.extend(addtext)
    fg_sung_line_text_split.extend(addtext)

    bg_sung_line_text_split.extend([
        f"\\c&HFFFFFF&\\3c&HFFFFFF&\\blur{BLUR}",
        RB
    ])
    fg_sung_line_text_split.extend([
        f"\\c&HFF0000&\\blur{BLUR}\\bord0",
        RB
    ])
    
    addtext = [
        LB,
        f"\\pos({line.left},{line.bottom})",
        f"\\clip({line.left-cl},{line.top-cl},{line.right+cl},{line.bottom+cl})",
        # RB
    ]
    bg_unsung_line_text_split.extend(addtext)
    fg_unsung_line_text_split.extend(addtext)
    bg_unsung_line_text_split.extend([
        f"\\c&H000000&\\3c&H000000&\\blur{BLUR}",
        RB
    ])
    fg_unsung_line_text_split.extend([
        f"\\c&HFFFFFF&\\blur{BLUR}\\bord0",
        RB
    ])


    for syl_idx, syl in enumerate(line_mod['syls']):
        syl_next = None
        if syl_idx+1 < len(line_mod['syls']):
            syl_next = line_mod['syls'][syl_idx+1]

        left = syl.left
        left_plus = syl.left
        right = syl.right
        right_plus = syl.right
        if syl.postspace > 0 or (not syl_next):
            right_plus += cl
        if syl.prespace > 0:
            left_plus -= cl

        addtext = [
            LB,
            f"\\t({syl.start_time},{syl.start_time},",
            f"\\clip({line.left-cl},{line.top-cl},{left_plus},{line.bottom+cl})"
            ")",
            f"\\t({syl.start_time},{syl.end_time},",
            f"\\clip({line.left-cl},{line.top-cl},{right_plus},{line.bottom+cl})"
            ")",
            RB,
            " " * syl.prespace,
            syl.text,   
            " " * syl.postspace,
        ]
        bg_sung_line_text_split.extend(addtext)
        fg_sung_line_text_split.extend(addtext)

        addtext = [
            LB,
            f"\\t({syl.start_time},{syl.start_time},",
            f"\\clip({left_plus},{line.top-cl},{line.right+cl},{line.bottom+cl})"
            ")",
            f"\\t({syl.start_time},{syl.end_time},",
            f"\\clip({right_plus},{line.top-cl},{line.right+cl},{line.bottom+cl})"
            ")",
            RB,
            " " * syl.prespace,
            syl.text,   
            " " * syl.postspace,
        ]
        bg_unsung_line_text_split.extend(addtext)
        fg_unsung_line_text_split.extend(addtext)

    line.text = "".join(bg_sung_line_text_split)
    io.write_line(line)
    line.text = "".join(fg_sung_line_text_split)
    io.write_line(line)
    line.text = "".join(bg_unsung_line_text_split)
    io.write_line(line)
    line.text = "".join(fg_unsung_line_text_split)
    io.write_line(line)

def remove_pos_tag(text):
    return re.sub(r'\\pos\(\d+(\.\d+)?,\d+(\.\d+)?\)', '', text)
def place_countdown(x, y, end_time):
    x_shift = x - countdown_lines[0].x
    y_shift = y - countdown_lines[0].y
    time_shift = end_time - countdown_lines[-1].end_time

    for orgline in countdown_lines:
        line: Line = orgline.copy()
        line.x += x_shift
        line.y += y_shift
        line.start_time += time_shift
        line.end_time += time_shift
        line.text = f"{LB}\\pos({line.x},{line.y}){RB}{remove_pos_tag(line.raw_text)}"
        io.write_line(line)


last_line = [None for _ in range(VISIBLE_LINES)]
start_start_time = 0
for idx, line_mod in enumerate(split_indexlines):
    orgline: Line = line_mod['line']
    line_mod_next = None
    orgline_next: Line = None
    if idx+1 < len(split_indexlines):
        line_mod_next = split_indexlines[idx+1]
        orgline_next = line_mod_next['line']

    is_starting_line = False
    line = orgline.copy()
    start_time = 0
    end_time = line_mod['line'].start_time
    row = line_mod['row']
    if not last_line[row]:
        if row == 0:
            if idx == 0:
                start_time = line_mod['line'].start_time - START_LEAD_IN_MS
                is_starting_line = True
            else:
                start_time = line_mod['line'].start_time - LEAD_IN_MS

            start_start_time = start_time
        else:
            # start_time = last_line[0]['line'].start_time
            start_time = start_start_time
    else:
        start_time = last_line[row]['line'].end_time

    line.start_time = start_time
    line.end_time = end_time

    last_line[row] = line_mod

    if is_starting_line:
        place_countdown(line.left, line.top-20, line.end_time)

    bg_line = line.copy()
    fg_line = line.copy()

    bg_line.text = "".join([
        f"{LB}\\c&H000000&\\3c&H000000&\\blur{BLUR}{RB}",
        bg_line.text
    ])
    fg_line.text = "".join([
        f"{LB}\\c&HFFFFFF&\\blur{BLUR}\\bord0{RB}",
        fg_line.text
    ])

    io.write_line(bg_line)
    io.write_line(fg_line)

    if orgline_next and orgline_next.start_time - orgline.end_time > MAX_GAP_MS:
        last_line = [None for _ in range(VISIBLE_LINES)]



for line_mod in split_indexlines:
    line = line_mod['line']

io.save()
