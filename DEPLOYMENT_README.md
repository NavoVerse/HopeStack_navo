# Mental Health Application Deployment

This application has been successfully restructured for containerized deployment using Docker.

## Project Structure Overview
The app consists of 5 microservices. Dockerfiles were created for each service without altering source code.
1. **Unified Emotion AI**: Port 8080 (`LiveEmotion/UnifiedEmotion`)
2. **Face Emotion Recognizer**: Port 8001 (`faceEmotion`)
3. **Voice Emotion Recognizer**: Port 8002 -> Maps to internall 8000 (`voiceEmotion`)
4. **Speech to Text**: Port 8003 -> Maps to internal 8000 (`speechToText`)
5. **User Login Portal**: Port 8004 -> Maps to internal 80 (`userLogin`)

## Prerequisites
- **Docker** and **Docker Compose** installed on your system.

## Deployment Instructions

### 1. Build and Run Deployments
Open a terminal in the root directory (where `docker-compose.yml` is located) and run the following command to build the Docker images and start the containers.

```bash
docker-compose up --build -d
```
*Note:* The initial build might take a while because it needs to retrieve base-images and install heavy machine learning dependencies (PyTorch, TensorFlow, OpenCV, Transformers).*

### 2. Status check
Use `docker-compose ps` to list all the active services and track loading status or `docker-compose logs -f [service_name]` to attach to the stream. Models take roughly 1-2 minutes to be cached and loaded entirely on the first boot. 

### 3. Stop running services
```bash
docker-compose down
```

## Useful Tools
Each subsystem operates independently in isolated containers. Modifying a service only requires you to execute `docker-compose build [service_name]` inside the root directory and re-executing `docker-compose up -d`.
