import clipboard

FRAMES = 3
FRAME_FRAMES = 3
FRAME_RATE = 24000/1001

TAGS_ONLY = False
MAX_LENGTH_MS = 20000

INVIS_TAG = "\\1a&HFF&\\3a&HFF&"
VIS_TAG = "\\1a&H00&\\3a&HCB&"

def ask_multiline(prompt):
    out = []
    print(f"{prompt} (multiline)")
    line_count = 0
    while True:
        if line_count == 0:
            in_text = input("> ")
        else:
            in_text = input(". ")
        line_count += 1
        if in_text == "":
            break
        else:
            out.append(in_text)
    return "\n".join(out)

def parse_time_to_seconds(time_str):
    time_parts = time_str.split(':')    
    hours = int(time_parts[0])
    minutes = int(time_parts[1])
    seconds = float(time_parts[2])
    
    total_seconds = hours * 3600 + minutes * 60 + seconds
    return total_seconds

input_lines = []
out_lines = []
multi_input = False
while True:
    if not TAGS_ONLY:
        if len(input_lines) == 0:
            input_line_input = ask_multiline("Enter dialogue line")
            input_lines.extend(reversed(input_line_input.split('\n')))
            multi_input = len(input_lines) > 1
        input_line = input_lines.pop()
        line_type, start_time_raw, end_time_raw, style, actor, _, _, _, _, text = input_line.split(',',9)
        start_time = parse_time_to_seconds(start_time_raw)
        end_time = parse_time_to_seconds(end_time_raw)

    # Dialogue: 0,0:00:26.67,0:00:35.29,English,fg,0,0,0,,{\c&HB3FFFF&\3c&HB3FFFF&\t(0,500,1.5,\c&H150E75&\3c&H2240BD&)\pos(65,50)\blur1.5\fad(0,300)}The smile you gave me, the tears you shed
    if not multi_input:
        out_lines.clear()

    for i in range(FRAMES):
        out = [INVIS_TAG]
        t = i * (1000/FRAME_RATE) * FRAME_FRAMES + (1000/FRAME_RATE/2)
        if TAGS_ONLY:
            t_end = MAX_LENGTH_MS
        else:
            t_end = (end_time - start_time) * 1000
        while t < t_end:
            start = int(round(t))
            end = int(round(t + (1000/FRAME_RATE)*FRAME_FRAMES))
            t += (1000/FRAME_RATE) * FRAMES * FRAME_FRAMES
            out.extend([
                f"\\t({start},{start+1},{VIS_TAG})",
                f"\\t({end},{end+1},{INVIS_TAG})"
            ])
        print("".join(out))
        if TAGS_ONLY:
            clipboard.copy("".join(out))
            input(f"Copied frame {i}, press enter to continue")
        else:
            a, b = text.split("{", 1)
            out.insert(0, a + "{")
            out.append(b)
            out_line = f"Dialogue: 0,{start_time_raw},{end_time_raw},{style},{actor},0,0,0,,{"".join(out)}"
            out_lines.append(out_line)
    if len(input_lines) == 0 and not TAGS_ONLY:
        print("\n".join(out_lines))
        clipboard.copy("\n".join(out_lines))
