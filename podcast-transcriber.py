import os
import whisper
import sys

# Takes a directory of split audio files and Audacity label files
# transcribes/dumps them via Whisper into a preformatted text file

pod_folder = os.getcwd() + "/" + sys.argv[1]
label_files = []
label_dict = {}

for file in os.listdir(pod_folder):
    if file.endswith(".txt"):
        label_files.append(file)

def label_cleaner(label_file, dictionary):
    labels = open(pod_folder + "/" + label_file, "r")
    
    while labels:

        label = labels.readline()
        if label == "":
            break

        labeldata = label.split("\t")

        filename = labeldata[2].removesuffix('\n')
        if len(labeldata[0]) < 11:
            timestamp = labeldata[0].rjust(11, '0')
        else:
            timestamp = labeldata[0]

        dictionary[filename] = timestamp

for file in label_files:
    label_cleaner(file, label_dict)

audio_files = sorted(label_dict.items(), key=lambda x:x[1])
print(audio_files)

model = whisper.load_model("medium.en")

with open(sys.argv[1] + ".txt", 'w') as podcast:
    previous_speaker = ""
    for audio in audio_files:
        if os.path.isfile(pod_folder + "/" + audio[0] + ".wav"):
            print(f"Reading file {audio[0]}...")
            current_speaker = audio[0].split(" ")[0]

            speech = whisper.load_audio(pod_folder + "/" + audio[0] + ".wav")
            speech = whisper.pad_or_trim(speech)
            result = model.transcribe(speech)
            line = current_speaker + ": " + result["text"]
            print(line)
            if result["text"] != "":
                if previous_speaker == "":
                    previous_speaker = current_speaker
                    podcast.write(line)
                elif current_speaker == previous_speaker:
                    podcast.write(" " + result["text"])
                elif current_speaker != previous_speaker:
                    podcast.write("\n\n")
                    podcast.write(line)
                    previous_speaker = current_speaker
                print("File analyzed.")
