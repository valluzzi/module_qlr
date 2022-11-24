@echo off
set comment=%1
cmd /c git add .
cmd /c git commit -m %comment%
cmd /c git push
cmd /c rmdir /Q /S dist
cmd /c python setup.py sdist
cmd /c twine upload dist/*