# pin base by digest so builds are reproducible
FROM python:3.13-slim@sha256:eb43ff125d8d58d7449dcba7d336c23bcac412f526d861db493b9994d8010280

# verifier deps, baked in so test.sh installs nothing at verify time
RUN pip install --no-cache-dir pytest==8.4.1 pytest-json-ctrf==0.3.5

WORKDIR /app

# only ship the log, no solution files
COPY access.log /app/access.log
