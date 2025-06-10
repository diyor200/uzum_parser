# Use Playwright's official base image
FROM mcr.microsoft.com/playwright/python:v1.52.0

# Set work directory
WORKDIR /app

# Copy app files
COPY .. /app

# Install dependencies (if you have requirements.txt)
RUN pip install --no-cache-dir -r requirements.txt

# Optional: if you use uvicorn for dev
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
