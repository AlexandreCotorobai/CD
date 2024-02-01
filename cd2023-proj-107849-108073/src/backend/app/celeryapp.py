import base64

from celery import Celery, current_task
from multiprocessing import current_process
from celery.exceptions import Retry

from demucs.apply import apply_model
from demucs.pretrained import get_model
from demucs.audio import AudioFile, save_audio

import torch
import os 
import time
import shutil

torch.set_num_threads(1)
os.environ['OMP_NUM_THREADS'] = '1'

CELERY_IMPORTS = [
'app.tasks',
]
tasks = Celery('tasks', broker='amqp://192.168.0.100:5672', backend='rpc://192.168.0.100:5672')

@tasks.task(bind=True, default_retry_delay=5)
def process_wave(self, wave_data, id, job_id):
    start_time = time.time()
    try:

        worker_name = current_process().pid    
        wave_bytes = base64.b64decode(wave_data)
        # save file
        if not os.path.exists('temp'):
            os.makedirs('temp')
        
        if not os.path.exists(f'temp/{worker_name}'):
            os.makedirs(f'temp/{worker_name}')
    
        # remove every file in the folder
        # IT SHOULD BE EMPTY
        for file in os.listdir(f'temp/{worker_name}'):
            os.remove(f'temp/{worker_name}/{file}')

        with open(f'temp/{worker_name}/task.wav', 'wb') as f:
            f.write(wave_bytes)
        
        # get the model
        model = get_model(name='htdemucs')
        model.cpu()
        model.eval()
    
        # load the audio file
        wav = AudioFile(f"temp/{worker_name}/task.wav").read(streams=0, samplerate=model.samplerate, channels=model.audio_channels)
        ref = wav.mean(0)
        wav = (wav - ref.mean()) / ref.std()
        
        # apply the model
        sources = apply_model(model, wav[None], device='cpu', progress=True, num_workers=1)[0]
        sources = sources * ref.std() + ref.mean()
        output_binary = {}
    
        # store the model
        for source, name in zip(sources, model.sources):
            stem = f'temp/{worker_name}/{name}.wav'
            print(stem)
            save_audio(source, str(stem), samplerate=model.samplerate)
            with open(stem, 'rb') as f:
                output_binary[name] = base64.b64encode(f.read())

        # remove the file
        shutil.rmtree(f'temp/{worker_name}')
        end_time = time.time()
        return [id, output_binary, end_time - start_time, job_id]
    except AssertionError as e:
        current_task.retry(exc=e, countdown=3)
        
    except Exception as e:
        print(f'Error: {e}')

        raise self.retry(exc=e)
    
