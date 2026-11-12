#!/usr/bin/env bash
set -euo pipefail

app_dir="${APP_DIR:-${HOME}/pdf-rag}"
compose_file="${app_dir}/docker-compose.yml"
env_file="${app_dir}/.env"

: "${GHCR_IMAGE:?Set GHCR_IMAGE to the image to deploy.}"

if [[ ! -f "${env_file}" ]]; then
    echo "Missing ${env_file}. Create it with GROQ_API_KEY before deploying." >&2
    exit 1
fi
if [[ ! -f "${compose_file}" ]]; then
    echo "Missing ${compose_file}. Upload docker-compose.yml before deploying." >&2
    exit 1
fi
if ! docker compose version >/dev/null 2>&1; then
    echo "Docker Compose v2 is required on the EC2 instance." >&2
    exit 1
fi

chmod 600 "${env_file}"
cd "${app_dir}"
export GHCR_IMAGE

docker compose pull
docker compose up -d --remove-orphans

for attempt in {1..60}; do
    health_status="$(docker inspect --format='{{.State.Health.Status}}' "$(docker compose ps -q app)" 2>/dev/null || true)"
    if [[ "${health_status}" == "healthy" ]]; then
        echo "Deployment is healthy."
        exit 0
    fi
    if [[ "${health_status}" == "unhealthy" ]]; then
        break
    fi
    sleep 2
done

docker compose logs --tail=100 app
echo "Deployment did not become healthy." >&2
exit 1
