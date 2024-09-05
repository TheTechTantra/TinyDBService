# Use an official Python image as a base
FROM python:3.12-slim

# Set the working directory to /app
WORKDIR /app

# Copy the requirements file
COPY requirements.txt .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Expose the port
EXPOSE 28080

# Run the command to start the development server
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "28080"]