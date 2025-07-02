# Use official Python 3.10 image
FROM python:3.10

# Set working directory
WORKDIR /app

# Copy requirements.txt and install dependencies
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your app
COPY . .

# Expose port (5000 inside container)
EXPOSE 5000

# Run Gunicorn when container starts
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
