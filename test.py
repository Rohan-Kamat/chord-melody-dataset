import xml.etree.ElementTree as ET
import os

songsWithHarmonyDegree = 0
for dirpath, subdirs, files in os.walk('.'):
    for file in files:
        if file.endswith('c.xml'):
            root = ET.parse(os.path.join(dirpath, file))
            for measure in root.findall('part/measure'):
                if measure.get('number') == '1':
                    continue
                harmonyDegree = measure.find('harmony/degree')
                if harmonyDegree is not None:
                    songsWithHarmonyDegree += 1
                    break

print(songsWithHarmonyDegree)
