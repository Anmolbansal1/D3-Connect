from python:2.7

ENV FLASK_APP app.py

RUN mkdir -p /usr/d3connect
WORKDIR /usr/d3connect

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY . .

RUN dos2unix boot.sh
RUN chmod +x boot.sh

EXPOSE 5000

CMD [ "flask", "run" ]
