#!/bin/sh
exec uv run -q --with numpy --with scipy --with opencv-python-headless --with pillow python "$@"
