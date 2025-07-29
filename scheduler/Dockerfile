FROM python:3.13.2-slim

WORKDIR /app

COPY scheduler/requirements.txt .

COPY common ./common

RUN pip install --upgrade pip \
 && pip install -r requirements.txt

CMD ["python", "scheduler_main.py"]
