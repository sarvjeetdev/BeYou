# # Dockerfile
# FROM python:3.9-slim

# # Set environment variables
# ENV PYTHONUNBUFFERED=1

# # Set working directory
# WORKDIR /app

# # Copy files
# COPY . .

# # Install dependencies
# RUN pip install --upgrade pip
# RUN pip install -r requirements.txt

# # Run the Django server
# CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]


FROM python:3.9-slim

# 1. Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# 2. Set workdir
WORKDIR /app

# 3. Copy everything
COPY . .

# 4. Upgrade pip and install dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# 5. Command (set in docker-compose instead)
