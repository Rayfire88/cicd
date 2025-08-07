FROM python:3.11-slim
WORKDIR /CICD
COPY app.py .
RUN pip install --no-cache-dir flask
EXPOSE 8000
CMD ["python", "app.py"]
