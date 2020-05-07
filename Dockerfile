FROM python:3.8-slim-buster

WORKDIR /app

COPY requirements.txt /app/
RUN pip install -r requirements.txt

# enable running app without any host mounts
COPY ./* /app/

EXPOSE 8050

CMD ["python", "app.py"]