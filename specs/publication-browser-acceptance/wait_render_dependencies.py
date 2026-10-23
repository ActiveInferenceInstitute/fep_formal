"""Wait fail-closed for this workflow attempt's genuine render dependency artifact.

Importing this stdlib module does not inspect the CI environment or access the network.
"""

from __future__ import annotations

import json
import os
import time
import urllib.request
from typing import Any


def main() -> None:
    repo = os.environ["GITHUB_REPOSITORY"]
    run = int(os.environ["GITHUB_RUN_ID"])
    attempt = int(os.environ["GITHUB_RUN_ATTEMPT"])
    checkout_head = os.environ["GITHUB_SHA"]
    event_name = os.environ["GITHUB_EVENT_NAME"]
    with open(os.environ["GITHUB_EVENT_PATH"]) as event_file:
        event = json.load(event_file)
    assert event_name in {"pull_request", "push", "workflow_dispatch"}, (
        "Unsupported source event"
    )
    api_head = (
        event["pull_request"]["head"]["sha"]
        if event_name == "pull_request"
        else checkout_head
    )
    assert len(api_head) == len(checkout_head) == 40 and all(
        c in "0123456789abcdef" for c in api_head + checkout_head
    )
    artifact_name = "render-figures-" + str(run) + "-" + str(attempt)
    base = os.environ["GITHUB_API_URL"] + "/repos/" + repo + "/actions/runs/" + str(run)
    headers = {
        "Authorization": "Bearer " + os.environ["GH_TOKEN"],
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    deadline = time.monotonic() + 1200

    def get(url: str) -> Any:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=20) as response:
            raw = response.read(4_000_001)
        assert len(raw) <= 4_000_000, "Oversized Actions API response"
        return json.loads(raw)

    metadata = get(base)
    assert (
        metadata["id"] == run
        and metadata["run_attempt"] == attempt
        and metadata["event"] == event_name
        and metadata["head_sha"] == api_head
    ), "Wrong workflow-run source identity"
    assert metadata["repository"]["full_name"] == repo, "Wrong repository"
    while time.monotonic() < deadline:
        data = get(base + "/attempts/" + str(attempt) + "/jobs?per_page=100")
        assert (
            data["total_count"] <= 100 and len(data["jobs"]) == data["total_count"]
        ), "Unexpected job pagination"
        jobs = [job for job in data["jobs"] if job["name"] == "render-deps"]
        assert len(jobs) <= 1, "Ambiguous render-deps job"
        if jobs:
            job = jobs[0]
            assert (
                job["run_id"] == run
                and job["run_attempt"] == attempt
                and job["head_sha"] == api_head
            ), "Wrong producer identity"
            if job["status"] == "completed":
                assert job["conclusion"] == "success", "render-deps did not succeed"
                artifacts = get(base + "/artifacts?per_page=100")
                assert (
                    artifacts["total_count"] <= 100
                    and len(artifacts["artifacts"]) == artifacts["total_count"]
                ), "Unexpected artifact pagination"
                matches = [
                    a
                    for a in artifacts["artifacts"]
                    if a["name"] == artifact_name and not a["expired"]
                ]
                if matches:
                    assert len(matches) == 1, "Ambiguous current-attempt artifact"
                    artifact = matches[0]
                    assert (
                        artifact["workflow_run"]["id"] == run
                        and artifact["workflow_run"]["head_sha"] == api_head
                        and artifact["size_in_bytes"] > 0
                    ), "Wrong artifact identity"
                    with open(os.environ["GITHUB_OUTPUT"], "a") as output:
                        output.write("artifact_id=" + str(int(artifact["id"])) + "\n")
                    print(
                        "render-deps barrier passed for run",
                        run,
                        "attempt",
                        attempt,
                        "job",
                        job["id"],
                        "artifact",
                        artifact["id"],
                    )
                    break
        time.sleep(min(10, max(0, deadline - time.monotonic())))
    else:
        raise SystemExit(
            "Timed out waiting for current-attempt render-deps success and artifact"
        )


if __name__ == "__main__":
    main()
