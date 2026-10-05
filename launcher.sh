#!/bin/bash
# Morning News Desktop App — launch wrapper
cd "$(dirname "$0")"
exec python3 -m app "$@"
