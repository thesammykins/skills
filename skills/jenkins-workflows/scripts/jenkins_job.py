#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any


DEFAULT_URL = "http://your-jenkins-host:8080"
DEFAULT_USER_REF = "op://your-vault/jenkins-api-key/username"
DEFAULT_TOKEN_REF = "op://your-vault/jenkins-api-key/credential"


@dataclass(frozen=True)
class Auth:
    url: str
    user: str
    token: str


@dataclass(frozen=True)
class HttpResult:
    status: int
    headers: dict[str, str]
    body: bytes


def read_1password(ref: str) -> str:
    try:
        result = subprocess.run(
            ["op", "read", ref],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except FileNotFoundError as exc:
        raise SystemExit("1Password CLI `op` is not installed; set JENKINS_USER_ID and JENKINS_API_TOKEN.") from exc
    except subprocess.CalledProcessError as exc:
        detail = exc.stderr.strip() or "unknown op read failure"
        raise SystemExit(f"Could not read 1Password ref {ref!r}: {detail}") from exc
    return result.stdout.rstrip("\n")


def resolve_auth(args: argparse.Namespace) -> Auth:
    url = (args.url or os.getenv("JENKINS_URL") or DEFAULT_URL).rstrip("/")
    username_ref = args.username_ref or os.getenv("JENKINS_1PASSWORD_USERNAME_REF") or DEFAULT_USER_REF
    token_ref = args.token_ref or os.getenv("JENKINS_1PASSWORD_TOKEN_REF") or DEFAULT_TOKEN_REF

    user = args.user or os.getenv("JENKINS_USER_ID")
    token = args.token or os.getenv("JENKINS_API_TOKEN")

    if not user and not args.no_op:
        user = read_1password(username_ref)
    if not token and not args.no_op:
        token = read_1password(token_ref)

    if not user:
        raise SystemExit("Missing Jenkins username. Set JENKINS_USER_ID or provide --user.")
    if not token:
        raise SystemExit("Missing Jenkins API token. Set JENKINS_API_TOKEN or provide --token.")

    return Auth(url=url, user=user, token=token)


def auth_header(auth: Auth) -> str:
    raw = f"{auth.user}:{auth.token}".encode("utf-8")
    return "Basic " + base64.b64encode(raw).decode("ascii")


def make_url(auth: Auth, path_or_url: str) -> str:
    if path_or_url.startswith("http://") or path_or_url.startswith("https://"):
        return path_or_url
    path = path_or_url if path_or_url.startswith("/") else f"/{path_or_url}"
    return f"{auth.url}{path}"


def request(
    auth: Auth,
    method: str,
    path_or_url: str,
    *,
    data: bytes | None = None,
    headers: dict[str, str] | None = None,
    timeout: int = 30,
    crumb: bool = False,
) -> HttpResult:
    request_headers = {
        "Authorization": auth_header(auth),
        "Accept": "application/json, text/plain, */*",
        "User-Agent": "jenkins-workflows-skill/1.0",
    }
    if headers:
        request_headers.update(headers)
    if crumb and method.upper() not in {"GET", "HEAD"}:
        crumb_data = get_crumb(auth, timeout=timeout)
        request_headers[crumb_data["crumbRequestField"]] = crumb_data["crumb"]

    req = urllib.request.Request(
        make_url(auth, path_or_url),
        data=data,
        headers=request_headers,
        method=method.upper(),
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            body = response.read()
            return HttpResult(response.status, dict(response.headers.items()), body)
    except urllib.error.HTTPError as exc:
        body = exc.read(1200).decode("utf-8", errors="replace")
        hint = ""
        if exc.code == 401:
            hint = " Check JENKINS_USER_ID and JENKINS_API_TOKEN."
        elif exc.code == 403:
            hint = " Check permissions; for POST, retry with --crumb if needed."
        raise SystemExit(f"Jenkins HTTP {exc.code} for {method.upper()} {path_or_url}.{hint}\n{body}") from exc
    except urllib.error.URLError as exc:
        raise SystemExit(f"Could not reach Jenkins at {auth.url}: {exc.reason}") from exc


def parse_json(result: HttpResult) -> Any:
    if not result.body:
        return None
    try:
        return json.loads(result.body.decode("utf-8"))
    except json.JSONDecodeError as exc:
        text = result.body.decode("utf-8", errors="replace")
        raise SystemExit(f"Expected JSON but received:\n{text}") from exc


def print_json(value: Any) -> None:
    print(json.dumps(value, indent=2, sort_keys=True))


def quote_tree(tree: str) -> str:
    return urllib.parse.quote(tree, safe="[],")


def job_path(job: str) -> str:
    if job.startswith("/job/"):
        return job.rstrip("/")
    parts = [part for part in job.strip("/").split("/") if part]
    if not parts:
        raise SystemExit("Job name/path cannot be empty.")
    encoded = "/job/".join(urllib.parse.quote(part, safe="") for part in parts)
    return f"/job/{encoded}"


def get_crumb(auth: Auth, *, timeout: int = 30) -> dict[str, str]:
    result = request(auth, "GET", "/crumbIssuer/api/json", timeout=timeout)
    data = parse_json(result)
    if not isinstance(data, dict) or "crumb" not in data or "crumbRequestField" not in data:
        raise SystemExit("Jenkins crumb issuer returned an unexpected response.")
    return {"crumb": str(data["crumb"]), "crumbRequestField": str(data["crumbRequestField"])}


def cmd_whoami(args: argparse.Namespace) -> None:
    auth = resolve_auth(args)
    print_json(parse_json(request(auth, "GET", "/whoAmI/api/json", timeout=args.timeout)))


def cmd_root(args: argparse.Namespace) -> None:
    auth = resolve_auth(args)
    tree = "mode,nodeName,nodeDescription,numExecutors,quietingDown,useCrumbs,views[name],primaryView[name],jobs[name,url,color,_class]"
    print_json(parse_json(request(auth, "GET", f"/api/json?tree={quote_tree(tree)}", timeout=args.timeout)))


def cmd_jobs(args: argparse.Namespace) -> None:
    auth = resolve_auth(args)
    tree = "jobs[name,url,color,_class,buildable,disabled,inQueue,description,lastBuild[number,result,url,timestamp,duration],lastSuccessfulBuild[number,url],lastFailedBuild[number,url]]"
    print_json(parse_json(request(auth, "GET", f"/api/json?tree={quote_tree(tree)}", timeout=args.timeout)))


def cmd_nodes(args: argparse.Namespace) -> None:
    auth = resolve_auth(args)
    tree = "computer[displayName,offline,temporarilyOffline,numExecutors,assignedLabels[name]]"
    print_json(parse_json(request(auth, "GET", f"/computer/api/json?tree={quote_tree(tree)}", timeout=args.timeout)))


def cmd_plugins(args: argparse.Namespace) -> None:
    auth = resolve_auth(args)
    tree = "plugins[shortName,version,active,enabled]"
    data = parse_json(request(auth, "GET", f"/pluginManager/api/json?tree={quote_tree(tree)}", timeout=args.timeout))
    if args.active_only and isinstance(data, dict):
        data["plugins"] = [plugin for plugin in data.get("plugins", []) if plugin.get("active")]
    print_json(data)


def cmd_job_info(args: argparse.Namespace) -> None:
    auth = resolve_auth(args)
    tree = args.tree or "name,url,color,_class,buildable,disabled,inQueue,description,assignedLabel[name],lastBuild[number,result,url,timestamp,duration,building],lastSuccessfulBuild[number,url],lastFailedBuild[number,url]"
    print_json(parse_json(request(auth, "GET", f"{job_path(args.job)}/api/json?tree={quote_tree(tree)}", timeout=args.timeout)))


def parse_parameters(values: list[str]) -> dict[str, str]:
    params: dict[str, str] = {}
    for value in values:
        if "=" not in value:
            raise SystemExit(f"Parameter {value!r} must be KEY=VALUE.")
        key, param_value = value.split("=", 1)
        if not key:
            raise SystemExit(f"Parameter {value!r} has an empty key.")
        params[key] = param_value
    return params


def queue_api_path(queue_url: str) -> str:
    parsed = urllib.parse.urlparse(queue_url)
    path = parsed.path.rstrip("/") + "/api/json"
    return urllib.parse.urlunparse((parsed.scheme, parsed.netloc, path, "", "", "")) if parsed.scheme else path


def wait_for_queue(auth: Auth, queue_url: str, *, timeout: int, poll: float) -> dict[str, Any]:
    deadline = time.time() + timeout
    api_url = queue_api_path(queue_url)
    while time.time() < deadline:
        data = parse_json(request(auth, "GET", api_url, timeout=30))
        if data.get("cancelled"):
            raise SystemExit("Queued Jenkins item was cancelled.")
        executable = data.get("executable")
        if executable:
            return executable
        time.sleep(poll)
    raise SystemExit(f"Timed out waiting for Jenkins queue item to start after {timeout}s.")


def stream_build(auth: Auth, build_url: str, *, timeout: int, poll: float) -> dict[str, Any]:
    deadline = time.time() + timeout
    offset = 0
    more = True
    api_url = build_url.rstrip("/") + "/api/json?tree=building,result,number,url,duration,timestamp"

    while time.time() < deadline:
        log_url = build_url.rstrip("/") + f"/logText/progressiveText?start={offset}"
        result = request(auth, "GET", log_url, timeout=30)
        if result.body:
            sys.stdout.write(result.body.decode("utf-8", errors="replace"))
            sys.stdout.flush()
        offset = int(result.headers.get("X-Text-Size", offset))
        more = result.headers.get("X-More-Data", "false").lower() == "true"

        build = parse_json(request(auth, "GET", api_url, timeout=30))
        if not build.get("building") and not more:
            return build
        time.sleep(poll)

    raise SystemExit(f"Timed out following Jenkins build after {timeout}s.")


def cmd_trigger(args: argparse.Namespace) -> None:
    auth = resolve_auth(args)
    params = parse_parameters(args.parameter)
    path = job_path(args.job)
    if params:
        endpoint = f"{path}/buildWithParameters"
        body = urllib.parse.urlencode(params).encode("utf-8")
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
    else:
        endpoint = f"{path}/build"
        body = b""
        headers = {}

    result = request(auth, "POST", endpoint, data=body, headers=headers, timeout=args.timeout, crumb=args.crumb)
    queue_url = result.headers.get("Location")
    queued = {"status": result.status, "queueUrl": queue_url}
    print_json(queued)

    if args.follow:
        if not queue_url:
            raise SystemExit("Jenkins did not return a queue Location header; cannot follow build.")
        executable = wait_for_queue(auth, queue_url, timeout=args.wait_timeout, poll=args.poll)
        build_url = executable.get("url")
        if not build_url:
            raise SystemExit("Jenkins queue item started without an executable URL.")
        final = stream_build(auth, build_url, timeout=args.follow_timeout, poll=args.poll)
        print_json({"final": final})
        if final.get("result") != "SUCCESS":
            raise SystemExit(f"Jenkins build finished with result {final.get('result')}")


def cmd_follow(args: argparse.Namespace) -> None:
    auth = resolve_auth(args)
    build = args.build.rstrip("/")
    if build.startswith("http://") or build.startswith("https://"):
        build_url = build
    else:
        build_url = f"{auth.url}{job_path(args.job)}/{urllib.parse.quote(build, safe='')}/"
    final = stream_build(auth, build_url, timeout=args.follow_timeout, poll=args.poll)
    print_json({"final": final})
    if final.get("result") != "SUCCESS":
        raise SystemExit(f"Jenkins build finished with result {final.get('result')}")


def cmd_console(args: argparse.Namespace) -> None:
    auth = resolve_auth(args)
    build = urllib.parse.quote(args.build, safe="")
    result = request(auth, "GET", f"{job_path(args.job)}/{build}/consoleText", timeout=args.timeout)
    sys.stdout.write(result.body.decode("utf-8", errors="replace"))


def cmd_api(args: argparse.Namespace) -> None:
    auth = resolve_auth(args)
    data = None
    headers: dict[str, str] = {}
    if args.data_json:
        data = args.data_json.encode("utf-8")
        headers["Content-Type"] = "application/json"
    elif args.data_form:
        form = parse_parameters(args.data_form)
        data = urllib.parse.urlencode(form).encode("utf-8")
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    elif args.method.upper() not in {"GET", "HEAD"}:
        data = b""

    result = request(auth, args.method, args.path, data=data, headers=headers, timeout=args.timeout, crumb=args.crumb)
    content_type = result.headers.get("Content-Type", "")
    if "json" in content_type:
        print_json(parse_json(result))
    else:
        sys.stdout.write(result.body.decode("utf-8", errors="replace"))


def add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--url", help="Jenkins base URL. Defaults to JENKINS_URL or the configured Butler URL.")
    parser.add_argument("--user", help="Jenkins user ID. Defaults to JENKINS_USER_ID or 1Password.")
    parser.add_argument("--token", help="Jenkins API token. Defaults to JENKINS_API_TOKEN or 1Password.")
    parser.add_argument("--username-ref", help="1Password ref for the Jenkins user ID.")
    parser.add_argument("--token-ref", help="1Password ref for the Jenkins API token.")
    parser.add_argument("--no-op", action="store_true", help="Disable 1Password fallback; require env vars or flags.")
    parser.add_argument("--timeout", type=int, default=30, help="HTTP timeout in seconds.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Small Jenkins API helper for the jenkins-workflows skill.")
    add_common(parser)
    sub = parser.add_subparsers(dest="command", required=True)

    whoami = sub.add_parser("whoami", help="Show authenticated Jenkins identity.")
    whoami.set_defaults(func=cmd_whoami)

    root = sub.add_parser("root", help="Show root Jenkins metadata and top-level jobs.")
    root.set_defaults(func=cmd_root)

    jobs = sub.add_parser("jobs", help="List top-level jobs and last build states.")
    jobs.set_defaults(func=cmd_jobs)

    nodes = sub.add_parser("nodes", help="List Jenkins nodes and labels.")
    nodes.set_defaults(func=cmd_nodes)

    plugins = sub.add_parser("plugins", help="List installed plugins.")
    plugins.add_argument("--active-only", action="store_true", help="Only show active plugins.")
    plugins.set_defaults(func=cmd_plugins)

    job_info = sub.add_parser("job-info", help="Show one job's metadata.")
    job_info.add_argument("job", help="Job name or folder path, for example folder/job.")
    job_info.add_argument("--tree", help="Custom Jenkins API tree expression.")
    job_info.set_defaults(func=cmd_job_info)

    trigger = sub.add_parser("trigger", help="Trigger a Jenkins job.")
    trigger.add_argument("job", help="Job name or folder path.")
    trigger.add_argument("-p", "--parameter", action="append", default=[], help="Build parameter as KEY=VALUE. Repeatable.")
    trigger.add_argument("--crumb", action="store_true", help="Include Jenkins crumb on the POST request.")
    trigger.add_argument("--follow", action="store_true", help="Wait for queue start and stream build output.")
    trigger.add_argument("--poll", type=float, default=2.0, help="Polling interval in seconds.")
    trigger.add_argument("--wait-timeout", type=int, default=300, help="Seconds to wait for queue item to start.")
    trigger.add_argument("--follow-timeout", type=int, default=3600, help="Seconds to follow build output.")
    trigger.set_defaults(func=cmd_trigger)

    follow = sub.add_parser("follow", help="Stream an existing Jenkins build.")
    follow.add_argument("job", help="Job name or folder path.")
    follow.add_argument("--build", default="lastBuild", help="Build number/permalink, or full build URL. Defaults to lastBuild.")
    follow.add_argument("--poll", type=float, default=2.0, help="Polling interval in seconds.")
    follow.add_argument("--follow-timeout", type=int, default=3600, help="Seconds to follow build output.")
    follow.set_defaults(func=cmd_follow)

    console = sub.add_parser("console", help="Print consoleText for an existing build.")
    console.add_argument("job", help="Job name or folder path.")
    console.add_argument("--build", default="lastBuild", help="Build number/permalink. Defaults to lastBuild.")
    console.set_defaults(func=cmd_console)

    api = sub.add_parser("api", help="Call a raw Jenkins API endpoint.")
    api.add_argument("method", choices=["GET", "POST", "PUT", "DELETE", "HEAD"])
    api.add_argument("path", help="Path or full URL.")
    api.add_argument("--data-json", help="Raw JSON request body.")
    api.add_argument("--data-form", action="append", default=[], help="Form field as KEY=VALUE. Repeatable.")
    api.add_argument("--crumb", action="store_true", help="Include Jenkins crumb on mutating requests.")
    api.set_defaults(func=cmd_api)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
