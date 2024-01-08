FROM python:3.9.13-slim-buster

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV DEBIAN_FRONTEND noninteractive
RUN apt-get update -y && apt-get install -y curl gnupg
RUN apt-get install --assume-yes nano tcpdump iputils-ping netcat-openbsd nmap iproute2

EXPOSE 8000
# Install pip requirements
COPY requirements.txt .
RUN python -m pip install -r requirements.txt

COPY server.py /usr/local/lib/python3.9/site-packages/pyrad/server.py
COPY sentence.py /usr/local/lib/python3.9/site-packages/routeros_api/sentence.py
WORKDIR /app
COPY . /app
# Creates a non-root user with an explicit UID and adds permission to access the /app folder
# For more info, please refer to https://aka.ms/vscode-docker-python-configure-containers
RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser
RUN mkdir -p /app/media
RUN mkdir -p /app/static

RUN chmod -R 755 /app/static
RUN chmod -R 775 /app/media


# During debugging, this entry point will be overridden. For more information, please refer to https://aka.ms/vscode-docker-python-debug
# CMD ["gunicorn", "--bind", "0.0.0.0:8000", "app.wsgi"]
# CMD ["sleep", "10000"]
CMD ["bash", "/app/runserver.sh"]


