from python:3.12-alpine3.22

WORKDIR /app
COPY . /app

# Install dependencies from requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

CMD ["python", "/app/main.py"]


