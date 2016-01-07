# Steps to release a new version

- Change version in `cfnplan/__init__.py`
- Create a signed tag: ```git tag -m "Release 1.0.0" 1.0.0```
- Create PyPI release: ```python setup.py sdist upload```
