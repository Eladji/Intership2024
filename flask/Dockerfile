FROM python:3.9
FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04
WORKDIR /app
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*
    
COPY . /app
# Copy and install dependencies
RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt

# Expose the port
EXPOSE 5000

# Command to run the application
CMD ["flask", "run", "--host=0.0.0.0"]