# Use an official lightweight Python image
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Copy the requirements file into the container
# Assumes the Docker build context is the `backend` directory
COPY requirements.txt .

# Install python packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy all files from the backend directory to /app/backend inside the container
# This preserves the `backend.main:app` module path expected by the codebase
COPY . ./backend/

# Expose the API port
EXPOSE 8000

# Start the uvicorn server
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
