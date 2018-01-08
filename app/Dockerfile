FROM python:3.6-alpine
ADD requirements /config/
RUN pip install -r /config/requirements
RUN mkdir /app
COPY . /app
WORKDIR /app