# Use an official Python image as a base
FROM python:3.12-slim

# Set the working directory to /app
WORKDIR /app

# Copy the requirements file
COPY requirements.txt .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy only the application code (avoid baking .git, secrets, or db.json into the image)
COPY app.py CredentialModel.py TinyDBUtil.py __init__.py ./

# Expose the port
EXPOSE 28080

# Run the command to start the development server
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "28080"]