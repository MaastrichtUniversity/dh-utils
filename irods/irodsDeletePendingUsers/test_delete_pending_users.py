"""Offline tests: every irule invocation is mocked; no iRODS login is needed."""

from contextlib import redirect_stderr
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import delete_pending_users as utility


class DeletePendingUsersTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.output = Path(self.directory.name) / "report"
        self.console = io.StringIO()
        self.calls = []

    def run_script(self, pending, responses=None, dry_run=False):
        responses = responses or {}

        def irule(command, **kwargs):
            self.assertEqual(command[:3], ["irule", "-r", utility.RULE_ENGINE])
            self.assertEqual(command[4:], ["null", "ruleExecOut"])
            self.assertNotIn("shell", kwargs)
            prefix = "test_rule_output("
            self.assertTrue(command[3].startswith(prefix))
            self.assertTrue(command[3].endswith(")"))
            name, arguments = json.loads("[" + command[3][len(prefix):-1] + "]")
            username = arguments if arguments else None
            self.calls.append((name, username))
            if name == "get_all_users_pending_deletion":
                response = pending
            else:
                default = [] if name == "get_users_active_permissions" else {"success": True, "deleted_user": username}
                response = responses.get((name, username), default)
            if isinstance(response, Exception):
                raise response
            if isinstance(response, subprocess.CompletedProcess):
                return response
            return subprocess.CompletedProcess(command, 0, json.dumps(response), "")

        args = ["--output-dir", str(self.output)] + (["--dry-run"] if dry_run else [])
        with patch.object(utility.subprocess, "run", side_effect=irule), redirect_stderr(self.console):
            return utility.main(args)

    def permissions_file(self, username):
        files = list(self.output.glob("user_permissions_{}_*.json".format(username)))
        self.assertEqual(len(files), 1)
        return files[0]

    def test_saves_nonempty_permissions_before_deletion(self):
        permissions = [{"project": "/nlmumc/projects/P000000001", "username": "alice",
                        "user_id": "10001", "access": "read"}]
        real_run_rule = utility.run_rule

        def check_saved(name, username=None):
            if name == "delete_user":
                self.assertEqual(json.loads(self.permissions_file(username).read_text()), permissions)
            return real_run_rule(name, username)

        with patch.object(utility, "run_rule", side_effect=check_saved):
            code = self.run_script(["alice"], {("get_users_active_permissions", "alice"): permissions})
        self.assertEqual(code, 0)
        self.assertEqual(self.calls, [("get_all_users_pending_deletion", None),
                                    ("get_users_active_permissions", "alice"), ("delete_user", "alice")])
        report = self.permissions_file("alice")
        timestamp = report.stem[len("user_permissions_alice_"):]
        self.assertRegex(timestamp, r"^\d{8}T\d{12}Z$")
        self.assertTrue((self.output / ("delete_pending_users_" + timestamp + ".log")).is_file())
        self.assertIn("deleted=1", self.console.getvalue())

    def test_dry_run_saves_all_permissions_without_deleting(self):
        self.assertEqual(self.run_script(["alice", "bob"], dry_run=True), 0)
        self.assertEqual(len(self.calls), 3)
        self.assertFalse(any(name == "delete_user" for name, user in self.calls))
        for user in ("alice", "bob"):
            self.assertEqual(json.loads(self.permissions_file(user).read_text()), [])
        self.assertIn("would attempt deletion of alice", self.console.getvalue())
        self.assertIn("would_attempt=2", self.console.getvalue())

    def test_empty_list(self):
        self.assertEqual(self.run_script([]), 0)
        self.assertEqual(self.calls, [("get_all_users_pending_deletion", None)])
        self.assertEqual(list(self.output.glob("*.json")), [])

    def test_duplicate_users_are_only_processed_once_in_order(self):
        self.assertEqual(self.run_script(["bob", "alice", "bob"]), 0)
        self.assertEqual([user for name, user in self.calls if name == "delete_user"], ["bob", "alice"])

    def test_deletion_failure_retains_permissions_and_continues(self):
        failure = subprocess.CompletedProcess([], 4, "server output", "User is not valid for deletion")
        code = self.run_script(["alice", "bob"], {("delete_user", "alice"): failure})
        self.assertEqual(code, 1)
        self.permissions_file("alice")
        self.assertIn(("delete_user", "bob"), self.calls)
        log = next(self.output.glob("*.log")).read_text()
        for text in ("Complete failure list", "user='alice', stage=delete_user", "status 4",
                     "User is not valid for deletion", "server output", "deleted=1"):
            self.assertIn(text, log)
            self.assertIn(text, self.console.getvalue())

    def test_permission_read_failure_prevents_deletion_and_continues(self):
        code = self.run_script(["alice", "bob"], {
            ("get_users_active_permissions", "alice"): subprocess.CompletedProcess([], 1, "", "denied")})
        self.assertEqual(code, 1)
        self.assertNotIn(("delete_user", "alice"), self.calls)
        self.assertIn(("delete_user", "bob"), self.calls)
        self.assertEqual(list(self.output.glob("user_permissions_alice_*")), [])

    def test_permission_write_failure_prevents_deletion_and_continues(self):
        real_open = Path.open

        def open_file(path, *args, **kwargs):
            if path.name.startswith("user_permissions_alice_"):
                raise OSError("disk full")
            return real_open(path, *args, **kwargs)

        with patch.object(Path, "open", open_file):
            self.assertEqual(self.run_script(["alice", "bob"]), 1)
        self.assertNotIn(("delete_user", "alice"), self.calls)
        self.assertIn(("delete_user", "bob"), self.calls)
        self.assertIn("stage=save_permissions: disk full", self.console.getvalue())

    def test_pending_list_errors_abort_before_processing(self):
        for pending in ({}, ["alice", 123], [""],
                        subprocess.CompletedProcess([], 0, "not JSON", ""),
                        subprocess.CompletedProcess([], 1, "", "connection failed"),
                        FileNotFoundError("irule not found")):
            with self.subTest(pending=pending):
                self.calls.clear()
                self.assertEqual(self.run_script(pending), 1)
                self.assertEqual(self.calls, [("get_all_users_pending_deletion", None)])

    def test_malformed_permissions_prevent_deletion(self):
        for response in ({}, ["not a permission object"], subprocess.CompletedProcess([], 0, "invalid", "")):
            with self.subTest(response=response):
                self.calls.clear()
                self.assertEqual(self.run_script(["alice"], {("get_users_active_permissions", "alice"): response}), 1)
                self.assertNotIn(("delete_user", "alice"), self.calls)

    def test_unconfirmed_or_malformed_deletions_are_failures(self):
        for response in ({"success": False}, {"success": True, "deleted_user": "someone_else"},
                         [], subprocess.CompletedProcess([], 0, "invalid", "")):
            with self.subTest(response=response):
                self.calls.clear()
                self.assertEqual(self.run_script(["alice", "bob"], {("delete_user", "alice"): response}), 1)
                self.assertIn(("delete_user", "bob"), self.calls)

    def test_invocations_match_documented_run_test_examples(self):
        with patch.object(utility.subprocess, "run",
                          return_value=subprocess.CompletedProcess([], 0, "[]", "")) as run:
            for name, username, expression in (
                ("get_all_users_pending_deletion", None,
                 'test_rule_output("get_all_users_pending_deletion", "")'),
                ("get_users_active_permissions", "dlinssen",
                 'test_rule_output("get_users_active_permissions", "dlinssen")'),
                ("delete_user", "jmelius", 'test_rule_output("delete_user", "jmelius")'),
            ):
                with self.subTest(name=name):
                    utility.run_rule(name, username)
                    run.assert_called_with(
                        ["irule", "-r", utility.RULE_ENGINE, expression, "null", "ruleExecOut"],
                        capture_output=True, text=True, encoding="utf-8",
                    )

    def test_usernames_are_quoted_and_safe_filenames(self):
        username = '../a"b\\c;$(touch nope)'
        self.assertEqual(self.run_script([username]), 0)
        self.assertIn(("delete_user", username), self.calls)
        files = list(self.output.glob("user_permissions_*.json"))
        self.assertEqual(len(files), 1)
        self.assertIn("%2F", files[0].name)
        self.assertEqual(files[0].parent, self.output)
        with patch.object(utility.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, "[]", "")) as run:
            utility.run_rule("get_users_active_permissions", username)
            self.assertEqual(run.call_args.args[0][3],
                             'test_rule_output("get_users_active_permissions", "../a\\"b\\\\c;$(touch nope)")')
            self.assertEqual(run.call_args.args[0][4], "null")

    def test_dispatcher_argument_separator_cannot_introduce_extra_arguments(self):
        self.assertEqual(self.run_script(["alice,bob", "bob"]), 1)
        self.assertNotIn(("get_users_active_permissions", "alice,bob"), self.calls)
        self.assertNotIn(("delete_user", "alice,bob"), self.calls)
        self.assertIn(("delete_user", "bob"), self.calls)
        self.assertIn("without commas", self.console.getvalue())

    def test_unwritable_output_location_does_not_call_irule(self):
        self.output.write_text("not a directory")
        with patch.object(utility.subprocess, "run") as run, redirect_stderr(self.console):
            self.assertEqual(utility.main(["--output-dir", str(self.output)]), 1)
        run.assert_not_called()
        self.assertIn("Cannot initialize", self.console.getvalue())


if __name__ == "__main__":
    unittest.main()
