#!/usr/bin/env bash
#
# Redeploy the antd-to-html Docker service by removing the old container,
# rebuilding the image, and starting a fresh container.

set -euo pipefail

SERVICE_NAME="${SERVICE_NAME:-antd-to-html}"
IMAGE_NAME="${IMAGE_NAME:-antd-to-html}"
HOST_PORT="${HOST_PORT:-6422}"
CONTAINER_PORT="${CONTAINER_PORT:-6422}"

log() {
  printf '[redeploy] %s\n' "$*"
}

if docker container inspect "${SERVICE_NAME}" >/dev/null 2>&1; then
  log "Removing existing container ${SERVICE_NAME}..."
  docker rm -f "${SERVICE_NAME}" >/dev/null
else
  log "No existing container named ${SERVICE_NAME}."
fi

if docker image inspect "${IMAGE_NAME}" >/dev/null 2>&1; then
  log "Removing existing image ${IMAGE_NAME}..."
  docker image rm -f "${IMAGE_NAME}" >/dev/null || log "Image ${IMAGE_NAME} is in use; skipping removal."
else
  log "No existing image named ${IMAGE_NAME}."
fi

log "Building image ${IMAGE_NAME}..."
docker build --tag "${IMAGE_NAME}" .

log "Starting container ${SERVICE_NAME}..."
docker run -d \
  --name "${SERVICE_NAME}" \
  -p "${HOST_PORT}:${CONTAINER_PORT}" \
  "${IMAGE_NAME}" >/dev/null

log "Deployment complete. Container ${SERVICE_NAME} is listening on port ${HOST_PORT}."
