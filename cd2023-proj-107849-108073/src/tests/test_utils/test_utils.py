import pytest
import os
import shutil
from ffmpeg_utils import mp3ToWav, getDuration, splitAudio, stitchAudio, wavToMp3
# from ffmpeg_utils import mp3ToWav
# Test data

mp3_file = "./tests/test_utils/aux_files/test.mp3"
outputlocation = "./tests/test_utils/temp_output/"
wav_file = ""
wav_split_files = []
outputSplitFiles = "./tests/test_utils/temp_output/splitted/"
@pytest.fixture(scope="session", autouse=True)
def clean_output():
    # create temp_output
    os.mkdir(outputlocation)

    yield

    # delete every file in temp_output
    if os.path.exists(outputlocation):
        shutil.rmtree(outputlocation)

def test_mp3ToWav():
    mp3ToWav(mp3_file, outputlocation)
    files = os.listdir(outputlocation)
    assert len(files) == 1
    wav_file = files[0]
    assert wav_file.endswith(".wav")

def test_getDuration():
    files = os.listdir(outputlocation)
    wav_file = outputlocation+files[0]
    assert 34.351020 == getDuration(wav_file)

def test_splitAudio():
    files = os.listdir(outputlocation)
    wav_file = outputlocation+files[0]

    splitAudio(wav_file, outputSplitFiles, 4)
    files = os.listdir(outputSplitFiles)
    assert len(files) == 4
    for i in range(0,4):
        wav_split_files.append(files[i])
    
    for file in wav_split_files:
        assert file.endswith(".wav")
    
    assert 8.591383 == getDuration(outputSplitFiles + wav_split_files[0])

def test_stitchAudio():
    stitchAudio(outputSplitFiles, outputlocation+"stitched.wav")
    files = os.listdir(outputlocation)
    assert len(files) == 3
    assert "stitched.wav" in files
    assert 34.351020 == getDuration(outputlocation+"stitched.wav")
    pass

def test_wavToMp3():
    wavToMp3(outputlocation+"stitched.wav", outputlocation)
    files = os.listdir(outputlocation)
    assert len(files) == 4
    assert "stitched.mp3" in files
    assert 34.377143 == getDuration(outputlocation+"stitched.mp3")
    pass
