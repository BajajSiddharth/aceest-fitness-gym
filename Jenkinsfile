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
                    flake8 app/ tests/ --count --select=E9,F63,F7,F82 --show-source --statistics
                '''
            }
        }

        stage('Docker Image Assembly') {
            steps {
                echo "Assembling Docker image ${APP_IMAGE}:${IMAGE_TAG}..."
                sh '''
                    # Self-heal docker socket permissions if not writable
                    if [ ! -w /var/run/docker.sock ]; then
                        echo "Fixing Docker socket permissions..."
                        sudo chmod 666 /var/run/docker.sock || true
                    fi

                    docker build -t ${APP_IMAGE}:${IMAGE_TAG} .
                '''
            }
        }

        stage('Containerized Pytest') {
            steps {
                echo "Running unit tests in containerized runner..."
                sh '''
                    if [ ! -w /var/run/docker.sock ]; then
                        sudo chmod 666 /var/run/docker.sock || true
                    fi

                    docker run --rm ${APP_IMAGE}:${IMAGE_TAG} pytest -v tests/
                '''
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