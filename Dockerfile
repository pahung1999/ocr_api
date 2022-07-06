FROM python:3.9.2

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

RUN apt-get update
RUN apt-get install ffmpeg libsm6 libxext6  -y

EXPOSE 8000

COPY ./app /code

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--reload"]

# CMD ["uvicorn", "main:app", "--reload"]