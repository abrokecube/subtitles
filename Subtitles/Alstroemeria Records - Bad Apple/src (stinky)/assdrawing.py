from ass_tag_parser import draw_parser, draw_composer
class ASSDrawing:
    def __init__(self) -> None:
        self.parts = []

    def append_part(self, command, *params):
        rounded_params = []
        for p in params:
            rounded_params.append(str(int(round(p,0))))

        self.parts.append({
            "command": command.lower(),
            "parameters": list(params)
        })

    def append_move(self, x,y):
        self.append_part("m", x,y)
    
    def append_line(self, x,y):
        self.append_part('l', x,y)
    
    def append_bezier(self, x1,y1, x2,y2, x3,y3):
        self.append_part('b', x1,y1, x2,y2, x3,y3)

    def translate(self, x, y):
        for part in self.parts:
            for i in range(len(part['parameters'])):
                if i % 2 == 0:
                    part['parameters'][i] += x
                else:
                    part['parameters'][i] += y
        return self

    def scale(self, scale):
        for part in self.parts:
            for i in range(len(part['parameters'])):
                part['parameters'][i] *= scale
        return self

    def get_string(self):
        last_command = ""

        str_parts = []
        for part in self.parts:
            params = part['parameters']
            command = part['command']

            rounded_params = []
            for p in params:
                rounded_params.append(str(int(round(p,0))))

            if command.lower() == last_command:
                str_parts.append(" ".join(rounded_params))
            else:
                str_parts.append(f"{command} {" ".join(rounded_params)}")
            last_command = command.lower()

        return " ".join(str_parts)
    
    def get_clip(self):
        return "\\clip(%s)" % (self.get_string())
    
    def get_iclip(self):
        return "\\iclip(%s)" % (self.get_string())
    
    def get_drawing(self):
        return "{\\p1}%s" % (self.get_string())
    
    def get_tag_parser_drawing(self):
        last_command = ""

        parts = []
        for part in self.parts:
            params = part['parameters']
            command = part['command']

            rounded_params = []
            for p in params:
                rounded_params.append(str(int(round(p,0))))

            last_command = command.lower()

            points = []
            for i in range(0,len(params)//2,2):
                points.append(draw_parser.AssDrawPoint(*params[i:i+2]))
            if last_command == "m":
                parts.append(draw_parser.AssDrawCmdMove(*points, True))
            elif last_command == "l":
                parts.append(draw_parser.AssDrawCmdLine(*points))
            elif last_command == "b":
                parts.append(draw_parser.AssDrawCmdBezier(points))

        return draw_composer.compose_draw_commands(parts)

    def is_empty(self):
        return len(self.parts) == 0