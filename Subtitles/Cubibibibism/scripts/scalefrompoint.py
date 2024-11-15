import ass_tag_parser  # modified https://github.com/bubblesub/ass_tag_parser/tree/master/ass_tag_parser
import clipboard
import re

def ask(prompt, default="", validation = None):
    uuin = ""
    while True:
        if len(default) > 0:
            uin = input(f"{prompt}\n({default})\n> ")
            if len(uin) == 0:
                uuin = default
            else:
                uuin = uin.strip()
        else:
            uuin = input(f"{prompt}\n> ").strip()
        is_valid_input = True
        error_msg = ""
        if validation:
            v_res = validation(uuin)
            if v_res is None:
                is_valid_input = False
            elif type(v_res) == bool:
                if not v_res:
                    is_valid_input = False
            elif type(v_res) == str:
                is_valid_input = False
                error_msg = v_res
        if not is_valid_input:
            print(f"Invalid input. {error_msg}")
        else:
            return uuin
        
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

def cleanup_pass_1(tags):
    tag_filter = [
        ass_tag_parser.AssItem,
        ass_tag_parser.AssText,
        ass_tag_parser.AssTagAnimation,
    ]
    # cleanup tags pass 1
    result_tags = []
    tags_in_list = []
    for item in reversed(tags):
        if type(item) in tag_filter:
            result_tags.append(item)
            if type(item) is ass_tag_parser.AssText:
                tags_in_list.clear()
            continue

        if not type(item) in tags_in_list:
            tags_in_list.append(type(item))
            result_tags.append(item)
            continue

    result_tags.reverse()
    return result_tags

def cleanup_pass_2(tags):
    tag_filter = [
        ass_tag_parser.AssItem,
        ass_tag_parser.AssText,
        ass_tag_parser.AssTagListOpening,
        ass_tag_parser.AssTagListEnding
    ]
    result_tags = []
    tags_in_list_index = {}
    # cleanup tags pass 2
    for item in tags:
        if type(item) in tag_filter:
            result_tags.append(item)
            continue

        if type(item) == ass_tag_parser.AssTagAnimation:
            for tag in item.tags:
                tags_in_list_index[type(tag)] = None
            result_tags.append(item)
        elif not type(item) in tags_in_list_index:
            # tags_in_list_index[type(item)] = item.meta.text
            tags_in_list_index[type(item)] = str(item.__dict__)
            result_tags.append(item)
        # elif tags_in_list_index[type(item)] != item.meta.text:
        elif tags_in_list_index[type(item)] != str(item.__dict__):
            result_tags.append(item)
            # tags_in_list_index[type(item)] = item.meta.text
            tags_in_list_index[type(item)] = str(item.__dict__)

    return result_tags

def cleanup_pass_3(tags):
    # round numbers
    digits = 3
    result_tags = []
    for tag in tags:
        _tags = [tag]
        if type(tag) == ass_tag_parser.AssTagAnimation:
            _tags = tag.tags

        for _tag in _tags:
            for key in _tag.__dict__:
                if type(_tag.__dict__[key]) == float:
                    _tag.__dict__[key] = round(_tag.__dict__[key], digits)

        result_tags.append(tag)
    return result_tags

def cleanup_tags(tags):
    a = cleanup_pass_1(tags)
    a = cleanup_pass_2(a)
    a = cleanup_pass_3(a)
    return a


input_lines = []
out_lines = []
multi_input = False
scale_factor = 1
center_point = (960,540)
while True:
    if len(input_lines) == 0:
        input_line_input = ask_multiline("Enter dialogue line")
        if input_line_input.strip().lower() == 'paste':
            input_line_input = clipboard.paste()
        input_lines.extend(reversed(input_line_input.split('\n')))
        multi_input = len(input_lines) > 1

        user_input = ask("Scale factor (in percentage, where 100.0 = 1.0)", "100", lambda x: True if re.match(r"^-?\d+(\.\d+)?$", x) else "Not a number.")
        scale_factor = float(user_input) / 100
        valfunc = lambda x: True if re.match(r"^\s*-?\d+(\.\d+)?\s*,\s*-?\d+(\.\d+)?\s*$", x) else "Not in format x,y"
        user_input = ask("Center point (in format x,y)", validation=valfunc)
        m = re.match(r"^\s*(-?\d+(\.\d+)?)\s*,\s*(-?\d+(\.\d+)?)\s*$", user_input)
        num1, num2 = m.group(1), m.group(3)
        center_point = (float(num1) if '.' in num1 else int(num1),
                        float(num2) if '.' in num2 else int(num2))
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
        x, y = center_point
        result_tags = parsed.copy()
        out_tags = []

        asdf = [
            ass_tag_parser.AssTagFontXScale(100),
            ass_tag_parser.AssTagFontYScale(100),
        ]
        asdf.extend(result_tags)
        result_tags = asdf

        value_tags = (
            ass_tag_parser.AssTagFontXScale,
            ass_tag_parser.AssTagFontYScale,
            ass_tag_parser.AssTagBorder,
            ass_tag_parser.AssTagShadow
        )
        for tag in result_tags:
            tags = [tag]
            if type(tag) == ass_tag_parser.AssTagAnimation:
                tags = tag.tags

            for _tag in tags:
                if type(_tag) in value_tags:
                    for key in _tag.__dict__:
                        if key in ['value', 'size', 'scale']:
                            _tag.__dict__[key] *= scale_factor
                elif type(_tag) == ass_tag_parser.AssTagPosition:
                    _tag.x = ((_tag.x - x) * scale_factor) + x
                    _tag.y = ((_tag.y - y) * scale_factor) + y
                elif type(_tag) == ass_tag_parser.AssTagClipRectangle:
                    _tag.x1 = ((_tag.x1 - x) * scale_factor) + x
                    _tag.y1 = ((_tag.y1 - y) * scale_factor) + y
                    _tag.x2 = ((_tag.x2 - x) * scale_factor) + x
                    _tag.y2 = ((_tag.y2 - y) * scale_factor) + y

            out_tags.append(tag)
        result_tags = out_tags
        out_tags = []

        out_text = ass_tag_parser.compose_ass(cleanup_tags(result_tags))
    else:
        out_text = text

    out_line = f"{line_type_and_layer},{start_time_raw},{end_time_raw},{style},{actor},0,0,0,{effect},{out_text}"
    out_lines.append(out_line)
    
    if len(input_lines) == 0:
        print("\n".join(out_lines))
        clipboard.copy("\n".join(out_lines))
        out_lines.clear()
