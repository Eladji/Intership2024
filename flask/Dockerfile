FROM python:3.9

WORKDIR /app

COPY . /app
# Copy and install dependencies
COPY requirements.txt /src
RUN --mount=type=cache,target=/root/.cache/pip pip install -r requirements.txt


# Expose the port
EXPOSE 5000

# Command to run the application
CMD ["flask", "run", "--host=0.0.0.0"]