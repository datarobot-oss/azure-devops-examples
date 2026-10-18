#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Check whether you can deploy a workload to a DataRobot cluster.

Reads what the platform says about your account and checks the `dr` CLI. Read-only. Never prints a token. It does not
build anything, so a restricted network can still stop a build. The example in templates/azure-devops-workload settles that.

Needs DATAROBOT_ENDPOINT and DATAROBOT_API_TOKEN. Usage:

    uv run scripts/check_workload_ready.py [--skip-cli]
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.request

REQUIRED_FLAGS = ("ENABLE_WORKLOAD_API_CONTAINERS",)
# Shown only. On prod US the artifacts flag was off for two accounts that deployed with `dr workload up`.
OPTIONAL_FLAGS = (
    ("ENABLE_WORKLOAD_API_ARTIFACTS_AND_WORKLOADS", "reported by some releases, not what the API checks"),
    ("ENABLE_WORKLOAD_API_AGENT", "agent workloads, `dr workload config --type agent`"),
)
# Before v0.13, `dr workload` was hidden behind the DATAROBOT_CLI_FEATURE_WORKLOAD variable.
MIN_CLI = (0, 13, 0)


def call(base, api_token, path):
    """Return (status, parsed JSON or text) for one GET call to the platform API."""
    request = urllib.request.Request(base + path, headers={"Authorization": f"Bearer {api_token}"})
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return response.status, json.load(response)
    except urllib.error.HTTPError as err:
        raw = err.read()[:300].decode("utf8", "replace")
        try:
            return err.code, json.loads(raw)
        except ValueError:
            return err.code, raw


def parse_cli_version(text):
    """Return the (major, minor, patch) tuple of the first version in `dr --version` output, or None."""
    found = re.search(r"v?(\d+)\.(\d+)\.(\d+)", text)
    return tuple(int(part) for part in found.groups()) if found else None


def check_cli(dr_path):
    """Return (description, problem or None) for the dr CLI at dr_path, or None when it is not installed."""
    if not dr_path:
        return "not found on PATH", "Install the dr CLI (https://github.com/datarobot-oss/cli#installation)."
    # dr_path comes from PATH on purpose, and the arguments are a list, so no shell is involved.
    done = subprocess.run([dr_path, "--version"], capture_output=True, text=True, timeout=30)  # noqa: S603
    version = parse_cli_version(done.stdout + done.stderr)
    if version is None:
        return f"{dr_path}, version unknown", "Run `dr self update`, then check `dr --version`."
    label = "v{}.{}.{}".format(*version)
    if version < MIN_CLI:
        return f"{label} at {dr_path}", (
            f"{label} is older than v0.13. Run `dr self update`. Older releases lack `dr workload up` or hide "
            "`dr workload` behind DATAROBOT_CLI_FEATURE_WORKLOAD=true."
        )
    return f"{label} at {dr_path}, `dr workload up` needs no feature gate", None


def flag_state(permissions, name):
    """Return "on", "OFF" or "not reported" for a feature flag in the account permissions."""
    if name not in permissions:
        return "not reported"
    return "on" if permissions[name] else "OFF"


def message_of(body):
    """Return the human message of an API error body, as text."""
    if isinstance(body, dict):
        return str(body.get("message") or body.get("detail") or body)[:200]
    return str(body)[:200]


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--skip-cli", action="store_true", help="do not check the dr CLI")
    args = parser.parse_args()
    base = os.environ.get("DATAROBOT_ENDPOINT", "").rstrip("/")
    api_token = os.environ.get("DATAROBOT_API_TOKEN", "")
    if not base or not api_token:
        sys.exit('Set DATAROBOT_ENDPOINT and DATAROBOT_API_TOKEN (`eval "$(dr auth export)"` sets both).')

    problems = []
    status, info = call(base, api_token, "/account/info/")
    if status != 200 or not isinstance(info, dict):
        print(f"1. user: HTTP {status}, {message_of(info)}")
        sys.exit("The platform did not accept the API key. Check DATAROBOT_ENDPOINT and DATAROBOT_API_TOKEN.")
    print(f"1. user: {info.get('username')} on {base}")

    permissions = info.get("permissions") or {}
    states = {name: flag_state(permissions, name) for name in REQUIRED_FLAGS}
    print("2. feature flags: " + ", ".join(f"{name} {state}" for name, state in states.items()))
    for name, state in states.items():
        if state == "OFF":
            problems.append(f"{name} is off. Ask a DataRobot administrator to enable it.")
    for name, purpose in OPTIONAL_FLAGS:
        print(f"   optional: {name} {flag_state(permissions, name)} ({purpose})")

    seats = info.get("seatLicenses") or {}
    if seats.get("NON_BUILDER_USER"):
        problems.append("Your user has no builder seat. Ask an administrator for an Agentic Builder seat.")
    print(f"3. seat: {'no builder seat' if seats.get('NON_BUILDER_USER') else 'builder'}")

    # maxConcurrentWorkloads limits running workloads, and an unfiltered total also counts stopped ones.
    status, listing = call(base, api_token, "/workloads/?limit=1&status=running")
    limits = info.get("limits") or {}
    max_workloads = limits.get("maxConcurrentWorkloads")
    max_replicas = limits.get("maxWorkloadReplicas")
    count = listing.get("totalCount") if status == 200 and isinstance(listing, dict) else None
    cap = f"{max_workloads} workloads" if max_workloads else "unlimited workloads"
    print(f"4. limits: up to {cap}, {max_replicas or 'unlimited'} replicas per workload; you can see {count} running")
    if max_workloads and count is not None and count >= max_workloads:
        problems.append("The concurrent workload limit is reached. Stop or delete a workload first.")

    print(
        f"5. workload API: GET /workloads/ answered HTTP {status}"
        + ("" if status == 200 else f", {message_of(listing)}")
    )
    if status != 200:
        problems.append(
            "The Workload API refused the request. The message names the check: usually a feature flag or a seat."
        )

    if not args.skip_cli:
        description, problem = check_cli(shutil.which("dr"))
        print(f"6. dr CLI: {description}")
        if problem:
            problems.append(problem)

    if problems:
        print("\nNOT ready:")
        for problem in problems:
            print(f"  - {problem}")
        sys.exit(1)
    print(
        "\nReady. The platform side is fine. Deploy templates/azure-devops-workload next to find out whether builds work here."
    )


if __name__ == "__main__":
    main()
