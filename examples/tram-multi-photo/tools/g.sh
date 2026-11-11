#!/bin/zsh
uv run -q --no-project --with pillow python "$(dirname $0)/grid.py" "$@"
