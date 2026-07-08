# Fixed Harbor task: dynamo/log-report

Repaired Terminal-Bench 2 (Harbor) task. The job itself is small: parse an
Apache-style access log into a JSON report. This repo holds the corrected version.

## Layout

```
log-report/
  task.toml                TB2 config, artifacts = ["/app/report.json"]
  instruction.md           numbered success criteria
  environment/
    Dockerfile             base pinned by @sha256 digest, no solution shipped
    access.log             task input, baked in
  solution/
    solve.sh               oracle entrypoint
    solve.py               reference solution, writes /app/report.json
  tests/
    test.sh                runs pytest, writes reward.txt + ctrf.json to /logs/verifier
    test_outputs.py        asserts the actual values
```

## Verify

```
harbor run -p log-report -a oracle      # reward 1
harbor run -p log-report --agent nop    # reward 0
```
