#!/usr/bin/env bash
# Usage: bash k8s/deploy.sh <rolling|blue-green|canary|shadow|ab-testing|all>
set -euo pipefail
cd "$(dirname "$0")"

apply() {
  kubectl apply -f "$1"
}

case "${1:-all}" in
  rolling)    apply base/deployment-rolling.yaml ;;
  blue-green) apply blue-green/blue-green.yaml ;;
  canary)     apply canary/canary.yaml ;;
  shadow)     apply shadow/shadow.yaml ;;
  ab-testing) apply ab-testing/ab-testing.yaml ;;
  all)
    for f in base/deployment-rolling.yaml blue-green/blue-green.yaml canary/canary.yaml shadow/shadow.yaml ab-testing/ab-testing.yaml; do
      apply "$f"
    done ;;
  *) echo "unknown strategy"; exit 1 ;;
esac

kubectl get deploy,svc
