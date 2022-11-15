@echo off
git add .
git commit -m "some fix"
git push
python setup.py sdist
twine upload dist/*