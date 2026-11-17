# SentinelX — Mini-SOC (Milestone 1)

Local, read-only security monitoring platform. Standard library only, localhost only.

## Run (Windows PowerShell)
    cd C:\Users\Albin\SENTINELX
    python --version          # must be 3.9 or newer
    python app.py             # then open http://127.0.0.1:8080

## Test
    python -m unittest discover -s tests -v

## Configure
Edit thresholds in `config.py` (DETECTION_RULES). Restart the app.

## Safety
- Binds to 127.0.0.1 only. Host + Origin checks. No JavaScript. CSP + security headers.
- Parameterized SQL, HTML escaping, CSV formula-injection protection.
- Test data is labelled TEST; real data is labelled REAL.
- Automatic DB backups on start (data/backups, newest 7 kept). Logs in logs/sentinelx.log.
