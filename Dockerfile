FROM python:3.10
WORKDIR /app
COPY app/ /app
RUN pip install --no-cache-dir --timeout 100 -r requirements.txt
EXPOSE 8501
CMD ["streamlit", "run", "index.py"]