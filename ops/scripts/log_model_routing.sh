#!/bin/bash

LOGFILE=/home/desazure/.openclaw/workspace/logs/model_routing.log

# Rotate logs every 2 days (cleanup older than 2 days)
find /home/desazure/.openclaw/workspace/logs/model_routing.log* -mtime +2 -type f -delete

# This script should be called from gateway event hooks or wrapper to log model routing
# Usage: log_model_routing.sh <sessionKey> <modelId> <promptExcerpt>

sessionKey="$1"
modelId="$2"
promptExcerpt="$3"

# Print timestamped log line

echo "$(date -u +'%Y-%m-%dT%H:%M:%SZ') - session:$sessionKey - model:$modelId - prompt:'${promptExcerpt:0:100}'" >> "$LOGFILE"

# Compress old logs
find /home/desazure/.openclaw/workspace/logs/model_routing.log* -mtime +1 -type f -exec gzip -9 {} \;
