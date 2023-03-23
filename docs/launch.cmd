sphinx-apidoc -o docs src/
call .\/docs/make html
cls
echo "hosting docs at http://localhost:8000/docs/_build/html/"
python -m http.server > nul