There is an Apache-style access log at `/app/access.log`. Each line starts with the
client IP address and contains a quoted request line, for example:

    192.168.0.1 - - [16/Jun/2026:10:00:01 +0000] "GET /index.html HTTP/1.1" 200 1024

Parse the log and write a JSON summary to `/app/report.json`. The file must contain a
single JSON object with exactly these three keys:

- `total_requests`: an integer, the number of non-empty lines in the log.
- `unique_ips`: an integer, the number of distinct client IP addresses (the first
  whitespace-separated field of each line).
- `top_path`: a string, the request path (the target of the quoted request line, e.g.
  `/index.html`) that appears most often.

Your report is correct when all of the following hold:

1. `/app/report.json` exists and contains a single valid JSON object.
2. That object has exactly the keys `total_requests`, `unique_ips`, and `top_path`.
3. `total_requests` equals the number of non-empty lines in the log.
4. `unique_ips` equals the number of distinct client IP addresses in the log.
5. `top_path` equals the most frequently requested path in the log.
