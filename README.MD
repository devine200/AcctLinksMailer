# ACCT BANK EMAIL SENDER
## Building executable
```bash
pyinstaller \
  --onefile \
  --clean \
  --name dynamic-email-backend \
  --add-data "webapp/templates/public:webapp/templates/public" \
  --collect-all django \
  --collect-all rest_framework \
  --collect-all corsheaders \
  --collect-all dotenv \
  --collect-all pandas \
  --collect-all requests \
  run_server.py
```

## Remove and reset execution
```bash
rm -rf build dist *.spec
```