FROM python:3.11-buster

COPY ./requirements.txt ./

RUN pip install --upgrade pip wheel
RUN pip install -r requirements.txt

# COPY ./data ./data # uncomment if building/running on new server
COPY ./.env ./
COPY ./hangman_battle.py ./

ENV PYTHONPATH=.

WORKDIR .