# format code
isort src/sbmlutils
black src/sbmlutils --exclude resources
tox -p
