pipeline {
    agent any

    parameters {
        string(name: 'APP_VERSION', defaultValue: '1.0.0', description: 'Semantic version used as Docker Hub tag')
        booleanParam(name: 'DEPLOY_TO_K8S', defaultValue: false, description: 'Deploy to Kubernetes (rolling update) after push')
    }

    environment {
        DOCKERHUB_USER = 'bajaj1995'
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

        stage('SonarQube Analysis & Quality Gate') {
            steps {
                // 'sonarqube' = server name configured in Manage Jenkins > System; 'sonar-scanner' = tool name
                withSonarQubeEnv('sonarqube') {
                    script {
                        def scannerHome = tool 'sonar-scanner'
                        sh "${scannerHome}/bin/sonar-scanner -Dsonar.qualitygate.wait=true -Dsonar.qualitygate.timeout=300"
                    }
                }
            }
        }

        stage('Docker Image Assembly') {
            steps {
                echo "Assembling Docker image ${APP_IMAGE}:${IMAGE_TAG}..."
                sh '''
                    docker build -t ${APP_IMAGE}:${IMAGE_TAG} .
                '''
            }
        }

        stage('Containerized Pytest') {
            steps {
                echo "Running unit tests in containerized runner..."
                sh '''
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
                        set -eu

                        previous_revision=""
                        existing_deployment=$(kubectl get deployment aceest-rolling --ignore-not-found -o name)

                        if [ -n "$existing_deployment" ]; then
                            kubectl rollout status deployment/aceest-rolling --timeout=120s
                            previous_revision=$(kubectl get deployment aceest-rolling \
                                -o go-template='{{index .metadata.annotations "deployment.kubernetes.io/revision"}}')
                            case "$previous_revision" in
                                ''|*[!0-9]*)
                                    echo "Cannot determine the healthy deployment revision." >&2
                                    exit 1
                                    ;;
                            esac
                        fi

                        sed \
                            -e "s#image: .*#image: $DH_USER/${APP_IMAGE}:build-${IMAGE_TAG}#" \
                            -e "s#1[.]0[.]0#${APP_VERSION}#g" \
                            k8s/base/deployment-rolling.yaml | kubectl apply -f -

                        if ! kubectl rollout status deployment/aceest-rolling --timeout=180s; then
                            if [ -n "$previous_revision" ]; then
                                echo "Rollout failed - restoring healthy revision $previous_revision."
                                kubectl rollout undo deployment/aceest-rolling \
                                    --to-revision="$previous_revision"
                                kubectl rollout status deployment/aceest-rolling --timeout=180s
                            else
                                echo "Initial deployment failed; no previous revision exists." >&2
                            fi
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