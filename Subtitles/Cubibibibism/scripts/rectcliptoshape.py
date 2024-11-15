
import ass_tag_parser  # modified https://github.com/bubblesub/ass_tag_parser/tree/master/ass_tag_parser
import clipboard

# shapery macros > shape clipper
# shapery macros > shape to clip
# non-gui-macros > HR vector to rect clip
# then paste lines into prompt
PADDING = 5

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
    input_line = input_lines.pop()
    line_type_and_layer, start_time_raw, end_time_raw, style, actor, _, _, _, effect, text = input_line.split(',',9)


    parse_success = False
    try:
        parsed = ass_tag_parser.parse_ass(text)
    except ass_tag_parser.ParseError:
        print("Parse error (this parser is janky with shapes)")
    else:
        parse_success = True

    if parse_success:
        result_tags = [ass_tag_parser.AssTagAlignment(7)]
        new_text = ""
        for tag in parsed:
            if type(tag) == ass_tag_parser.AssTagClipRectangle:
                if tag.x1 > tag.x2:
                    a = tag.x2
                    tag.x2 = tag.x1
                    tag.x1 = a
                if tag.y1 > tag.y2:
                    a = tag.y2
                    tag.y2 = tag.y1
                    tag.y1 = a
                new_text = f"m {tag.x1 - PADDING} {tag.y1 - PADDING} l {tag.x2 + PADDING} {tag.y1 - PADDING} {tag.x2 + PADDING} {tag.y2 + PADDING} {tag.x1 - PADDING} {tag.y2 + PADDING}"
            elif type(tag) == ass_tag_parser.AssText:
                if len(new_text) > 0:
                    tag.text = new_text
            elif type(tag) == ass_tag_parser.AssTagPosition:
                tag.x = 0
                tag.y = 0
            elif type(tag) == ass_tag_parser.AssTagAlignment:
                continue
            elif type(tag) in (ass_tag_parser.AssTagFontXScale, ass_tag_parser.AssTagFontYScale):
                continue
            result_tags.append(tag)

        out_text = ass_tag_parser.compose_ass(result_tags)
    else:
        out_text = text

    out_line = f"{line_type_and_layer},{start_time_raw},{end_time_raw},{style},{actor},0,0,0,{effect},{out_text}"
    out_lines.append(out_line)
    
    if len(input_lines) == 0:
        print("\n".join(out_lines))
        clipboard.copy("\n".join(out_lines))
        out_lines.clear()
