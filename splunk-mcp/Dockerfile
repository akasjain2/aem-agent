FROM python:3.10-slim
WORKDIR /app
COPY splunk_server.py .
RUN pip install fastapi uvicorn
EXPOSE 5002
CMD ["uvicorn", "splunk_server:app", "--host", "0.0.0.0", "--port", "5002"]
