"""TDD: OpenAI-hosted sandbox environment policy for the agent fleet."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.agent_openai_hosted_env import (
    FLEET_MONTHLY_CAP_USD,
    WORKSPACE_OUTPUTS,
    build_session_request,
    evaluate_budget_for_hosted,
    evaluate_environment_status,
    evaluate_network_policy,
    evaluate_platform,
    evaluate_reserved_env,
    evaluate_restricted_domains,
    evaluate_setup_result,
    evaluate_template_network_inheritance,
    prefer_local_or_hosted,
    publish_outputs_to_vault,
    validate_hosted_environment,
)


class PlatformTests(unittest.TestCase):
    def test_openai_hosted_allowed(self) -> None:
        d = evaluate_platform(platform="openai_hosted")
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_openai_hosted")

    def test_unmanaged_raw_container_blocked(self) -> None:
        d = evaluate_platform(platform="unmanaged_raw_container_admin")
        self.assertFalse(d.ok)


class NetworkPolicyTests(unittest.TestCase):
    def test_disabled_is_default_safe(self) -> None:
        d = evaluate_network_policy(access="disabled")
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_network_disabled")

    def test_restricted_requires_exact_hosts(self) -> None:
        bad = evaluate_restricted_domains(
            domains=["https://api.example.com/v1", "*.example.com", "api.example.com:443"]
        )
        self.assertFalse(bad.ok)
        good = evaluate_restricted_domains(domains=["api.example.com", "cdn.jsdelivr.net"])
        self.assertTrue(good.ok)

    def test_restricted_empty_denied(self) -> None:
        d = evaluate_network_policy(access="restricted", allowed_domains=[])
        self.assertFalse(d.ok)


class EnvVarTests(unittest.TestCase):
    def test_runtime_reserved_env_rejected(self) -> None:
        d = evaluate_reserved_env(
            env={"OPENAI_API_KEY": "sk-test", "PATH": "/bin", "REPORT_DIR": "reports"}
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_reserved_env")

    def test_app_env_allowed(self) -> None:
        d = evaluate_reserved_env(env={"REPORT_DIR": "reports", "TASK_ID": "t1"})
        self.assertTrue(d.ok)


class SetupAndStatusTests(unittest.TestCase):
    def test_nonzero_setup_blocks_agent_start(self) -> None:
        d = evaluate_setup_result(exit_status=1)
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_setup_failed")

    def test_files_require_connected(self) -> None:
        provisioning = evaluate_environment_status(status="provisioning")
        self.assertFalse(provisioning.ok)
        self.assertEqual(provisioning.action, "wait_for_connected")
        connected = evaluate_environment_status(status="connected")
        self.assertTrue(connected.ok)


class TemplateInheritanceTests(unittest.TestCase):
    def test_cannot_broaden_template_network(self) -> None:
        d = evaluate_template_network_inheritance(
            template_access="disabled",
            session_access="enabled",
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_network_policy_broaden")


class BudgetAndRoutingTests(unittest.TestCase):
    def test_fleet_cap(self) -> None:
        self.assertEqual(FLEET_MONTHLY_CAP_USD, 20.0)

    def test_budget_blocks_hosted_when_exhausted(self) -> None:
        d = evaluate_budget_for_hosted(
            month_to_date_spend_usd=FLEET_MONTHLY_CAP_USD,
            estimated_session_usd=0.5,
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_hosted_budget")

    def test_prefer_local_when_no_hosted_need(self) -> None:
        d = prefer_local_or_hosted(
            needs_isolated_linux=False,
            needs_downloadable_outputs=True,
            private_data=True,
        )
        self.assertEqual(d.action, "prefer_local_workspace")
        self.assertTrue(d.ok)

    def test_hosted_when_isolated_linux_needed_under_budget(self) -> None:
        d = prefer_local_or_hosted(
            needs_isolated_linux=True,
            needs_downloadable_outputs=True,
            private_data=False,
            month_to_date_spend_usd=1.0,
            estimated_session_usd=0.5,
        )
        self.assertEqual(d.action, "allow_openai_hosted_session")
        self.assertTrue(d.ok)


class RequestBuilderTests(unittest.TestCase):
    def test_build_session_defaults_network_disabled_and_outputs_contract(self) -> None:
        req = build_session_request(
            model="gpt-6-astra",
            input_text="sum amounts.csv into outputs/summary.json",
            inline_files=[
                {
                    "path": "/workspace/amounts.csv",
                    "data_b64": "YW1vdW50CjEwCjIwCjMwCg==",
                }
            ],
            packages={"python": ["pandas==2.2.3"]},
            setup_commands=[{"command": "mkdir -p reports"}],
        )
        self.assertEqual(req["environment"]["type"], "openai_hosted")
        self.assertEqual(req["environment"]["network"]["access"], "disabled")
        self.assertEqual(req["workspace_outputs"], WORKSPACE_OUTPUTS)
        self.assertNotIn("OPENAI_API_KEY", req["environment"].get("env", {}))

    def test_validate_rejects_enabled_without_budget_headroom(self) -> None:
        d = validate_hosted_environment(
            network_access="enabled",
            allowed_domains=[],
            env={"TASK": "x"},
            month_to_date_spend_usd=19.8,
            estimated_session_usd=1.0,
        )
        self.assertFalse(d.ok)


class OutputsVaultTests(unittest.TestCase):
    def test_publish_outputs_into_artifact_vault(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "outputs"
            out.mkdir()
            (out / "summary.json").write_text('{"total": 60}\n', encoding="utf-8")
            vault = Path(tmp) / "vault"
            published = publish_outputs_to_vault(
                vault_root=vault,
                run_id="hosted-summary",
                outputs_dir=out,
                tool_trace=[{"tool": "python", "query": "sum"}],
                generated_code="print(60)\n",
                pre_compaction_text="session transcript",
            )
            self.assertTrue(published["ok"])
            recalled_path = vault / "hosted-summary" / "summary.json"
            self.assertTrue(recalled_path.exists())
            self.assertIn("60", recalled_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
