@echo off
cmd /c git add .
cmd /c git commit -m "some fix"
cmd /c git push
cmd /c python setup.py sdist
cmd /c twine upload dist/*