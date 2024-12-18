CI/CD Pipeline for Python Web Application

This repository contains a Jenkins pipeline configuration to automate the CI/CD process for a Python web application. The pipeline performs linting, dependency scanning, Docker image building, testing, and deployment.


---

Features

1. Clone Repository
Fetches the latest code from the Git repository.


2. Verification (Parallel Tasks):

Linting: Analyzes code quality with pylint.

Dependency Scan: Scans for high-severity vulnerabilities with bandit.

Dockerfile Scan: Validates Dockerfile security and best practices using checkov.



3. Build

Configures Git for safe directory access.

Builds a Docker image with unique tags, including the Jenkins build number and Git commit hash.



4. Test

Starts the Docker container.

Validates the endpoint with a connectivity test to ensure the application is running correctly.

Stops and removes the container after the test.



5. Push
Pushes the Docker image to Docker Hub with both versioned and latest tags.


6. Trigger CD Pipeline
Initiates a CD pipeline (project-cd) with build metadata.


7. Notifications
Sends Slack alerts for both successful and failed builds.




---

Pipeline Configuration

Environment Variables

registry: Docker Hub repository (eranzaksh/infinity).

registryCredential: Jenkins credential ID for Docker Hub.

API_KEY: Secure API key for visual-crossing-api.


Jenkins Agent

Label: eee

Docker Image: eranzaksh/jenkins-agent:python



---

Pipeline Stages

1. Clone Git Repository

Fetches the latest code using checkout scm.

2. Verification (Parallel)

Linting: Uses pylint to analyze Python code for quality and style issues.

Dependency Scan: Scans for security vulnerabilities with bandit.

Dockerfile Scan: Checks for Dockerfile security issues using checkov.


3. Build

Tags Docker images with BUILD_NUMBER and GIT_COMMIT.

Builds the Docker image from the web_app/ directory.


4. Test

Runs the built Docker container.

Validates endpoint connectivity with a 200 HTTP status check.

Cleans up the container after testing.


5. Push

Pushes the built Docker images to Docker Hub with both versioned and latest tags.

6. Trigger CD Pipeline

Triggers the project-cd job in Jenkins, passing the BUILD_NUMBER and GIT_COMMIT as parameters.


---

Notifications

Success: Sends a Slack message to the succeeded-build channel.

Failure: Sends a Slack message to the devops-alerts channel.



---

Prerequisites

1. Jenkins Setup:

Install required plugins:

Docker

Pipeline

Slack


Configure Jenkins agents with Docker capabilities.



2. Docker Hub:

Create a Docker Hub repository (eranzaksh/infinity).

Add Docker Hub credentials to Jenkins.



3. Slack:

Configure Slack integration in Jenkins.

Add appropriate channel IDs for notifications.



4. EC2 Metadata Access:

Ensure the EC2 instance running the pipeline can access its metadata.





---

Repository Structure

web_app/
├── app.py                  # Main application file
├── requirements.txt        # Python dependencies
├── Dockerfile              # Docker configuration
├── tests/                  # Unit tests
└── other_files/            # Additional files


---

Running Locally

1. Clone the repository:

git clone <repository_url>
cd <repository_directory>


2. run the Jenkinsfile in a pipeline Jenkins job
