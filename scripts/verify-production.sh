#!/bin/sh
set -eu

base_url=${1:?usage: verify-production.sh https://service.example}

if ! body=$(curl --silent --show-error --max-time 15 "${base_url%/}/health"); then
  printf '%s\n' inconclusive
  exit 2
fi

if printf '%s' "$body" | grep -q '"status":"healthy"'; then
  printf '%s\n' healthy
  exit 0
fi

printf '%s\n' unhealthy
exit 1
