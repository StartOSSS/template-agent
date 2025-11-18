#!/usr/bin/env bash
set -euo pipefail

echo "This is a placeholder for deploying the agent to Vertex AI Agent Builder."
echo "Ensure gcloud is configured and GOOGLE_APPLICATION_CREDENTIALS is set."

echo "gcloud alpha aiplatform agents deploy \"
  --display-name=todo-orchestrator \"
  --location=${VERTEX_LOCATION:-us-central1} \"
  --project=${VERTEX_PROJECT_ID:-your-project} \"
  --image=todo-agent:latest \"
  --set-env-vars=TODO_API_BASE_URL=${TODO_API_BASE_URL}"
