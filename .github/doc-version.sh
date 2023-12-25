version=$(awk -F '"' '/version[[:space:]]*=/ {print $2}' pyproject.toml)
sed -i "s|documentation-latest-blue|documentation-$version-blue|" README.md
echo "$version"