# Use an official lightweight Python image
FROM python:3.13-slim

# Set environment variables to optimize Python inside Docker
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies (needed for certain Python packages like psycopg2)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your Django project code
COPY . /app/

# Expose Django's default port
EXPOSE 8000

# Run database migrations and start the Gunicorn server (or development server for now)
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]