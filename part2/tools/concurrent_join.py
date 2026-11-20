"""Send a concurrent join batch to an initially empty lab queue.

Run from part2: python tools/concurrent_join.py --url http://localhost:8000
Use --drain to also check names via /next after the join batch has finished.
This consumes the queue; use only a separate, empty test queue.
"""

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import json
import threading
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://localhost:8000")
    parser.add_argument("--count", type=int, default=200)
    parser.add_argument("--workers", type=int, default=200)
    parser.add_argument("--drain", action="store_true")
    args = parser.parse_args()
    if args.count < 1 or args.workers < 1:
        parser.error("count and workers must be positive")
    base = args.url.rstrip("/")
    start = threading.Event()

    def post(route, payload=None):
        data = b"" if payload is None else json.dumps(payload).encode("utf-8")
        request = Request(base + route, data=data, method="POST",
                          headers={"Content-Type": "application/json"})
        try:
            with urlopen(request, timeout=60) as response:
                return response.status, response.read().decode("utf-8")
        except HTTPError as error:
            return error.code, error.read().decode("utf-8")
        except (URLError, OSError) as error:
            return 0, str(error)

    names = [f"student-{i:03d}" for i in range(args.count)]

    def join(name):
        start.wait()
        return name, post("/join", {"name": name})

    with ThreadPoolExecutor(max_workers=min(args.workers, args.count)) as pool:
        futures = [pool.submit(join, name) for name in names]
        start.set()
        results = [future.result() for future in futures]

    tickets = []
    errors = []
    for name, (status, body) in results:
        try:
            if status != 200:
                raise ValueError
            tickets.append(int(body))
        except ValueError:
            errors.append({"name": name, "status": status, "body": body})
    duplicates = {str(ticket): count for ticket, count in Counter(tickets).items()
                  if count > 1}
    expected = set(range(1, args.count + 1))
    report = {"sent": args.count, "successful": len(tickets),
              "duplicate_tickets": duplicates,
              "missing_tickets": sorted(expected - set(tickets)),
              "unexpected_tickets": sorted(set(tickets) - expected),
              "errors": errors}
    passed = not errors and not duplicates and set(tickets) == expected
    if args.drain:
        taken = []
        # Bound the loop so a broken /next implementation cannot run forever.
        for _ in range(args.count + 1):
            status, body = post("/next")
            if status != 200:
                break
            taken.append(body)
        actual = Counter(taken)
        wanted = Counter(names)
        report.update({"taken": len(taken),
                       "missing_names": list((wanted - actual).elements()),
                       "extra_names": list((actual - wanted).elements()),
                       "final_next": {"status": status, "body": body}})
        passed = passed and actual == wanted and (status, body) == (404, "empty")
    report["passed"] = passed
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
