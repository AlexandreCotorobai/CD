# Requirements
All requirements are found in the requirements.txt file. To install them, please use the following command:
```bash
pip install -r requirements.txt
```

# Celery
To use celery please make sure you have a rabbitmq server running on your machine. You can install rabbitmq on docker using the following command:s
```bash
docker run -d -p 5672:5672 -v /absolutepath/to/rabbitmq-custom.conf:/etc/rabbitmq rabbitmq
```

To run celery, you can use the following command whe the file celeryapp.py is located (in the backend folder):
```bash
celery -A celeryapp worker --loglevel=info --hostname={workername}@{worker_pc_ip_address} --concurrency 1
```

Please also make sure that the IP address in the celeryapp.py file is the same as the IP address of the machine that's running the rabbitmq server and API.

# API
To run the API, please use the following command:
```bash
uvicorn app.main:app --reload
```
in the backend folder.

# Frontend
Open the index.html file in the frontend folder in your browser to use the frontend.

