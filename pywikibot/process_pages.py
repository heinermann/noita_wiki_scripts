import csv
import re

langs = ['en', 'zh', 'ja', 'tr']

def get_word_variations(word):
  result = {word}
  
  matches = re.findall(r"[_\-(]\w", word)
  for match in matches:
    i = word.index(match)
    for letter in [match[1:].lower(), match[1:].upper()]:
      for last_half in get_word_variations(word[i+2:]):
        result.add(word[:i+1] + letter + last_half)
  
  return result

def make_safe(s):
  return re.sub(r"([\(\)\'&])", r"\\\1", s)

def write_word_hints(f, word):
  variations = get_word_variations(word)

  for lang in langs:
    for variation in variations:
      f.write(f"-hint:{lang}:{make_safe(variation)} ")

def write_cmd(f, word, row):
    outfile.write(f"python pwb.py interwiki -initialredirect -noauto {make_safe(word)} ")
    write_word_hints(outfile, word)
    
    if row['zh']:
      outfile.write(f"-hint:zh:{make_safe(row['zh'])} ")
    if row['ja']:
      outfile.write(f"-hint:ja:{make_safe(row['ja'])} ")

    outfile.write("\n")


outfile = open('cmds.sh', 'w')
with open('common.csv') as csvfile:
  reader = csv.DictReader(csvfile)
  for row in reader:
    word=row['en']
    for w in get_word_variations(word):
      write_cmd(outfile, w, row)
      #write_cmd(outfile, f"{word} (Spell)", row)
      #write_cmd(outfile, f"{word} (Material)", row)

outfile.close()
