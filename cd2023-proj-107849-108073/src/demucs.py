import logging
import argparse
import subprocess
import demucs

from demucs.apply import apply_model
from demucs.pretrained import get_model
from demucs.audio import AudioFile, save_audio

def run_demucs(args):
    # get the model
    model = get_model(name='htdemucs')
    model.cpu()
    model.eval()

    # load the audio file
    wav = AudioFile(args.i).read(streams=0,
    samplerate=model.samplerate, channels=model.audio_channels)
    ref = wav.mean(0)
    wav = (wav - ref.mean()) / ref.std()
    
    # apply the model
    sources = apply_model(model, wav[None], device='cpu', progress=True, num_workers=1)[0]
    sources = sources * ref.std() + ref.mean()

    # store the model
    for source, name in zip(sources, model.sources):
        stem = f'{args.o}/{name}.wav'
        save_audio(source, str(stem), samplerate=model.samplerate)


parser = argparse.ArgumentParser(description='Split an audio track', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('-i', type=str, help='./tracks/wavs/test.wav', default='music.mp3')
parser.add_argument('-o', type=str, help='./tracks/wavs/demucs/', default='tracks')
args = parser.parse_args()

run_demucs(args)



# # Example usage
# audio_path = "./tracks/wavs/test.wav"
# output_path = "./tracks/wavs/demucs/"
# run_demucs(audio_path, output_path)
