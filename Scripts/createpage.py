import PIL.Image
import markdown
import os
import PIL
import glob
from colorama import Fore
import font_collector
import pathlib
import shutil
from datetime import datetime
import urllib.parse

from typing import Set
import argparse

INFO_FILE_NAME = "./readme.md"
FONT_FOLDER_PATH = "./fonts"
COMMON_FONTS_FOLDER = "D:\\Documents\\FontBase\\NekoCap"
COMMON_FONTS_URL_START = "https://github.com/abrokecube/subtitles-fonts/tree/main/NekoCap%20fonts"
DEFAULT_IMAGE_FOLDER = "C:\\Users\\abrokecube\\Pictures\\mpv"

parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument(
    "--no_copy_font", action='store_true',
    help="Don't copy fonts to folder"
)
args = parser.parse_args()

COPY_FONTS = not args.no_copy_font


class Font:
    def __init__(self, filename: str, font_name: str, font_path: str, is_common: bool) -> None:
        self.filename = filename
        self.font_name = font_name
        self.font_path = font_path
        self.is_common = is_common

    def __hash__(self) -> int:
        return hash(self.filename)
    
    def __eq__(self, other):
        return self.filename == other.filename


def ask(prompt, default=""):
    if len(default) > 0:
        uin =  input(f"{prompt}\n({default})\n> ")
        if len(uin) == 0:
            return default
        else:
            return uin.strip()
    else:
        return input(f"{prompt}\n> ").strip()

def ask_path(prompt, default='', start_path=None):
    path = ""
    while True:
        path = ask(prompt, default)
        if start_path and os.path.exists(os.path.join(start_path, path)):
            return os.path.join(start_path, path)
        if (not start_path) and os.path.exists(path):
            return path
        else:
            print("Not a valid path.")


def ask_directory(prompt, default="", validate_default=True):
    path = ""
    while True:
        path = ask(prompt, default)
        if os.path.isdir(path) or ((not validate_default) and path == default):
            return path
        else:
            print("Not a valid directory.")

def ask_file(prompt, default=""):
    file = ""
    while True:
        file = ask(prompt, default)
        if os.path.isfile(file):
            return file
        else:
            print("Not a valid file.")

def ask_yes_no(prompt, default: bool=None):
    while True:
        response = ask(f"{prompt} (y/n)", default='y' if default else 'n').strip().lower()
        if response == '' and default is not None:
            return default
        if response in ['y', 'yes']:
            return True
        elif response in ['n', 'no']:
            return False
        else:
            print("Please enter 'y' for yes or 'n' for no.")
    

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

def get_youtube_video_id(yt_url):
    return yt_url.split("watch?v=")[-1][:11]
    
def get_youtube_shorturl(yt_url):
    return f"https://youtu.be/{get_youtube_video_id(yt_url)}"

def get_nekocap_id(nekocap_url):
    return nekocap_url.split("view/")[-1][:10]

def get_youtube_nekocap_ref(yt_url, nekocap_url):
    return f"https://www.youtube.com/watch?v={get_youtube_video_id(yt_url)}&nekocap={get_nekocap_id(nekocap_url)}"

def get_all_files(directory, glob_="*"):
    return [str(file) for file in pathlib.Path(directory).rglob(glob_) if file.is_file()]

SUBTITLE_FOLDER = ask_directory("Input/Output folder path. Should have at least one .ass file", "./")
FONT_FOLDER = os.path.join(SUBTITLE_FOLDER, FONT_FOLDER_PATH)
EXTERNAL_FONT_FOLDER = ask_directory("External fonts:", "", False)
ext_fonts_scan_subdirs = False
if EXTERNAL_FONT_FOLDER:
    ext_fonts_scan_subdirs = ask_yes_no("Scan subdirectories for fonts?", False)
common_fonts = []
for file in glob.glob(os.path.join(COMMON_FONTS_FOLDER, "*.*")):
    common_fonts.append(os.path.basename(file).lower())

FONT_LISTING: Set[Font] = set()

font_coll_strat = font_collector.FontSelectionStrategyLibass()
add_fonts = font_collector.FontLoader.load_additional_fonts([pathlib.Path(COMMON_FONTS_FOLDER),], ext_fonts_scan_subdirs)
common_font_collection = font_collector.FontCollection(additional_fonts=add_fonts, use_system_font=False)
if EXTERNAL_FONT_FOLDER:
    extfonts = font_collector.FontLoader.load_additional_fonts([pathlib.Path(EXTERNAL_FONT_FOLDER),])
    system_font_collection = font_collector.FontCollection(additional_fonts=extfonts)
else:
    system_font_collection = font_collector.FontCollection()
num_missing_fonts = 0
sub_file_count = 0
font_results = []
for file in get_all_files(SUBTITLE_FOLDER, "*.ass"):
    sub_file_count += 1
    print(f"{Fore.LIGHTCYAN_EX}Subtitle file: {file}{Fore.RESET}")
    subtitle = font_collector.AssDocument.from_file(pathlib.Path(file))
    used_styles = subtitle.get_used_style()

    for style, usage_data in used_styles.items():
        font_result = common_font_collection.get_used_font_by_style(style, font_coll_strat)
        if font_result is None:
            font_result = system_font_collection.get_used_font_by_style(style, font_coll_strat)
        if font_result is None:
            num_missing_fonts += 1
            print(f'{Fore.RED}Could not find font {style.fontname}!{Fore.RESET}')
        else:
            print(f'{Fore.GREEN}Found font {style.fontname} ({style.weight}{" Italic" if style.italic else ""}){Fore.RESET}')
            font_results.append(font_result)

            if font_result.need_faux_bold:
                print(f"{Fore.YELLOW}Faux bold used for '{style.fontname}'.{Fore.RESET}")
            elif font_result.mismatch_bold:
                print(f"{Fore.YELLOW}'{style.fontname}' does not have a bold variant.{Fore.RESET}")
            if font_result.mismatch_italic:
                print(f"{Fore.YELLOW}'{style.fontname}' does not have an italic variant.{Fore.RESET}")

if sub_file_count > 0:
    if num_missing_fonts == 1:
        print(f"{Fore.RED}1 font was not found!{Fore.RESET}")
    elif num_missing_fonts > 1:
        print(f"{Fore.RED}{num_missing_fonts} fonts were not found!{Fore.RESET}")
    else:
        print(f"{Fore.GREEN}All fonts were found!{Fore.RESET}")
else:
    print(f"{Fore.RED}No subtitles were found!{Fore.RESET}")

fonts_file_found: Set[font_collector.FontFile] = set()

for font_result in font_results:
    if font_result.font_face.font_file is None:
        print('yikes')
    fonts_file_found.add(font_result.font_face.font_file)

for font in fonts_file_found:
    font_filename = os.path.join(FONT_FOLDER, font.filename.resolve().name)
    base_name = font.filename.name.lower()

    # i want my capitalization back
    files = os.listdir(font.filename.parent)
    for file in files:
        if file.lower() == base_name.lower():
            base_name = file
            break

    if base_name.lower() in common_fonts:
        gh_path = os.path.join(COMMON_FONTS_URL_START, urllib.parse.quote(base_name)).replace("\\", "/")
        is_common = True
        print(f"{base_name} is a common font")
    else:
        gh_path = os.path.join(FONT_FOLDER_PATH, urllib.parse.quote(base_name)).replace("\\", "/")
        is_common = False
        if COPY_FONTS:
            if not os.path.isdir(FONT_FOLDER):
                os.mkdir(FONT_FOLDER)
            if not os.path.isfile(font_filename):
                shutil.copy(font.filename, font_filename)
    FONT_LISTING.add(Font(
        base_name,
        font.font_faces[0].get_best_exact_name().value,
        gh_path,
        is_common
    ))
            
md_font_table_rows = [
    "| Filename | Font name | NekoCap font? |",
    "| ---- | ---- | :--: |"
]
for font in sorted(FONT_LISTING, key=lambda x: x.filename.lower()):
    md_font_table_rows.append(
        f" [`{font.filename}`]({font.font_path}) | {font.font_name} | {'✔️' if font.is_common else '❌'} |"
    )
MD_FONT_TABLE = "\n".join(md_font_table_rows)

md_folder_table_rows = [
    "| File | Description |",
    "| ---- | ----------- |"
]
def folder_sort_key(x):
    is_ass = 'ass' in os.path.splitext(x)[-1]
    if is_ass:
        return x
    else:
        return "~" + x
for file in sorted(get_all_files(SUBTITLE_FOLDER), key=folder_sort_key):
    print(file)
    print(os.path.join(SUBTITLE_FOLDER, FONT_FOLDER_PATH))
    if not os.path.isfile(file):
        continue
    elif os.path.abspath(os.path.join(SUBTITLE_FOLDER, FONT_FOLDER_PATH)) in file:
        continue
    elif "preview.webp" in file:
        continue
    elif "readme" in file:
        continue
    else:
        path = os.path.relpath(file, SUBTITLE_FOLDER).replace("\\", "/")
        desc = ask(f"{Fore.LIGHTYELLOW_EX}Description for file {path}?{Fore.RESET}", "Subtitle file")
        md_folder_table_rows.append(
            f"[`{path}`]({urllib.parse.quote(path, safe=":/")}) | {desc} |"
        )
MD_FILE_TABLE = "\n".join(md_folder_table_rows)

TITLE = ask("Title?", os.path.split(SUBTITLE_FOLDER)[-1])
YOUTUBE = ask("YouTube link?")
if "&nekocap" in YOUTUBE:
    nekocap_id = YOUTUBE.split("&nekocap=", 1)[-1][:10]
    NEKOCAP = "https://nekocap.com/view/" + nekocap_id
else:
    NEKOCAP = ask("NekoCap link?")
NEKOCAP_YOUTUBE_REF = get_youtube_nekocap_ref(YOUTUBE, NEKOCAP)
YOUTUBE_SHORTURL = get_youtube_shorturl(YOUTUBE)
PREVIEW_IMG = ask_path("Path to preview image. If input is a folder, gets most recent image file", DEFAULT_IMAGE_FOLDER, SUBTITLE_FOLDER)

SUB_CREDITS = ask_multiline("Subtitle credits. (Splits at first ':' each line)")

sub_credits_lines = [
    "<table align='center'>"
]
for credit_line in SUB_CREDITS.splitlines():
    title, info = credit_line.split(":", 1)
    sub_credits_lines.append('    <tr>')
    sub_credits_lines.append(
        f"        <!-- {title} -->"
    )
    sub_credits_lines.append(
        f"        <td><b>{markdown.markdown(title.strip())[3:-4]}</b></td>"
    )
    sub_credits_lines.append(
        f"        <!-- {info} -->"
    )
    sub_credits_lines.append(
        f"        <td>{markdown.markdown(info.strip())[3:-4]}</td>"
    )

    sub_credits_lines.append('    </tr>')

sub_credits_lines.append('</table>')

HTML_SUB_CREDITS = "\n".join(sub_credits_lines)

while True:
    cdate_user_in = ask("Creation date in YYYY-MM-DD", "now")
    if cdate_user_in.lower() == "now":
        create_date_obj = datetime.now()
        break
    try:
        create_date_obj = datetime.strptime(cdate_user_in, "%Y-%m-%d")
        break
    except ValueError:
        print("Please try again.")

if cdate_user_in.lower() != "now":
    while True:
        mdate_user_in = ask("Last modification date in YYYY-MM-DD", "now")
        if mdate_user_in.lower() == "now":
            mod_date_obj = datetime.now()
            break
        try:
            mod_date_obj = datetime.strptime(mdate_user_in, "%Y-%m-%d")
            break
        except ValueError:
            print("Please try again.")
else:
    mod_date_obj = datetime.now()

F_CREATE_DATE = create_date_obj.strftime("%B %d, %Y")
F_MOD_DATE = mod_date_obj.strftime("%B %d, %Y")

output = f"""
<h1 align='center'>{TITLE}</h1>

<table align='center'>
    <tr>
        <td> <img src='../.img/youtube.svg' alt='YouTube' width=27 align='center'> &nbsp {YOUTUBE_SHORTURL} </td>
        <td> <img src='../.img/nekocap.svg' alt='NekoCap' width=23 align='center'> &nbsp {NEKOCAP} </td>
    </tr>
</table>

[![](./preview.webp)]({NEKOCAP_YOUTUBE_REF})

{HTML_SUB_CREDITS}

**Uploaded:** {F_CREATE_DATE}  
**Last updated:** {F_MOD_DATE}

<!-- Description goes here -->

## Folder info

{MD_FILE_TABLE}

## Font list

{MD_FONT_TABLE}

<!-- Permissions -->
## 
You are free to use these subtitles for whatever purpose. Please retain any credits listed in the subs. Credit to me is not required, but is appriciated.
"""

image_file_path = ""
if os.path.isdir(PREVIEW_IMG):
    files = []
    for file_type in ["*.png", "*.jpg", "*.jpeg", "*.webp"]:
        files.extend(glob.glob(os.path.join(PREVIEW_IMG, file_type)))
    if files:
        image_file_path = max(files, key=os.path.getmtime)
    else:
        exit()
        print('No image!')
elif os.path.isfile(PREVIEW_IMG):
    image_file_path = PREVIEW_IMG

img_pil = PIL.Image.open(image_file_path)
img_pil.save(os.path.join(SUBTITLE_FOLDER, "./preview.webp"), "WEBP", quality=90)

info_out_path = os.path.join(SUBTITLE_FOLDER, INFO_FILE_NAME)
if os.path.isfile(info_out_path):
    answer = ask_yes_no("A readme already exists on this folder! Overwrite?", False)
    if not answer:
        old_i = INFO_FILE_NAME
        head, ext = os.path.splitext(old_i)
        idx = 1
        while os.path.isfile(os.path.join(SUBTITLE_FOLDER,f"{head} ({idx}){ext}")):
            idx += 1
        INFO_FILE_NAME = f"{head} ({idx}){ext}"
        
with open(os.path.join(SUBTITLE_FOLDER, INFO_FILE_NAME), 'w', encoding='utf-8') as f:
    f.write(output)
