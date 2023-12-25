#!/bin/bash

# Run Pylint
poetry install
poetry run pylint aiodesa > .github/pylint_report.txt

# Check the exit code of Pylint
if [ $? -eq 0 ]; then
    PYLINT_STATUS="passed"
else
    PYLINT_STATUS="failed"
fi

# Extract the rating from the Pylint report
PYLINT_RATING=$(grep -oP '(?<=rated at ).*?/10' .github/pylint_report.txt | awk '{printf "%.2f", $1}')
echo "$PYLINT_RATING"
# Convert to integer if the rating is 10.00
if [ "$PYLINT_RATING" = "10.00" ]; then
    PYLINT_RATING=10
fi

# Update README with the badge
sed -i "s|!\[Pylint\].*|![Pylint](https://img.shields.io/badge/Pylint-$PYLINT_RATING/10-brightgreen)|" README.md
