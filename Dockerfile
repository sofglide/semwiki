FROM python:3.8

WORKDIR /usr/src/app

COPY src ./src

RUN pip install --no-cache-dir -r src/api/requirements.txt

ENV PYTHONPATH "src"

CMD [ "python", "./src/api/search_server.py" ]