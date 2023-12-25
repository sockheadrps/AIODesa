#!/bin/bash

# Set git user info
git config user.name "GitHub Actions"
git config user.email "actions@github.com"

# Check if there are changes in the README
if git diff --exit-code README.md; then
    echo "No changes in README. Skipping commit and push."
else
    # Commit and push changes
    git add README.md
    git commit -m "Update README with GitHub Actions [skip ci]"
    git push
    echo "Changes in README committed and pushed."
fi
