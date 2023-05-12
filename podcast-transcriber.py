import os
import whisper
import sys
import re
import heapq

# Audacity piping setup
TONAME = '/tmp/audacity_script_pipe.to.' + str(os.getuid())
FROMNAME = '/tmp/audacity_script_pipe.from.' + str(os.getuid())

TOFILE = open(TONAME, 'w')
FROMFILE = open(FROMNAME, 'rt')
EOL = '\n'

def send_command(command):
    """Send a single command."""
    print("Send: >>> "+command)
    TOFILE.write(command + EOL)
    TOFILE.flush()

def get_response():
    """Return the command response."""
    result = ''
    line = ''
    while True:
        if line == '\n' and len(result) > 0:
            break
        result += line
        line = FROMFILE.readline()
    return result

def do_command(command):
    """Send one command, and return the response."""
    send_command(command)
    response = get_response()
    print("Rcvd: <<< " + response)
    return response

# Priority Queue / Heap Setup
# function to load speaker files in sequence (which is based on timestamp)
def read_numbers_from_file(file_path):
    with open(file_path, 'r') as file:
        for line in file:
            number = float(line.split('\t')[0])
            speaker = line.split('\t')[2]
            yield number, speaker # This should yield a tuple?

# Switch to episode folder and generate a list of sorted files
episode_folder = sys.argv[1]
os.chdir(os.getcwd() + "/" + episode_folder)
file_list = sorted(os.listdir(os.getcwd()))

speakers = []

# first argument is the episode folder, subsequent arguments are the speaker(s)
if len(sys.argv) > 3: 
    for arg in range(2, len(sys.argv)):
        speakers.append(sys.argv[arg])
elif len(sys.argv) == 3:
    speakers.append(sys.argv[2])


# Load audio and generate labels for each file, then split audio files based on label
datapath = os.getcwd() + "/" + "data"
if os.path.exists(datapath) == False:
    os.mkdir(datapath)

for speaker in speakers:
    # lazy check - if there are label files already, skip right to the transcription portion
    # otherwise, loads them into Audacity and labels the sounds
    if os.path.isfile(datapath + "/" + speaker + "-Labels.txt") == False:
        speaker_filecount = 0
        for file in file_list:
            print(file)
            if (speaker in file) and (".wav" in file):
                do_command(f'Import2: Filename={os.getcwd() + "/" + file}')
                speaker_filecount += 1

        if speaker_filecount > 1:
            do_command('SelectAll')
            do_command('Align_EndToEnd')
            do_command('MixAndRender')

        do_command('SelectAll')
        do_command(f'LabelSounds: threshold=-25 sil-dur=0.4 text="{speaker} ###1"')
        do_command('ExportLabels')
        do_command('ExportMultiple')
        do_command('SelectAll')
        do_command('TrackClose')
        do_command('SelectAll')
        do_command('TrackClose')

# List of common slips or phrases the model picks up in error
phrases = [
    "Thank you for watching",
    "Thanks for watching",
    "Bye",
    "Thanks for listening",
    "Thank you for listening",
    "You",
    "you",
    "Good job",
    "Well be right back",
    "Thank you",
    "Thank you bye",
    "Thank you Thanks everybody",
    "Thank you Thanks everyone",
    "Stop"
]

model = whisper.load_model("medium.en")
blanklines = 0
os.chdir(datapath)

with open(f'df-{sys.argv[1]}.txt', 'w') as podcast:
    previous_line = ""
    previous_speaker = ""
    current_speaker = ""
    previous_timestamp = 0

    file_generators = [(read_numbers_from_file(speaker + "-Labels.txt")) for speaker in speakers]

    # Initialize min-heap with first audio snippet of each speaker
    min_heap = []
    for idx, (file_gen) in enumerate(file_generators):
        timestamp = next(file_gen, None)
        if timestamp is not None:
            heapq.heappush(min_heap, (timestamp, idx))

    # load/transcribe the earliest audio snippet based on timestamp, advance speaker to next file, repeat
    # why not just load them all into a list instead of this heap queue nonsense? cause it was worth learning, that's why
    while min_heap:
        timestamp, idx = heapq.heappop(min_heap)
        current_speaker = timestamp[1].split()[0]
        if os.path.isfile(datapath + "/" + timestamp[1].strip() + ".wav"):
            speech = whisper.load_audio(datapath + "/" + timestamp[1].strip() + ".wav")
            speech = whisper.pad_or_trim(speech)
            result = model.transcribe(speech)

            alphanum_result = re.sub(r'[^\w\s]', '', result["text"].strip())

            if (result["text"] != "") and alphanum_result not in phrases:
                line = result["text"].strip()
                print(f"{timestamp[0]} : {current_speaker}: {line}")

                # speaker detection and formatting
                if previous_speaker == "":
                    podcast.write(current_speaker + ": " + line)
                elif current_speaker == previous_speaker:
                    if (line[0].islower()) and ((previous_line_end.isalnum() == False)):
                        podcast.seek(podcast.tell() - 1, os.SEEK_SET)
                        podcast.write("")
                    podcast.write(" " + line)
                elif current_speaker != previous_speaker:
                    if ((float(timestamp[0]) < (previous_timestamp + 0.25)) and previous_line_end.isalpha() == False):
                        podcast.seek(podcast.tell() - 1, os.SEEK_SET)
                        podcast.write("-")
                    elif previous_line_end.isalpha():
                        podcast.write("-")
                    podcast.write(f"\n\n{current_speaker}: ")
                    if line[0].islower():
                        podcast.write("-")
                    podcast.write(line)
                    
                previous_line_end = line[-1]
                previous_speaker = current_speaker
                previous_timestamp = float(timestamp[0])

        # Get the next timestamp/speaker and load it into the stack
        next_number = next(file_generators[idx], None)
        if next_number is not None:
            heapq.heappush(min_heap, (next_number, idx))


    
