param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

& "C:\Users\Administrator\me12\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload