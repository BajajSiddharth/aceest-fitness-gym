# ACEest Fitness & Gym — Automated CI/CD Pipeline

A containerized Flask web application designed for **ACEest Fitness & Gym**. This project transitions legacy fitness logic into a modular REST API, fully integrated with automated testing, containerization, and dual CI/CD pipeline quality gates using **GitHub Actions** and **Jenkins**.

---

## Architecture & Project Structure

```text
aceest-fitness-gym/
├── .github/
│   └── workflows/
│       └── main.yml        # GitHub Actions automated workflow
├── app/
│   ├── __init__.py
│   └── app.py              # Modular Flask web application & REST API
├── tests/
│   ├── __init__.py
│   └── test_app.py         # Pytest unit testing suite
├── .dockerignore           # Exclusions for container builds
├── .flake8                 # Linting rules & path exclusions
├── .gitignore              # Git tracking exclusions
├── Dockerfile              # Multi-stage, non-root Docker build
├── Jenkinsfile             # Declarative Jenkins build & quality gate pipeline
├── requirements.txt        # Python production & testing dependencies
└── README.md               # Setup and architecture documentation

## 1. Local Setup and Execution Instructions

### Prerequisites

* **Python:** 3.11+
* **Docker:** Engine 24+
* **Git:** Version 2.40+

### Running Locally with Virtual Environment

1. **Clone the repository:**
   ```bash
   git clone https://github.com/BajajSiddharth/aceest-fitness-gym.git
   cd aceest-fitness-gym
   ```

2. **Initialize and activate a virtual environment:**
   ```bash
   # Create virtual environment
   python3 -m venv venv

   # Activate on macOS/Linux:
   source venv/bin/activate

   # Activate on Windows:
   venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Start the Flask development server:**
   ```bash
   python app/app.py
   ```
   > The service will start locally at **`http://127.0.0.1:5000`**.

5. **Verify API endpoints:**
   ```bash
   # Check system health status
   curl http://127.0.0.1:5000/health

   # Fetch available gym programs & nutrition plans
   curl http://127.0.0.1:5000/programs
   ```

---

## 2. Running Tests

### Running Unit Tests Locally
Execute the test suite across all endpoints, calculation logic, and validation schemas:
```bash
pytest -v tests/
```

### Running Static Code Analysis (Linting)
Ensure code cleanliness and syntax validation with `flake8`:
```bash
flake8 app/ tests/ --count --select=E9,F63,F7,F82 --show-source --statistics
```

### Running Containerized Tests (Local Docker Verification)
Verify that tests pass inside an isolated production-parity runtime container prior to pushing code:
```bash
# Build temporary test container
docker build -t aceest-fitness:test .

# Execute test suite inside the container
docker run --rm aceest-fitness:test pytest -v tests/
```

---

## 3. Container Management (Docker)

The application utilizes a secure, multi-stage `Dockerfile` executed under a non-root user (`devopsuser`) to optimize image size, build caching, and runtime security.

* **Build the image:**
  ```bash
  docker build -t aceest-fitness:latest .
  ```

* **Run the containerized application:**
  ```bash
  docker run -d -p 5000:5000 --name aceest-gym aceest-fitness:latest
  ```

* **Inspect running container and health checks:**
  ```bash
  docker ps --filter "name=aceest-gym"
  ```

* **Stop and remove container:**
  ```bash
  docker stop aceest-gym && docker rm aceest-gym
  ```

---

## 4. CI/CD Integration & Pipeline Overview

The project incorporates two automated validation pipelines to guarantee zero-defect delivery across distributed environments.

### GitHub Actions Pipeline (`.github/workflows/main.yml`)
* **Trigger:** Automatically invoked on any `push` or `pull_request` targeting `main` or `dev`.
* **Workflow Stages:**
  1. **Source Checkout & Python Setup:** Pulls repository commits and initializes Python 3.11 with cached pip wheels.
  2. **Build & Lint:** Executes `flake8` across application source directories (`app/`, `tests/`) to block syntax regressions and undefined variables.
  3. **Docker Image Assembly:** Assembles the multi-stage, hardened Docker container.
  4. **Automated Container Testing:** Runs `pytest` inside the newly built Docker container to confirm environmental parity and test stability.

### Jenkins Build & Quality Gate (`Jenkinsfile`)
* **Role:** Acts as the dedicated build server and secondary quality gate in an automated pipeline environment.
* **Workflow Stages:**
  1. **Checkout SCM:** Clones the latest commit from GitHub using webhooks or SCM polling.
  2. **Static Lint Analysis:** Initializes an isolated environment and executes `flake8 app/ tests/`.
  3. **Docker Image Assembly:** Builds the immutable container image tagged dynamically with `${BUILD_NUMBER}`.
  4. **Containerized Pytest:** Executes the test suite inside the runtime container artifact:
     ```bash
     docker run --rm aceest-fitness:${BUILD_NUMBER} pytest -v tests/
     ```
  5. **Post Actions / Workspace Cleanup:** Runs `cleanWs()` after execution to maintain host runner health and prevent disk bloat.