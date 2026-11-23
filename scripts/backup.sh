#!/usr/bin/env bash
set -euo pipefail
: "${BUCKET:?define BUCKET}"
cd ~/RAG
aws s3 sync data s3://$BUCKET/data
[ -d storage/qdrant ] && aws s3 sync storage/qdrant s3://$BUCKET/qdrant
echo "Backup OK -> s3://$BUCKET"
