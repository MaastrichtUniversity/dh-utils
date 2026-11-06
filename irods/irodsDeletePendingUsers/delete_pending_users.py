#!/usr/bin/env python3
"""Save project permissions and delete users pending deletion via iCommands."""

import argparse
from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import subprocess
import sys
import time
from urllib.parse import quote


RULE_ENGINE = "irods_rule_engine_plugin-irods_rule_language-instance"


def run_rule(name, username=None):
    """Use the same Python-rule dispatcher as /rules/tests/run_test.sh."""
    if username is not None and (not username or "," in username):
        raise ValueError("test_rule_output requires a single nonempty username without commas")
    rule = "test_rule_output({}, {})".format(
        json.dumps(name), json.dumps(username if username is not None else "", ensure_ascii=False),
    )
    result = subprocess.run(
        ["irule", "-r", RULE_ENGINE, rule, "null", "ruleExecOut"],
        capture_output=True, text=True, encoding="utf-8",
    )
    if result.returncode:
        details = "\n".join(part.strip() for part in (result.stderr, result.stdout) if part.strip())
        raise RuntimeError("{} exited with status {}: {}".format(name, result.returncode, details))
    try:
        return json.loads(result.stdout)
    except ValueError as error:
        raise ValueError("{} returned invalid JSON: {!r}".format(name, result.stdout)) from error


def process_users(output_dir, timestamp, dry_run, logger):
    failures = []
    deleted = 0
    would_attempt = 0
    users = []

    def record_failure(username, stage, error):
        failure = "user={!r}, stage={}: {}".format(username, stage, error)
        failures.append(failure)
        logger.error("%s", failure)

    try:
        pending = run_rule("get_all_users_pending_deletion")
        if not isinstance(pending, list) or any(not isinstance(user, str) or not user for user in pending):
            raise ValueError("Expected a JSON list of nonempty usernames")
        users = list(dict.fromkeys(pending))
    except (OSError, ValueError, RuntimeError) as error:
        record_failure(None, "get_all_users_pending_deletion", error)

    logger.info("Found %d distinct pending-deletion users", len(users))
    for username in users:
        stage = "get_users_active_permissions"
        try:
            permissions = run_rule("get_users_active_permissions", username)
            if not isinstance(permissions, list) or any(not isinstance(item, dict) for item in permissions):
                raise ValueError("Expected a JSON list of project permission objects")

            stage = "save_permissions"
            filename = "user_permissions_{}_{}.json".format(quote(username, safe=""), timestamp)
            path = output_dir / filename
            with path.open("x", encoding="utf-8") as output:
                json.dump(permissions, output, indent=2, ensure_ascii=False)
                output.write("\n")
            logger.info("Saved permissions for %s to %s", username, path)

            if dry_run:
                would_attempt += 1
                logger.info("DRY RUN: would attempt deletion of %s", username)
                continue

            stage = "delete_user"
            result = run_rule("delete_user", username)
            if not isinstance(result, dict) or result.get("success") is not True or result.get("deleted_user") != username:
                raise ValueError("Deletion was not confirmed for {!r}: {!r}".format(username, result))
            deleted += 1
            logger.info("Deleted %s", username)
        except (OSError, ValueError, RuntimeError) as error:
            record_failure(username, stage, error)

    logger.info("Summary: pending=%d, deleted=%d, would_attempt=%d, failures=%d",
                len(users), deleted, would_attempt, len(failures))
    if failures:
        logger.error("Complete failure list:")
        for failure in failures:
            logger.error("%s", failure)
    return 1 if failures else 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true",
                        help="save permissions and report intended attempts without calling delete_user")
    parser.add_argument("--output-dir", type=Path, default=Path.cwd(),
                        help="directory for permissions files and the run log (default: current directory)")
    args = parser.parse_args(argv)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    logger = logging.getLogger("irodsDeletePendingUsers")
    logger.setLevel(logging.INFO)
    logger.propagate = False
    handlers = []
    try:
        args.output_dir.mkdir(parents=True, exist_ok=True)
        log_path = args.output_dir / "delete_pending_users_{}.log".format(timestamp)
        handlers = [logging.StreamHandler(), logging.FileHandler(log_path, mode="x", encoding="utf-8")]
        formatter = logging.Formatter("%(asctime)sZ %(levelname)s %(message)s", datefmt="%Y-%m-%dT%H:%M:%S")
        # Keep log timestamps in UTC, matching the report filenames.
        formatter.converter = time.gmtime
        for handler in handlers:
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        logger.info("Mode: %s; log: %s", "DRY RUN" if args.dry_run else "LIVE DELETION", log_path)
        return process_users(args.output_dir, timestamp, args.dry_run, logger)
    except OSError as error:
        print("Cannot initialize report directory/log: {}".format(error), file=sys.stderr)
        return 1
    finally:
        for handler in handlers:
            logger.removeHandler(handler)
            handler.close()


if __name__ == "__main__":
    sys.exit(main())
