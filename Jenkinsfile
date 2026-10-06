pipeline {
    agent any

    environment {
        APP_IMAGE = 'aceest-fitness'
        IMAGE_TAG = "${BUILD_NUMBER}"
    }

    stages {
        stage('Checkout SCM') {
            steps {
                echo 'Pulling latest commit from GitHub...'
                checkout scm
            }
        }

        stage('Static Lint Analysis') {
            steps {
                echo 'Checking syntax and code standards with flake8...'
                sh '''
                    python3 -m venv venv
                    . venv/bin/activate
                    pip install flake8
                    flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
                '''
            }
        }

        stage('Docker Image Assembly') {
            steps {
                echo "Building Docker image ${APP_IMAGE}:${IMAGE_TAG}..."
                sh "docker build -t ${APP_IMAGE}:${IMAGE_TAG} ."
            }
        }

        stage('Containerized Pytest') {
            steps {
                echo "Running unit tests in containerized runner..."
                sh "docker run --rm ${APP_IMAGE}:${IMAGE_TAG} pytest -v tests/"
            }
        }
    }

    post {
        always {
            cleanWs()
        }
        success {
            echo "Jenkins Quality Gate Passed: Artifact validated successfully."
        }
        failure {
            echo "Jenkins Pipeline Failed: Please check stage logs."
        }
    }
}