#!/usr/bin/env bash
TOKEN=$(curl -s -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 60")
echo "== Instancia =="; curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/instance-type; echo
echo "== CPU ==";  lscpu | grep -E "Model name|^CPU\(s\)"
echo "== RAM ==";  free -h | head -2
echo "== Swap ==";  swapon --show
echo "== Disco =="; df -h / | tail -1
echo "== GPU ==";  nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv 2>/dev/null || echo "Sin GPU"
echo "== Versiones =="; docker --version; docker compose version; ollama --version; python3 --version; aws --version
echo "== Modelos Ollama =="; ollama list
