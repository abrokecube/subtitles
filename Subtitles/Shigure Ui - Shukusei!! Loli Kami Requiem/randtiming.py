# Shuffles event timings
# Tags are linked to event time (does not include inline tags)

import clipboard
import random

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

# Dialogue: 0,0:00:00.60,0:00:03.77,Sign,a,0,0,0,fx,{\fsp-7.00\t(0,83,0.93,\fsp-4.90)\t(83,166,0.93,\fsp-3.17)\t(166,249,0.93,\fsp-1.74)\t(249,332,0.93,\fsp-0.56)\t(332,415,0.93,\fsp0.41)\t(415,498,0.93,\fsp1.21)\t(498,582,0.93,\fsp1.87)\t(582,665,0.93,\fsp2.42)\t(665,748,0.93,\fsp2.87)\t(748,831,0.93,\fsp3.24)\t(831,914,0.93,\fsp3.55)\t(914,997,0.93,\fsp3.80)\t(997,1081,0.93,\fsp4.01)\t(1081,1164,0.93,\fsp4.19)\t(1164,1247,0.93,\fsp4.33)\t(1247,1330,0.93,\fsp4.45)\t(1330,1413,0.93,\fsp4.54)\t(1413,1496,0.93,\fsp4.62)\t(1496,1580,0.93,\fsp4.69)\t(1580,1663,0.93,\fsp4.74)\t(1663,1746,0.93,\fsp4.79)\t(1746,1829,0.93,\fsp4.82)\t(1829,1912,0.93,\fsp4.86)\t(1912,1995,0.93,\fsp4.88)\t(1995,2079,0.93,\fsp4.90)\t(2079,2162,0.93,\fsp4.92)\t(2162,2245,0.93,\fsp4.93)\t(2245,2328,0.93,\fsp4.94)\t(2328,2411,0.93,\fsp4.95)\t(2411,2494,0.93,\fsp4.96)\t(2494,2578,0.93,\fsp4.97)\t(2578,2661,0.93,\fsp4.97)\t(2661,2744,0.93,\fsp4.98)\t(2744,2827,0.93,\fsp4.98)\t(2827,2910,0.93,\fsp4.99)\t(2910,2993,0.93,\fsp4.99)\t(2993,3000,7.14,\fsp5.00)\fs100\fad(150,150)\c&HE2E9EF&\pos(960,662)}Lonely, the loli-loli god descends

input_lines = []
out_lines = []

multi_input = False
while True:
    if len(input_lines) == 0:
        input_line_input = ask_multiline("Enter dialogue line")
        if input_line_input.strip().lower() == 'paste':
            input_line_input = clipboard.paste()
        input_lines.extend(reversed(input_line_input.split('\n')))
        multi_input = len(input_lines) > 1

    if not multi_input:
        out_lines.clear()
    
    text_indeces = list(range(len(input_lines)))
    time_indeces = list(range(len(input_lines)))
    # random.seed(239847)
    random.shuffle(text_indeces)
    random.shuffle(time_indeces)

    for i in range(len(input_lines)):
        text_line = input_lines[text_indeces.pop()]
        time_line = input_lines[time_indeces.pop()]
        line_type_and_layer, _, _, style, actor, _, _, _, effect, text = text_line.split(',',9)
        _, start_time_raw, end_time_raw, _, _, _, _, _, _, t_text = time_line.split(',',9)
        if text.strip()[0] == "{" and t_text.strip()[0] == "{":
            tags = t_text.split("}",1)[0].lstrip("{")
            mod_text = text.split("}",1)[-1]
            out_text = "{" + tags + "}" + mod_text
        else:
            out_text = text

        out_line = f"{line_type_and_layer},{start_time_raw},{end_time_raw},{style},{actor},0,0,0,{effect},{out_text}"
        out_lines.append(out_line)
    input_lines.clear()
            
    if len(input_lines) == 0:
        print("\n".join(out_lines))
        clipboard.copy("\n".join(out_lines))
        out_lines.clear()

