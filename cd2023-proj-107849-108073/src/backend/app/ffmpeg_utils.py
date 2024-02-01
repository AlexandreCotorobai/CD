import ffmpeg
import subprocess
import os

def mp3ToWav(FileLocation: str, OutputLocation: str):
    """
    Convert mp3 file to wav file
    """

    OutputLocation = OutputLocation + "/" + FileLocation.split("/")[-1].replace(".mp3", ".wav")

    try:
        (
            ffmpeg.input(FileLocation)
            .output(OutputLocation, format='wav')
            .run(overwrite_output=True)
        )
        # print(f"Conversion completed. WAV file saved at: {OutputLocation}")
    except ffmpeg.Error as e:
        ...
        # print(f"An error occurred during conversion: {e.stderr}")


# mp3ToWav("./tracks/test.mp3", "./tracks/wavs/")


def getDuration(FileLocation: str) -> float:
    """
    Get duration of audio file
    """
    # print(FileLocation)
    try:
        probe = ffmpeg.probe(FileLocation)
        
        # print(probe)
        duration = probe["format"]["duration"]
        # print(f"Duration: {duration}s.")
        return float(duration)
    except ffmpeg.Error as e:
        print(f"An error occurred during conversion: {e.stderr}")



def splitAudio(FileLocation: str, OutputLocation: str, splitDuration: float):
    """
    Split audio file into n parts
    """
    # duration = getDuration(FileLocation)

    # print(duration, numberOfSplits)
    
    # splitDuration = duration / numberOfSplits
    # print(duration, splitDuration)
    try:
        # Create the output directory if it doesn't exist
        os.makedirs(OutputLocation, exist_ok=True)

        # Get the input file name without extension
        file_name = os.path.splitext(os.path.basename(FileLocation))[0]

        # Generate the output file pattern
        output_pattern = os.path.join(OutputLocation, f"splitted-%03d.wav")

        # Run FFmpeg to divide the WAV track into chunks
        subprocess.run([
            "ffmpeg",
            "-i", FileLocation,
            "-f", "segment",
            "-segment_time", str(splitDuration),
            "-c", "copy",
            output_pattern
        ])

        print("WAV track divided into chunks successfully.")
    except subprocess.CalledProcessError as e:
        # print(f"An error occurred during division: {e.stderr}")
        ...
    

# split = splitAudio("./tracks/wavs/test.wav", "./tracks/wavs/splits/", 2)

def stitchAudio(FileLocation: str, OutputFile: str):
    """
    Stitch together multiple WAV chunks into a single WAV file.
    """
    try:
        # Get the list of WAV chunk files in the input directory
        chunk_files = [
            file
            for file in os.listdir(FileLocation)
            if file.lower().endswith(".wav")
        ]
        
        # Sort the chunk files by filename
        chunk_files.sort()

        # Generate a text file with the list of chunk files
        input_list_file = "input_list.txt"
        with open(input_list_file, "w") as f:
            for chunk_file in chunk_files:
                f.write(f"file '{os.path.join(FileLocation, chunk_file)}'\n")

        # Run FFmpeg to concatenate the WAV chunks into a single file
        subprocess.run([
            "ffmpeg",
            "-f", "concat",
            "-safe", "0",
            "-i", input_list_file,
            "-c", "copy",
            OutputFile
        ])

        # Delete the input list file
        # os.remove(input_list_file)

        print(f"WAV chunks stitched together successfully. Output file: {OutputFile}")
    except subprocess.CalledProcessError as e:
        ...
        # print(f"An error occurred during stitching: {e.stderr}")

# Example usage


# stitchAudio("./tracks/wavs/splits/", "./tracks/wavs/stitched/test.wav")

def wavToMp3(FileLocation: str, OutputLocation: str):
    """
    Convert WAV file to MP3 file.
    """
    OutputLocation = OutputLocation + os.path.splitext(os.path.basename(FileLocation))[0] + ".mp3"
    try:
        subprocess.run([
            "ffmpeg",
            "-i", FileLocation,
            "-codec:a", "libmp3lame",
            "-qscale:a", "2",
            OutputLocation
        ])

        print(f"Conversion completed. MP3 file saved at: {OutputLocation}")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred during conversion: {e.stderr}")

# Example usage
# wavToMp3("./tracks/wavs/test.wav", "./tracks/mp3/")