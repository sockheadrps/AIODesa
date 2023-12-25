#!/bin/bash

# Check if the index.txt file exists
if [ -f ".github/mypy/index.txt" ]; then
    # Extract the total precise percentage from the index.txt file
    precise_percentage=$(awk -F'|' '/Total/ {gsub(/[%[:space:]]/, "", $3); print 100 - $3}' .github/mypy/index.txt)
    echo "$precise_percentage"
    # Check if precise_percentage is not empty
    if [ -n "$precise_percentage" ]; then
        # Update the badge in README.md with the calculated precise percentage
        sed -i "s|!\[MyPy\].*|![MyPy](https://img.shields.io/badge/MyPy-$precise_percentage%25-brightgreen)|" README.md

    else
        echo "Error: Unable to retrieve MyPy precise percentage from .github/mypy/index.txt."
    fi
else
    echo "Error: .github/mypy/index.txt not found."
fi
