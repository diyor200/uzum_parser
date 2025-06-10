FROM python:3.10-slim

# Set working directory
WORKDIR /bot

# Copy project files
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Use absolute path for CMD (good practice)
CMD ["python", "bot.py"]
