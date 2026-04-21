from __future__ import annotations

import shutil
import stat
import subprocess
import tempfile
import unittest
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MAKEFILE = ROOT / "Makefile"
README = ROOT / "README.md"
BOOTSTRAP = ROOT / "scripts" / "shell" / "bootstrap_git_config.sh"


class GitBootstrapContractsTests(unittest.TestCase):
    def test_makefile_bootstrap_target_uses_git_bootstrap_script(self) -> None:
        source = MAKEFILE.read_text(encoding="utf-8")

        self.assertIn("./scripts/shell/bootstrap_git_config.sh", source)
        self.assertIn("bootstrap-git: install-hooks", source)

    def test_readme_documents_bootstrap_git_and_status_compare_branches(self) -> None:
        source = README.read_text(encoding="utf-8")

        self.assertIn("make bootstrap-git", source)
        self.assertIn("status` comparisons against both `@{upstream}` and `@{push}`", source)

    def test_bootstrap_script_configures_git_254_repo_without_hookdir_pre_commit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            env = os.environ.copy()
            env["GIT_CONFIG_GLOBAL"] = os.devnull
            env["GIT_CONFIG_NOSYSTEM"] = "1"

            subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True, text=True, env=env)

            scripts_dir = repo / "scripts"
            shell_dir = scripts_dir / "shell"
            shell_dir.mkdir(parents=True)

            managed_pre_commit = scripts_dir / "pre-commit"
            managed_pre_commit.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
            managed_pre_commit.chmod(managed_pre_commit.stat().st_mode | stat.S_IXUSR)

            copied_bootstrap = shell_dir / "bootstrap_git_config.sh"
            shutil.copy2(BOOTSTRAP, copied_bootstrap)
            copied_bootstrap.chmod(copied_bootstrap.stat().st_mode | stat.S_IXUSR)

            subprocess.run([str(copied_bootstrap)], cwd=repo, check=True, capture_output=True, text=True, env=env)

            configured_hook = subprocess.run(
                ["git", "config", "--local", "--get", "hook.random-timer-pre-commit.command"],
                cwd=repo,
                check=True,
                capture_output=True,
                text=True,
                env=env,
            ).stdout.strip()
            self.assertEqual(Path(configured_hook).resolve(), managed_pre_commit.resolve())

            configured_events = subprocess.run(
                ["git", "config", "--local", "--get-all", "hook.random-timer-pre-commit.event"],
                cwd=repo,
                check=True,
                capture_output=True,
                text=True,
                env=env,
            ).stdout.splitlines()
            self.assertEqual(configured_events, ["pre-commit"])

            compare_branches = subprocess.run(
                ["git", "config", "--local", "--get", "status.compareBranches"],
                cwd=repo,
                check=True,
                capture_output=True,
                text=True,
                env=env,
            ).stdout.strip()
            self.assertEqual(compare_branches, "@{upstream} @{push}")

            hooks_dir = subprocess.run(
                ["git", "rev-parse", "--git-path", "hooks"],
                cwd=repo,
                check=True,
                capture_output=True,
                text=True,
                env=env,
            ).stdout.strip()
            self.assertFalse((repo / hooks_dir / "pre-commit").exists())


if __name__ == "__main__":
    unittest.main()
