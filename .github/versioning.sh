version=$(awk -F '"' '/version[[:space:]]*=/ {print $2}' pyproject.toml)
echo "updating changie and docs version $version"
sed -i "s|!\[Read The Docs\].*|![Read The Docs](https://img.shields.io/badge/Documentation-$version-blue)|" README.md

sed -i "s|!\[Changie Logs\].*|![Changie Logs](https://img.shields.io/badge/Changie_logs-$version-blue)|" README.md



