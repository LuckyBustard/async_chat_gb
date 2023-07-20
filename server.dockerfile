FROM python:3.8-buster

RUN apt-get update \
	&& apt-get install -y --no-install-recommends \
		postgresql-client \
	&& rm -rf /var/lib/apt/lists/*

RUN mkdir -p /opt/app
WORKDIR /opt/app

RUN pip install --upgrade pip
COPY requirements.txt ./
RUN pip install -r requirements.txt

EXPOSE 8000
CMD ["python server.py && tail -f /dev/null"]