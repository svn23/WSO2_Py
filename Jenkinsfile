pipeline {
    agent any

    environment {
        // You can set specific environment variables here if necessary
        PYTHONUNBUFFERED = "1"
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Setup Dependencies') {
            steps {
                bat '''
                python -m venv venv
                call venv\\Scripts\\activate.bat
                python -m pip install --upgrade pip
                if exist requirements.txt ( pip install -r requirements.txt )
                if exist requirements-dev.txt ( pip install -r requirements-dev.txt )
                '''
            }
        }

        stage('Lint (Flake8)') {
            steps {
                bat '''
                call venv\\Scripts\\activate.bat
                flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
                flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
                '''
            }
        }

        stage('Test (Pytest)') {
            steps {
                bat '''
                call venv\\Scripts\\activate.bat
                pytest -v
                '''
            }
        }
    }

    post {
        always {
            cleanWs()
        }
    }
}
