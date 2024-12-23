FROM python:3.9

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

ADD . ./

EXPOSE 5000/tcp

VOLUME /app/data

CMD [ "gunicorn", "-b 0.0.0.0:5000", "-w 2", "main:app" ]
