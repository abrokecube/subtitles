funny scripts

## osu2kara.py
### Requirements
```
pip install slider
```
### See example usage in [Makeine OP - Tsuyogaru Girl](https://github.com/abrokecube/subtitles/tree/main/Makeine%20OP%20-%20Tsuyogaru%20Girl)

https://github.com/user-attachments/assets/f154ac0f-6492-420a-a436-4ea96857f841


Inline effects are used for karaoke flash colors and intensity
### Inline effects usage in ass:
Parse the added tags
```
code syl: function forMod(a) return syl.text:find("\\**" .. a) ~= null end; Norm=forMod('Norm'); Soft=forMod('Soft'); Drum=forMod('Drum'); Whistle=forMod('Whistle'); Finish=forMod('Finish'); Clap=forMod('Clap')
```
Then use 0x539 templater's if modifier
```
code syl if Finish: kara_flash='&H6594FD&'
```
