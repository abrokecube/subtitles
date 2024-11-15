
import clipboard
import ass_tag_parser  # modified https://github.com/bubblesub/ass_tag_parser/tree/master/ass_tag_parser

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
    input_line = input_lines.pop()
    line_type_and_layer, start_time_raw, end_time_raw, style, actor, _, _, _, effect, text = input_line.split(',',9)
    start_time = parse_time_to_seconds(start_time_raw)
    end_time = parse_time_to_seconds(end_time_raw)
    duration_ms = (end_time - start_time) * 1000

    if not multi_input:
        out_lines.clear()

    parse_success = False
    try:
        parsed = ass_tag_parser.parse_ass(text)
    except ass_tag_parser.ParseError:
        print("Parse error (this parser is janky with shapes)")
    else:
        parse_success = True

    if parse_success:
        result_tags = []
        # remove negative times
        for item in parsed:
            if type(item) is not ass_tag_parser.AssTagAnimation:
                result_tags.append(item)
                continue
            if item.time1 < 0 and item.time2 < 0:
                result_tags.extend(item.tags)
            elif item.time1 > duration_ms and item.time2 > duration_ms:
                pass
            else:
                result_tags.append(item)

        tag_filter = [
            ass_tag_parser.AssItem,
            ass_tag_parser.AssText,
            ass_tag_parser.AssTagAnimation,
        ]
        # cleanup tags pass 1
        result_tags2 = []
        tags_in_list = []
        for item in reversed(result_tags):
            if type(item) in tag_filter:
                result_tags2.append(item)
                if type(item) is ass_tag_parser.AssText:
                    tags_in_list.clear()
                continue

            if not type(item) in tags_in_list:
                tags_in_list.append(type(item))
                result_tags2.append(item)
                continue
        result_tags2.reverse()
        result_tags.clear()

        tag_filter = [
            ass_tag_parser.AssItem,
            ass_tag_parser.AssText,
            # ass_tag_parser.AssTagAnimation,
            ass_tag_parser.AssTagListOpening,
            ass_tag_parser.AssTagListEnding
        ]
        tags_in_list_index = {}
        # cleanup tags pass 2
        for item in result_tags2:
            if type(item) in tag_filter:
                result_tags.append(item)
                continue

            if type(item) == ass_tag_parser.AssTagAnimation:
                for tag in item.tags:
                    tags_in_list_index[type(tag)] = None
                result_tags.append(item)
            elif not type(item) in tags_in_list_index:
                tags_in_list_index[type(item)] = item.meta.text
                result_tags.append(item)
            elif tags_in_list_index[type(item)] != item.meta.text:
                result_tags.append(item)
                tags_in_list_index[type(item)] = item.meta.text
        result_tags2.clear()

        # move global tags to start of line
        global_tags = [
            ass_tag_parser.AssTagClipRectangle,
            ass_tag_parser.AssTagClipVector,
            ass_tag_parser.AssTagPosition,
            ass_tag_parser.AssTagRotationOrigin,
            ass_tag_parser.AssTagMove
        ]
        global_tags_list = {}
        for tag in result_tags:
            if type(tag) in global_tags:
                global_tags_list[type(tag)] = tag
            else:
                result_tags2.append(tag)
        result_tags2 = [global_tags_list[x] for x in global_tags_list] + result_tags2
        result_tags.clear()

        # remove trailing tags
        text_found = False
        for tag in reversed(result_tags2):
            if type(tag) == ass_tag_parser.AssText:
                if len(tag.text.strip()) > 0:
                    text_found = True
            if text_found:
                result_tags.append(tag)
            else:
                tags = [tag]                
                if type(tag) == ass_tag_parser.AssTagAnimation:
                    tags = tag.tags
                    for _tag in tags:
                        if type(_tag) in global_tags:
                            result_tags.append(tag)
                            break
        result_tags.reverse()
        result_tags2.clear()

        digits = 3
        # round items
        for tag in result_tags:
            _tags = [tag]
            if type(tag) == ass_tag_parser.AssTagAnimation:
                _tags = tag.tags

            for _tag in _tags:
                for key in _tag.__dict__:
                    if type(_tag.__dict__[key]) == float:
                        _tag.__dict__[key] = round(_tag.__dict__[key], digits)
            result_tags2.append(tag)
        result_tags.clear()

        out_text = ass_tag_parser.compose_ass(result_tags2)
    else:
        out_text = text
    out_line = f"{line_type_and_layer},{start_time_raw},{end_time_raw},{style},{actor},0,0,0,{effect},{out_text}"
    out_lines.append(out_line)
    
    if len(input_lines) == 0:
        print("\n".join(out_lines))
        clipboard.copy("\n".join(out_lines))
        out_lines.clear()
