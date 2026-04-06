FROM python:3.11-slim

WORKDIR /app/apps/api

COPY apps/api/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY apps/api/app ./app
COPY apps/api/tests ./tests
COPY packages/mock-data /app/packages/mock-data

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
