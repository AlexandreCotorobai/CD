
from fastapi import FastAPI

from fastapi.middleware.cors import CORSMiddleware
import json
import os
from fastapi import File, UploadFile, BackgroundTasks
from starlette.responses import FileResponse

from app.ffmpeg_utils import *
import sys
sys.path.append('app')
from celeryapp import process_wave, tasks
from pydub import AudioSegment

from typing import List
import time
import math

from app.schemas import Music, Progress, Track, Instrument, Job
from tinytag import TinyTag
import shutil
from celery.result import AsyncResult
import base64

# used to cancel tasks
global cancel_tasks
cancel_tasks = False

app = FastAPI(title="Distributed Music Editor - Advanced Sound Systems")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if not os.path.exists("DATA_FILES"):
    os.makedirs("DATA_FILES")

if not os.path.exists("DATA_FILES/music.json"):
    with open("DATA_FILES/music.json", "w") as json_file:
        json.dump([], json_file)

data_file_path = os.path.join("DATA_FILES", "music.json")
# Load existing JSON data from file
existing_json_data = []
if os.path.exists(data_file_path):
    with open(data_file_path, "r") as json_file:
        existing_json_data = json.load(json_file)
    
absbackend_path = os.path.abspath("backend")

jobs = []
ongoing_jobs = {}
@app.get("/music", status_code=200 ,response_model=List[Music])
def get_music():
    #len(tasks.control.inspect().stats().keys())) get number of workers
    arr = [x["METADATA"] for x in existing_json_data]
    print(arr)
    mus_arr = []
    for x in arr:
        x = json.loads(x)
        mus_arr.append(Music(
            music_id=x["music_id"],
            music_name=x["music_name"],
            music_band=x["music_band"],
            music_tracks=x["music_tracks"]
        ))

    return mus_arr

@app.post("/music", status_code=200, response_model=Music)
def post_music(file: UploadFile = File(...)):

    # with open(file.filename, "wb") as buffer:
    #     buffer.write(file.file.read())
    id = selectID()
    
    # write file to folder with id as name in DATA_FILES
    
    os.makedirs(os.path.join("DATA_FILES", str(id)), exist_ok=True)
    with open(os.path.join("DATA_FILES", str(id), "original.mp3"), "wb") as buffer:
        buffer.write(file.file.read())
    
    tag = TinyTag.get(os.path.join("DATA_FILES", str(id), "original.mp3"))

    music = Music(
        music_id=id,  # Set the appropriate music_id
        music_name=tag.title if tag.title else "Unknown",
        music_band=tag.artist if tag.artist else "Unknown",  # Set the appropriate band/artist name
        music_tracks=[],  # Set the appropriate track list
    )

    
    saveFile(file, id)

    ## save in json
    music_json = music.json()
    
    # Append new JSON data to the list
    obj = {"ID": id, "STATUS" : "WAITING", "METADATA" : music_json}
    existing_json_data.append(obj)

    # Save updated JSON data to file
    with open(data_file_path, "w") as json_file:
        json.dump(existing_json_data, json_file)

    return music

@app.post("/music/{music_id}", status_code=200, response_model=List[int])
def post_music(music_id: int, tracks: List[int], background_tasks: BackgroundTasks):
    # file_path = os.path.join("DATA_FILES", str(music_id))
    # if not os.path.exists(file_path):
    #     return {"error": "Music not found"}
    # # epa ya, é o q da pra fazer por enquanto
    # stitchAudio(file_path, file_path + "/stitched.wav")    
    background_tasks.add_task(start_processing, music_id, tracks)
    return tracks

@app.get("/music/{music_id}", status_code=200, response_model=Progress)
def get_music(music_id: int):
    job_info = ongoing_jobs[music_id]
    instrumentArr = []
    for x in job_info[2]:
        name = ""
        if x == 0:
            name = "bass"
        elif x == 1:
            name = "drums"
        elif x == 2:
            name = "vocals"
        elif x == 3:
            name = "other"
        instrumentArr.append(Instrument(
            name=name,
            track=absbackend_path + "/DATA_FILES/" + str(music_id) + "/output/" + name + ".wav"
        ))
    if job_info[1] != 100:
        return Progress(
            progress=job_info[1],
            final="",
            instruments=instrumentArr
        )
    else:
        return Progress(
            progress=job_info[1],
            final=absbackend_path + "/DATA_FILES/" + str(music_id) + "/output/final.wav",
            instruments=instrumentArr
        )
    
    



def saveFile(file: UploadFile, music_id: int):
    dir_path = os.path.join("DATA_FILES", str(music_id))
    file_name = "original.mp3"
    mp3ToWav(file_name, dir_path)


def selectID():
        if len(existing_json_data) == 0:
            return 1
        else:
            return existing_json_data[-1]["ID"] + 1

jobs = []

@app.get("/job", status_code=200 ,response_model=List[Job])
def get_jobs():
    return jobs

@app.get("/job/{job_id}", status_code=200, response_model=Job)
def get_job(job_id: int):
    return jobs[job_id-1]

@app.post("/reset", status_code=200, response_model=None)
def post_reset():
    # stop every celery task
    cancel_tasks = True

    tasks.control.revoke(None, terminate=True)
    tasks.control.purge()
    
    # delete every file in DATA_FILES 
    folders = os.listdir("DATA_FILES")
    for folder in folders:
        if folder != "music.json":
            shutil.rmtree(os.path.join("DATA_FILES", folder))
    
    jobs.clear()
    ongoing_jobs.clear()

    while len(existing_json_data) > 0:
        existing_json_data.pop()
    
    with open(data_file_path, "w") as json_file:
        json.dump(existing_json_data, json_file)
    time.sleep(1)
    cancel_tasks = False
    return None

def start_processing(id: int, instruments: List[int]):
    #print("Starting processing")
    start = time.time()
    
    print(instruments)
    existing_json_data[id-1]["STATUS"] = "PROCESSING"

    file_path = os.path.join("DATA_FILES", str(id))
    if not os.path.exists(os.path.join(file_path, "output")):
        ongoing_jobs[id] = (id, 0, instruments)
        splitAudio(file_path+ "/original.mp3", file_path +"/splitted", 1.5) 
        
        splitted_files = os.listdir(file_path +"/splitted")
        splitted_files.sort()
        splitted_files = [[os.path.join(file_path +"/splitted", x), "WAITING"] for x in splitted_files]
        task_ids = []
    # print(len(splitted_files))
        for i in range(len(splitted_files)):
            file = splitted_files[i]
            if file[1] == "WAITING":
                file[1] = "PROCESSING"
                # open file and send to celery
            
                with open(file[0], "rb") as buffer:
                    wavedata = buffer.read()   
                file_size = os.path.getsize(file[0])
                temp_id = len(jobs)+1
                job = Job(job_id=temp_id, size=file_size, time=0, music_id=id, track_id=instruments)     
                jobs.append(job)
                b64data = base64.b64encode(wavedata).decode("utf-8")
                task_ids.append(process_wave.delay(b64data, i, temp_id))
        
        os.makedirs(os.path.join("DATA_FILES", str(id), "proccessed", "drums"), exist_ok=True)
        os.makedirs(os.path.join("DATA_FILES", str(id), "proccessed", "bass"), exist_ok=True)
        os.makedirs(os.path.join("DATA_FILES", str(id), "proccessed", "vocals"), exist_ok=True)
        os.makedirs(os.path.join("DATA_FILES", str(id), "proccessed", "other"), exist_ok=True)
        is_done = False
        completed = 0
        n_jobs = len(splitted_files)
        while not is_done:
            if cancel_tasks:
                return
            for i in task_ids:
                if i.ready():
                    completed += 1
                    res = i.result
                    if type(res) == AssertionError:
                        print(i)
                    else:
                        for instrument_type in res[1]:
                            if instrument_type == "bass":
                                # save bass
                                with open(os.path.join("DATA_FILES", str(id), "proccessed", "bass", str(res[0]) + ".wav"), "wb") as buffer:
                                    buffer.write(base64.b64decode(res[1][instrument_type]))
                            elif instrument_type == "drums":
                                # save drums
                                with open(os.path.join("DATA_FILES", str(id), "proccessed", "drums", str(res[0]) + ".wav"), "wb") as buffer:
                                    buffer.write(base64.b64decode(res[1][instrument_type]))
                            elif instrument_type == "vocals":
                                # save vocals
                                with open(os.path.join("DATA_FILES", str(id), "proccessed", "vocals", str(res[0]) + ".wav"), "wb") as buffer:
                                    buffer.write(base64.b64decode(res[1][instrument_type]))
                            elif instrument_type == "other":
                                # save other
                                with open(os.path.join("DATA_FILES", str(id), "proccessed", "other", str(res[0]) + ".wav"), "wb") as buffer:
                                    buffer.write(base64.b64decode(res[1][instrument_type]))
                        task_ids.remove(i)
                        job = jobs[res[3]-1]
                        new_job = Job(job_id=job.job_id, size=job.size, time=res[2], music_id=job.music_id, track_id=job.track_id)
                        jobs[res[3]-1] = new_job
                        progress = math.floor(completed/n_jobs*100)
                        if progress >= 100:
                            progress = 100
                        ongoing_jobs[id] = (id, progress, instruments)
                        if completed/n_jobs >= 1:
                            is_done = True
            time.sleep(1)
        os.makedirs(os.path.join("DATA_FILES", str(id), "output"), exist_ok=True)
        for instrument_type in ["bass", "drums", "vocals", "other"]:
            files = os.path.join("DATA_FILES", str(id), "proccessed", instrument_type)
            stitchAudio(files, os.path.join("DATA_FILES", str(id), "output", instrument_type + ".wav"))
    
    existing_json_data[id-1]["status"] = "DONE"

    Audioarr = []
    
    for i in instruments:
        if i == 0:
            filepath = os.path.join("DATA_FILES", str(id), "output", "bass.wav")
            Audioarr.append(AudioSegment.from_wav(filepath))
        elif i == 1:
            filepath = os.path.join("DATA_FILES", str(id), "output", "drums.wav")
            Audioarr.append(AudioSegment.from_wav(filepath))
        elif i == 2:
            filepath = os.path.join("DATA_FILES", str(id), "output", "vocals.wav")
            Audioarr.append(AudioSegment.from_wav(filepath))
        elif i == 3:
            filepath = os.path.join("DATA_FILES", str(id), "output", "other.wav")
            Audioarr.append(AudioSegment.from_wav(filepath))
    # remove final.wav if exists
    if os.path.exists(os.path.join("DATA_FILES", str(id), "output", "final.wav")):
        os.remove(os.path.join("DATA_FILES", str(id), "output", "final.wav"))
    
    combined = Audioarr[0]
    for i in range(1, len(Audioarr)):
        combined = combined.overlay(Audioarr[i])

    combined.export(os.path.join("DATA_FILES", str(id), "output" ,"final.wav"), format="wav") 
    # remove proccessed files
    shutil.rmtree(os.path.join("DATA_FILES", str(id), "proccessed"))
    # remove splitted files
    shutil.rmtree(os.path.join("DATA_FILES", str(id), "splitted"))

    end = time.time()
    print("Time taken in seconds : ", (end-start))

@app.get('/download/{id}/{instrument}')
async def download(id: int, instrument: str):
    if os.path.exists(os.path.join("DATA_FILES", str(id), "output", instrument + ".wav")):
        return FileResponse(os.path.join("DATA_FILES", str(id), "output", instrument + ".wav"))
    else:
        return {"error": "file not found"}