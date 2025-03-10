FROM python:3.9

# Install dependencies
RUN apt-get update && apt-get install -y tesseract-ocr

# Set Tesseract path
ENV TESSERACT_PATH="/usr/bin/tesseract"

# Install Python dependencies
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy project files
COPY . .

# Run the app
CMD ["python", "app.py"]
