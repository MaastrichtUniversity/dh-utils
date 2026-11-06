#!/usr/bin/env python3
"""Restore saved project permissions to an existing iRODS user via ichmod."""

import argparse
import json
from pathlib import Path
import shlex
import subprocess
import sys


ACCESS_LEVELS = {
    "read": "read",
    "read_object": "read",
    "read object": "read",
    "modify": "write",
    "modify_object": "write",
    "modify object": "write",
    "write": "write",
    "own": "own",
}


def load_permissions(path):
    """Validate the entire backup before changing any permissions."""
    with path.open(encoding="utf-8") as source:
        permissions = json.load(source)
    if not isinstance(permissions, list):
        raise ValueError("Expected a JSON list of project permission objects")

    projects = {}
    for index, permission in enumerate(permissions, start=1):
        if not isinstance(permission, dict):
            raise ValueError("Entry {} must be a project permission object".format(index))
        project = permission.get("project")
        parts = project.split("/") if isinstance(project, str) else []
        if (len(parts) != 4 or parts[0] != "" or parts[2] != "projects"
                or any(part in ("", ".", "..") for part in parts[1:])):
            raise ValueError("Entry {} requires a project path /<zone>/projects/<project>".format(index))
        access = permission.get("access")
        if not isinstance(access, str) or access not in ACCESS_LEVELS:
            raise ValueError("Entry {} has unsupported access: {!r}".format(index, access))
        level = ACCESS_LEVELS[access]
        if project in projects and projects[project] != level:
            raise ValueError("Conflicting permissions for {}".format(project))
        projects[project] = level
    return projects


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("permissions_file", type=Path, help="JSON permissions backup")
    parser.add_argument("username", help="existing target username (optionally user#zone)")
    parser.add_argument("--dry-run", action="store_true",
                        help="print commands without running ichmod or connecting to iRODS")
    args = parser.parse_args(argv)
    if not args.username.strip() or args.username.startswith("-"):
        parser.error("username must be nonempty and must not start with '-'")

    try:
        projects = load_permissions(args.permissions_file)
    except (OSError, ValueError) as error:
        print("Cannot load permissions: {}".format(error), file=sys.stderr)
        return 1

    restored = 0
    for project, access in projects.items():
        commands = [["ichmod", "-M", "-r", "read", args.username, project]]
        if access != "read":
            commands.append(["ichmod", "-M", access, args.username, project])
        for command in commands:
            print("{}{}".format("DRY RUN: " if args.dry_run else "", shlex.join(command)), flush=True)
            if args.dry_run:
                continue
            try:
                subprocess.run(command, check=True)
            except (OSError, subprocess.CalledProcessError) as error:
                print("Restore stopped: {}. Permissions may be partially applied; "
                      "review the commands above before retrying.".format(error), file=sys.stderr)
                return 1
        restored += 1

    print("{} {} project(s) for {!r}.".format(
        "Would restore" if args.dry_run else "Restored", restored, args.username,
    ))
    return 0


if __name__ == "__main__":
    sys.exit(main())
