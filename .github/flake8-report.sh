#!/bin/bash

# Run Flake8
poetry run flake8 aiodesa --exclude tests/ --max-line-length=88

# Check the exit code of Flake8
if [ $? -eq 0 ]; then
    FLAKE8_STATUS="passed"
else
    FLAKE8_STATUS="failed"
fi

# Update README with the badge
sed -i "s|!\[Flake8\].*|![Flake8](https://img.shields.io/badge/Flake8-$FLAKE8_STATUS-brightgreen)|" README.md
