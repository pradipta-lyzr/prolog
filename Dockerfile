# Use a lightweight Python base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies and tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Copy only the requirements file to leverage Docker's caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .


# Expose the application port
EXPOSE 5000

# Command to run the Flask app
CMD ["gunicorn", "-b", "0.0.0.0:5000", "main:app"]

