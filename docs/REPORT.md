# ACEest Fitness & Gym – CI/CD Report

## 1. CI/CD architecture overview
```
Developer -> GitHub (dev/main, tags v1.0.0, v2.0.0)
              |-> GitHub Actions: flake8 -> pytest+coverage -> docker build -> pytest in container
              |-> Jenkins (pollSCM every 2 min):
                    Checkout -> flake8 -> pytest+coverage -> SonarQube scan -> Quality Gate
                    -> docker build -> pytest in container -> push to Docker Hub
                    -> kubectl rolling update (auto `rollout undo` on failure)
Docker Hub (<user>/aceest-fitness:1.0.0, 2.0.0, build-N, latest)
   -> Kubernetes / Minikube: rolling, blue-green, canary, shadow, A/B (see k8s/)
```
* **Application**: Flask REST API (`app/app.py`); version reported on `/` via `APP_VERSION`.
* **Container**: multi-stage, non-root image with HEALTHCHECK.
* **Quality**: Pytest (9 tests), flake8, SonarQube (`sonar-project.properties`, coverage from `coverage.xml`).

## 2. Deployment strategies (k8s/)
| Strategy | Manifest | NodePort | Rollback |
|---|---|---|---|
| Rolling update | base/deployment-rolling.yaml | 30080 | `kubectl rollout undo deploy/aceest-rolling` |
| Blue-Green | blue-green/blue-green.yaml | 30081 | patch Service selector back to `blue` |
| Canary (20%) | canary/canary.yaml | 30082 | `kubectl scale deploy aceest-canary --replicas=0` |
| Shadow | shadow/shadow.yaml | 30083 | delete mirror deployment; users only ever hit v1 |
| A/B testing | ab-testing/ab-testing.yaml | 30084 | route all to variant A |

Endpoint URL: `http://<minikube ip>:<nodePort>/` (fill in before submission).

## 3. Challenges and mitigation
* Jenkins container could not use the Docker socket -> permission self-heal step in Jenkinsfile.
* Keeping dev/prod parity for tests -> tests also executed inside the built image.
* Zero-downtime releases -> readiness probes, `maxUnavailable: 0`, automatic rollback on failed rollout.
* Traffic splitting without a service mesh -> replica-ratio canary and nginx header routing/mirroring.

## 4. Key automation outcomes
* Every push/PR is linted, tested and containerised automatically.
* Versioned images published to Docker Hub; Quality Gate blocks low-quality builds.
* Five deployment strategies with documented, tested rollback paths.
