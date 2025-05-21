# Use the official Python image as a base
FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8080
ENV GEMNIN_API_KEY=AIzaSyDIdxQTzKvP4a6lof_xQ8IZaOp5yORFlJg
ENV PERPPLEXITY_API_KEY=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

# Set working directory
WORKDIR /app

# Copy only requirements to leverage Docker cache
COPY backend/requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the backend code
COPY backend/ ./backend/

# Expose the port Cloud Run expects
EXPOSE 5000

# Start the FastAPI server
CMD fastapi run server.py --port 5000
