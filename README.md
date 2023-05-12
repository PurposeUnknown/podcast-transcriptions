# podcast-transcriber
Script for transcribing audio files into an article format (designed for the Dojima Futures podcast or other podcasts)

Assumptions / Requirements:
Python >= 3.10
OpenAI's Whisper model
Audacity >= 3.0 for piping
Separate audio tracks for each speaker

General process:
-look for speaker audio files and load them into Audacity
-if there are multiple files for a given speaker, in Audacity sort and merge them into one file
-label sounds based on Audacity sound/audio detection
-export audio into clips based on labels
-transcribe with OpenAI's Whisper model
-format using audio timestamps from the labels to split into paragraphs per speaker (and general transcription cleanup)


