# Agent Instructions

## Push Safety

Do not run `git push` unless the relevant validation has been run in the current turn after the changes being pushed.

For this project, the default validation before push is:

```powershell
python -m py_compile app.py (Get-ChildItem studypdf -Recurse -Filter *.py | ForEach-Object { $_.FullName }) tests\conftest.py
node --check static\reader.js
.\.venv\Scripts\python.exe -m pytest
```

If `pytest` cannot run because required external test infrastructure is unavailable, such as `STUDYPDF_TEST_DATABASE_URL`, do not push silently. Report the blocker and ask before pushing anyway.
