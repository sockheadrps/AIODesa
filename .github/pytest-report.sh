#!/bin/bash

# Run pytest
poetry run pytest --cov-report term --cov=aiodesa
result=$(poetry run coverage report)
echo "$result"
# Get the last 3 characters from the 4th from last line
cov_percent=$(echo "$result" | tail -n 1 | rev | cut -c 2-3 | rev)
echo "$cov_percent"


# Update README with the badge
sed -i "s|!\[Pytest\].*|![Pytest](https://img.shields.io/badge/Pytest-$cov_percent%25-brightgreen)|" README.md
