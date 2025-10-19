import os
import xml.etree.ElementTree as ET
import json

SONGS_WITHOUT_EXACTLY_TWO_CHORDS_PER_MEASURE = [
    'angel_eyes',
    'earth_angel',
    'georyboy',
    'love_shack'
]
MAXIMUM_NOTE_RESOLUTION_DENOMINATOR = 64


notesInCMajor = ['C', 'D', 'E', 'F', 'G', 'A', 'B'] 
chordKinds = [
    'major',
    'major-seventh',
    'major-ninth',
    'minor',
    'minor-seventh',
    'minor-ninth',
    'dominant',
    'dominant-ninth',
    'diminished',
    'diminished-seventh'
]


def getPositionInKey(note):
    """
    Returns the position of a note in the key of C major. If the note does not belong in the key of C major,
    we return an alter showing that it is an off-key note 
    
    :param note: The note to find the position of. In case of alters we are assuming only sharps to keep it simple.
    :return: The position of the note in the key with the optional alter.
    """
    
    
    if note in notesInCMajor:
        return (notesInCMajor.index(note) + 1, 0)
    else:
        # Handle off key notes. Any off key note will be considered as a sharp.
        return (notesInCMajor.index(note[0]) + 1, 1)
    
def encodeChordKind(kind):
    return chordKinds.index(kind) + 1


def getAlteredStep(step, alter):
    if alter == '1':
        return step + '#'
    else:
        return notesInCMajor[(notesInCMajor.index(step) - 1)%7] + '#'
    

def getNormalizedDuration(duration, divisions):
    """
    Returns the number of divisions this note covers in the measure considering the measure contains 64 divisions
    """

    fractionForBeat = duration/divisions
    fractionForMeasure = fractionForBeat/4
    normalizedFraction = int(fractionForMeasure*MAXIMUM_NOTE_RESOLUTION_DENOMINATOR)

    normalizedFraction = str(normalizedFraction)
    if len(normalizedFraction) == 1:
        normalizedFraction = '0' + normalizedFraction
    return normalizedFraction


def getEncodedNote(note, divisions):
    """
    Each note will be encoded as a 5 digit string:
    Digit-1: note position in the key.
    Digit-2: the alter, in case the note is off-key
    Digit-3: Octave
    Digits-(4,5): duration of the note. We will normalize all durations with a maximum resolution of 64th notes.
    So the value represented by the duration will be a fraction of 64. For eg: 32 means the note is 32/64 or a half note.
    """
    
    pitch = note.find('pitch')
    if pitch is not None:
        step = pitch.find('step').text
        octave = pitch.find('octave').text
        alter = pitch.find('alter')
        if alter is not None:
            step = getAlteredStep(step, alter.text)
        notePosition, alt = getPositionInKey(step)  
    else:
        rest = note.find('rest')
        if rest is not None:
            notePosition, alt = 0, 0
            octave = 0
        else:
            print("No pitch or rest found in note")
            return None

    durationElement = note.find('duration')
    if durationElement is not None:
        duration = int(durationElement.text)
        normalizedDuration = getNormalizedDuration(duration, divisions)
    else:
        print("No duration found in note")
        return None

    return f"{notePosition}{alt}{octave}{normalizedDuration}"


def getEncodedChord(harmony): 
    """
    Every chord will be encoded as a 3 digit string:
    Digit-1: chord root note relative to the key
    Digit-2: alter for the chord root note, in case the chord is off key
    Digit-3: kind - eg: major, minor, dominant etc

    We are not considering chord degrees as they would add too many variations
    and we have very little data to train on.
    """
    chordRoot = harmony.find('root')
    if chordRoot is None:
        print("No root chord found in harmony element")
        return None
    chordStep = chordRoot.find('root-step').text
    chordAlter = chordRoot.find('root-alter')
    if chordAlter is not None:
        chordStep = getAlteredStep(chordStep, chordAlter.text)
    chordPosition, alt = getPositionInKey(chordStep)
    chordKind = encodeChordKind(harmony.find('kind').text)

    return f"{chordPosition}{alt}{chordKind}"
    

def getSongData(root):
    """
    Parses the XML root element to extract relevant musical information.
    
    :param root: The root element of the XML tree.
    :return: A dictionary containing parsed data.
    """
    
    firstMeasure = root.find('part/measure')
    if firstMeasure is not None:
        divisions = int(firstMeasure.find('attributes/divisions').text)
        
    songData = []
    for measure in root.findall('part/measure'):
        if measure.get('number') == '1':
            continue

        notesInMeasure = []
        for note in measure.findall('note'):
            encodedNote = getEncodedNote(note, divisions)
            if encodedNote is not None:
                notesInMeasure.append(encodedNote)
            else:
                print("Error encoding note")

        chordsInMeasure = []
        for harmony in measure.findall('harmony'):
            encodedChord = getEncodedChord(harmony)
            if encodedChord is not None:
                chordsInMeasure.append(encodedChord)
            else:
                print("Error encoding chord")
        
        songData.append([notesInMeasure, chordsInMeasure])
    
    return songData
                    

def parse_file(filePath, songName):
    """
    Parses the given musicXML file into a pandas DataFrame.
    
    :param file_path: Path to the file to be parsed.
    :return: Content of the file as a string.
    """
    try:
        tree = ET.parse(filePath)
        root = tree.getroot()
        songData = getSongData(root)

        songDataDictionary = {
            "songName": songName,
            "songData": songData
        }
        with open("enchord_dataset.json", 'a') as f:
            json.dump(songDataDictionary, f)
            f.write(',\n')
    except Exception as e:
        print("Error when trying to parse song file: ", e.with_traceback())
    
def main():
    with open("enchord_dataset.json", 'w') as f:
        f.write('[')
    
    for dirpath, subdirs, files in os.walk('.'):
        songName = dirpath[2:]
        if songName in SONGS_WITHOUT_EXACTLY_TWO_CHORDS_PER_MEASURE:
            print("Skipping song: ", songName)
            continue
        for fileName in files:
            if fileName == 'c.xml':
                filePath = os.path.join(dirpath, fileName)
                parse_file(filePath, songName)
                print("Song ", songName, " parsed successfully.")
    
    with open("enchord_dataset.json", 'a') as f:
        f.write(']')
    
    print("Dataset generated")


if __name__ == "__main__":
    main() 


