#!/bin/bash
# Copyright (C) 2024 shmilee

LS_PKG_DIR=${1:-~/.local/lib/python3.12/site-packages/label_studio}
TS_templates_DIR="$LS_PKG_DIR/annotation_templates/time-series-analysis"

if [ -d "$TS_templates_DIR" ]; then
    cd "$(dirname "$0")"
    find gtc-time-stage-forecasting-v1 -type f \
        -exec install -v -Dm644 {} "$TS_templates_DIR"/{} \;
else
    echo "Usage: $0 <label_studio package path>"
    echo "  Example: $LS_PKG_DIR"
fi
