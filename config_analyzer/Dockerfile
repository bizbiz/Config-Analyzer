# Use the official Python image as the base image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Install git
RUN apt-get update && apt-get install -y git

# Copy the requirements file into the container
COPY requirements.txt .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Expose the port the app runs on
EXPOSE 5000

# Définir le PYTHONPATH pour inclure le répertoire de votre projet
ENV PYTHONPATH "${PYTHONPATH}:/app/config_analyzer"

# Define the command to run the application
CMD ["sh", "-c", "flask db upgrade && python main.py"]