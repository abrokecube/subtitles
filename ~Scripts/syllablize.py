# Example usage
# Powershell - Get content from text file "lyrics.txt" and output to lyrics_syl.txt
# get-content python.exe .\syllablize.py ".\lyrics.txt" > lyrics_syl.txt

import re
import sys
import os

# yoink and twist (https://nanodesu.moe/karaoke-timer/)
def syllablize(text, syllablize_level):
    def level1(lines):
        mono = ("ka|ki|ku|ke|ko|sa|shi|su|se|so|ta|chi|tsu|te|to|na|ni|nu|ne|no|ha|hi|fu|he|ho|ma|mi|mu|me|mo|mu|ya|yu|yo|ra|ri|ru|re|ro|wa|wo|ga|gi|gu|ge|go|za|ji|zu|ze|zo|da|de|do|ba|bi|bu|be|bo|pa|pi|pu|pe|po|kya|kyu|kyo|sha|shu|sho|cha|chu|cho|nya|nyu|nyo|hya|hyu|hyo|mya|myu|myo|rya|ryu|ryo|gya|gyu|gyo|ja|ju|jo|bya|byu|byo|pya|pyu|pyo")
        return [re.sub(r"((t?|s?|k?)(" + mono + "))", r"|\1", line, flags=re.IGNORECASE)
                .replace("k|k", "|kk")
                .replace("p|p", "|pp")
                .replace("t|t", "|tt")
                .replace("d|zu", "|dzu")
                for line in lines]

    def level2(lines):
        vowels = "a|i|u|e|o"
        return [re.sub(r"(" + vowels + r")(" + vowels + r")", r"\1|\2", line, flags=re.IGNORECASE)
                .replace(vowels + "n", r"\1|n")
                for line in lines]

    def cleanup(lines):
        out = []
        for line in lines:
            line = re.sub(r"\(\|", r"|(", line)
            line = re.sub(r"\"\|", r"|\"", line)
            line = re.sub(r" ([^| ])", r" |\1", line)
            line = line.lstrip("|")
            out.append(line)
        return out

    lines = text.split('\n')
    
    if syllablize_level >= 1:
        lines = level1(lines)
    if syllablize_level >= 2:
        lines = level2(lines)
    
    lines = cleanup(lines)
    return '\n'.join(lines)


SAVE_FILE = False
if __name__ == "__main__":
    file_in = False
    file_path = ""
    if len(sys.argv) > 1 and os.path.isfile(sys.argv[1]):
        file_in = True
        file_path = sys.argv[1]
        with open(sys.argv[1], 'r', encoding='utf-8') as file:
            text = file.read()
    else:
        text = sys.stdin.read()

    syllablize_level = 2
    result = syllablize(text, syllablize_level)

    if file_in and SAVE_FILE:
        file_path_out = os.path.split(file_path)[0] + "/lyrics_out.txt"
        with open(file_path_out, "w") as f:
            f.write(result)
        os.startfile(os.path.abspath(file_path_out),)

    print(result)