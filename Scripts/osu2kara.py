# REQUIREMENTS
# pip install slider

# HOW TO USE
# Create an osu beatmap timed to the lyrics
# New combos (new color) will skip to the next line
# Script will only read the first difficulty it sees
# A slider on the last syllable of a line will set the line's end time

# Help text:
# usage: osu2kara [-h] [--style STYLE] [--no_combo_split] beatmap_path lyrics_path

# Use an osu! beatmap for k-timing

# positional arguments:
#   beatmap_path      Path to beatmap file. Accepts .osu and .osz files. Script will only read the first difficulty it sees.
#   lyrics_path       Path to a text file containing lyrics with syllables split with '|' character

# options:
#   -h, --help        show this help message and exit
#   --style STYLE     Style of output lines (default: Romanji)
#   --no_combo_split  Don't skip to the next line when a new combo starts (default: False)

# Output is printed onto the console


HITSOUNDS_AS_INLINE_FX = True
KF_ON_SLIDER = False
SLIDER_TO_END_TIME = False

import argparse
parser = argparse.ArgumentParser(
    prog="osu2kara",
    description="Use an osu! beatmap for k-timing",
    epilog="Output is printed onto the console",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)
parser.add_argument(
    "beatmap_path",
    help='Path to beatmap file. Accepts .osu and .osz files. Script will only read the first difficulty it sees.'
)
parser.add_argument(
    "lyrics_path",
    help='Path to a text file containing lyrics with syllables split with \'|\' character'
)
parser.add_argument(
    "--style", default="Romanji", help="Style name of output lines"
)
parser.add_argument(
    "--no_combo_split", action='store_true',
    help="Don't skip to the next line when a new combo starts"
)
# args = parser.parse_args([
#     r"D:\Documents\nekocap\Makeine ED - LOVE2000\love2000.osz",
#     r"D:\Documents\nekocap\Makeine ED - LOVE2000\lyrics_out.txt",
# ])
args = parser.parse_args()

import datetime
import os
import slider  # might write my own parser idk

def to_ass_time(delta: datetime.timedelta):
    hours = delta.seconds // (60*60)
    minutes = (delta.seconds // 60) % 60
    seconds = delta.seconds % 60
    centiseconds = delta.microseconds // 10000
    return '{:02}:{:02}:{:02}.{:02}'.format(hours, minutes, seconds, centiseconds)

def make_dialogue_line(t1, t2, text):
    t1 = to_ass_time(t1)
    t2 = to_ass_time(t2)
    result = f"Dialogue: 0,{t1},{t2},{args.style},,0,0,0,,{text}"
    return result

def read_bitflags(value, flag_values):
    set_flags = []
    for flag_name, flag_value in flag_values.items():
        if value & flag_value:
            set_flags.append(flag_name)
    return set_flags

def beatmap2kara(beatmap: slider.Beatmap, lyrics):    
    lines = []
    for line in lyrics.splitlines():
        if len(line.strip()) > 0:
            lines.append(list(reversed(line.strip().split("|"))))
    lines.reverse()

    output = []

    hit_objects = beatmap.hit_objects(circles=True, sliders=True,  spinners=False, stacking=False)
    line_start_t: datetime.timedelta = None
    ass_line_text = ""
    has_missing_syllables = False
    has_additional_syllables = False
    line_duration = 0
    line_duration_rounded_cs = 0
    for idx, hit_object in enumerate(hit_objects):
        if len(lines) == 0:
            has_missing_syllables = True
            break
        if not line_start_t:
            line_start_t = hit_object.time
        if idx < len(hit_objects) - 1:
            next_object = hit_objects[idx+1]
            end_time = next_object.time
        else:
            end_time = hit_object.time + datetime.timedelta(milliseconds=1000)
            next_object = slider.Circle((0,0), end_time, 0, new_combo=True)
            if SLIDER_TO_END_TIME and type(hit_object) == slider.Slider:
                end_time = hit_object.end_time
        syllable = lines[-1].pop()
        line_finished = len(lines[-1]) == 0            

        kara = 'k'
        inline_fx = ""
        if type(hit_object) == slider.Slider:
            if KF_ON_SLIDER:
                kara = 'kf'
            if line_finished:
                end_time = hit_object.end_time
        
        addition_spl = hit_object.addition.split(":")
        if HITSOUNDS_AS_INLINE_FX:
            inline_fx = "\\**%s" % ('A', 'N', 'S', 'D')[int(addition_spl[0])]
            if hit_object.hitsound > 0:
                inline_fx += "\\**"+"\\**".join(read_bitflags(hit_object.hitsound, {'No':1, 'Wh':2, 'Fi':4, 'Cl':8}))

        duration = end_time - hit_object.time
        line_duration += (duration.seconds + duration.microseconds/1000000)
        new_line_duration_cs = int(line_duration * 100)
        duration_cs = new_line_duration_cs - line_duration_rounded_cs
        ass_line_text += "{\\%s%s%s}%s" % (kara, int(round(duration_cs)), inline_fx, syllable)
        line_duration_rounded_cs = new_line_duration_cs
        
        if (not args.no_combo_split):
            if next_object.new_combo:
                while len(lines[-1]) > 0:
                    ass_line_text += "{\\k0}%s*" % lines[-1].pop()
                    has_additional_syllables = True
                line_finished = True
            if line_finished:
                if (not next_object.new_combo) and len(lines)>1:
                    lines[-1].append('_')
                    has_missing_syllables = True
                elif next_object.new_combo:
                    lines.pop()
                    output.append(make_dialogue_line(line_start_t, end_time, ass_line_text))
                    line_start_t = None
                    ass_line_text = ""
        elif line_finished:
            lines.pop()
            output.append(make_dialogue_line(line_start_t, end_time, ass_line_text))
            line_start_t = None
            ass_line_text = ""
            line_duration = 0
            line_duration_rounded_cs = 0

    if len(ass_line_text) > 0:
        output.append(make_dialogue_line(line_start_t, end_time, ass_line_text))
    if len(lines) > 0:
        for line in reversed(lines):
            output.append("".join(reversed(line)))
        output.append("File has extra lines!")
    if has_missing_syllables:
        output.append("File has missing syllables! (marked with _)")
    if has_additional_syllables:
        output.append("File has extra syllables! (marked with *)")
    return "\n".join(output)


def osz2kara(osz_file_path, lyrics):
    beatmap = slider.Beatmap.from_osz_path(osz_file_path)
    for bmap in beatmap:
        return beatmap2kara(beatmap[bmap], lyrics)


def osu2kara(osu_file_path, lyrics):
    try:
        beatmap = slider.Beatmap.from_path(osu_file_path)
    except ValueError:
        print("Please export your beatmap as a .osz (this beatmap parser is bugged im sorry)")
        exit()
    return beatmap2kara(beatmap, lyrics)


def main():
    lyrics_path = args.lyrics_path
    if not os.path.exists(lyrics_path):
        print("Lyrics file not found! Exiting...")
        exit()
    with open(lyrics_path, 'r') as f:
        lyrics = f.read()
    if not "|" in lyrics:
        print("File contains no syllables! Split syllables by inserting the pipe (|) character. \nExample: Se|ka|i |de |i|chi|ban |o|hi|me-|sa|ma")
        exit()
    beatmap_path = args.beatmap_path
    if not os.path.exists(beatmap_path):
        print("Beatmap file not found! Exiting...")
        exit()
    bm_ext = os.path.splitext(beatmap_path)[1]
    if "osu" in bm_ext:
        # Raw osu! beatmap difficulty
        ass_dialogue = osu2kara(beatmap_path, lyrics)
    elif "osz" in bm_ext:
        # osu! beatmap
        ass_dialogue = osz2kara(beatmap_path, lyrics)
    elif "olz" in bm_ext:
        # osu!lazer beatmap
        print(".olz files are not supported! Please export your beatmap as an .osz file.")
        exit()
    else:
        print("Only .osu and .osz files are accepted!")
        exit()

    print(ass_dialogue)

main()