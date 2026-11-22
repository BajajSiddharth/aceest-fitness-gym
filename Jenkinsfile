pipeline {
    agent any

    triggers {
        // Poll GitHub every 2 minutes (webhook can be added on top)
        pollSCM('H/2 * * * *')
    }

    parameters {
        string(name: 'APP_VERSION', defaultValue: '1.0.0', description: 'Semantic version used as Docker Hub tag')
        booleanParam(name: 'DEPLOY_TO_K8S', defaultValue: false, description: 'Deploy to Kubernetes (rolling update) after push')
    }

    environment {
        DOCKERHUB_USER = 'DOCKERHUB_USER'
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

        stage('Unit Tests & Coverage') {
            steps {
                sh '''
                    . venv/bin/activate
                    pip install -r requirements.txt
                    pytest --cov=app --cov-report=xml:coverage.xml --junitxml=pytest-report.xml tests/
                '''
            }
            post {
                always { junit 'pytest-report.xml' }
            }
        }

        stage('SonarQube Analysis') {
            steps {
                // 'sonarqube' = server name configured in Manage Jenkins > System; 'sonar-scanner' = tool name
                withSonarQubeEnv('sonarqube') {
                    script {
                        def scannerHome = tool 'sonar-scanner'
                        sh "${scannerHome}/bin/sonar-scanner"
                    }
                }
            }
        }

        stage('Quality Gate') {
            steps {
                timeout(time: 5, unit: 'MINUTES') {
                    waitForQualityGate abortPipeline: true
                }
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

        stage('Push to Docker Hub') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'dockerhub-creds', usernameVariable: 'DH_USER', passwordVariable: 'DH_PASS')]) {
                    sh '''
                        echo "$DH_PASS" | docker login -u "$DH_USER" --password-stdin
                        docker tag ${APP_IMAGE}:${IMAGE_TAG} $DH_USER/${APP_IMAGE}:${APP_VERSION}
                        docker tag ${APP_IMAGE}:${IMAGE_TAG} $DH_USER/${APP_IMAGE}:build-${IMAGE_TAG}
                        docker tag ${APP_IMAGE}:${IMAGE_TAG} $DH_USER/${APP_IMAGE}:latest
                        docker push $DH_USER/${APP_IMAGE}:${APP_VERSION}
                        docker push $DH_USER/${APP_IMAGE}:build-${IMAGE_TAG}
                        docker push $DH_USER/${APP_IMAGE}:latest
                        docker logout
                    '''
                }
            }
        }

        stage('Deploy to Kubernetes (Rolling Update)') {
            when { expression { params.DEPLOY_TO_K8S } }
            steps {
                withCredentials([usernamePassword(credentialsId: 'dockerhub-creds', usernameVariable: 'DH_USER', passwordVariable: 'DH_PASS')]) {
                    sh '''
                        kubectl apply -f k8s/base/deployment-rolling.yaml
                        kubectl set image deployment/aceest-rolling aceest=$DH_USER/${APP_IMAGE}:${APP_VERSION}
                        kubectl set env deployment/aceest-rolling APP_VERSION=${APP_VERSION}
                        # Automatic rollback to the last stable revision if the rollout does not become healthy
                        if ! kubectl rollout status deployment/aceest-rolling --timeout=120s; then
                            echo "Rollout failed - rolling back"
                            kubectl rollout undo deployment/aceest-rolling
                            exit 1
                        fi
                    '''
                }
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