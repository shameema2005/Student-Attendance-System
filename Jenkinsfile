pipeline {
    agent any
    environment {
        IMAGE_NAME = 'student-attendance-app'
    }
    stages {
        stage('Checkout') {
            steps { checkout scm }
        }
        stage('Install dependencies') {
            steps { bat 'python -m pip install -r requirements.txt' }
        }
        stage('Run application checks') {
            steps { bat 'python -m pytest tests -v' }
        }
        stage('Build Docker image') {
            steps { bat 'docker build -t %IMAGE_NAME%:latest .' }
        }
    }
    post {
        success { echo 'Student attendance pipeline completed successfully.' }
        failure { echo 'Pipeline failed. Review Console Output.' }
    }
}
