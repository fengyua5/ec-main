#!/bin/sh
cd "$(dirname "$0")" && uv run pytest tests/ -q
