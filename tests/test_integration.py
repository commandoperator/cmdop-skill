"""Full end-to-end integration tests simulating a real skill."""

from __future__ import annotations

import json
import subprocess
import sys
import textwrap
import tempfile
import os

import pytest

from cmdop_skill import Arg, Skill, TestClient, generate_manifest


class TestMiniSkillEndToEnd:
    """Define a complete mini-skill and verify all operations."""

    @pytest.fixture
    def email_skill(self) -> Skill:
        skill = Skill(
            name="test-email",
            description="Test email skill",
            version="1.0.0",
            auto_sys_path=False,
        )
        sent: list[dict] = []

        @skill.setup
        async def setup():
            sent.clear()

        @skill.teardown
        async def teardown():
            pass

        @skill.command
        async def send(
            to: str = Arg(help="Recipient(s)", required=True),
            subject: str = Arg(required=True),
            body: str = Arg(required=True),
            from_account: str = Arg("--from", default=""),
        ) -> dict:
            """Send an email immediately."""
            msg = {"to": to, "subject": subject, "body": body, "from": from_account}
            sent.append(msg)
            return {"sent": True, "message_id": f"msg-{len(sent)}"}

        @skill.command
        async def accounts() -> dict:
            """List available accounts."""
            return {"accounts": ["work@example.com", "personal@example.com"]}

        @skill.command
        def health() -> dict:
            """Check service health."""
            return {"ok": True, "status": "healthy"}

        @skill.command
        async def stats() -> dict:
            """Show send statistics."""
            return {"ok": True, "total_sent": len(sent)}

        skill._sent = sent  # type: ignore[attr-defined]
        return skill

    async def test_send_command(self, email_skill: Skill) -> None:
        async with TestClient(email_skill) as client:
            result = await client.run(
                "send",
                to="test@example.com",
                subject="Test",
                body="Hello",
                from_account="me@example.com",
            )
            assert result["ok"] is True
            assert result["sent"] is True
            assert result["message_id"] == "msg-1"

    async def test_accounts_command(self, email_skill: Skill) -> None:
        client = TestClient(email_skill)
        result = await client.run("accounts")
        assert result["ok"] is True
        assert len(result["accounts"]) == 2

    async def test_sync_health_command(self, email_skill: Skill) -> None:
        client = TestClient(email_skill)
        result = await client.run("health")
        assert result["ok"] is True
        assert result["status"] == "healthy"

    async def test_cli_interface(self, email_skill: Skill) -> None:
        client = TestClient(email_skill)
        result = await client.run_cli(
            "send", "--to", "x@y.com", "--subject", "Hi", "--body", "Hey", "--from", "me"
        )
        assert result["ok"] is True
        assert result["sent"] is True

    async def test_lifecycle_order(self, email_skill: Skill) -> None:
        """Setup clears sent list, so stats should show 0 initially."""
        async with TestClient(email_skill) as client:
            result = await client.run("stats")
            assert result["total_sent"] == 0

            await client.run("send", to="a@b.com", subject="S", body="B", from_account="")
            result = await client.run("stats")
            assert result["total_sent"] == 1

    async def test_multiple_sends(self, email_skill: Skill) -> None:
        async with TestClient(email_skill) as client:
            await client.run("send", to="a@b.com", subject="S1", body="B1", from_account="")
            await client.run("send", to="c@d.com", subject="S2", body="B2", from_account="")
            result = await client.run("stats")
            assert result["total_sent"] == 2

    def test_manifest_generation(self, email_skill: Skill) -> None:
        md = generate_manifest(email_skill)
        assert "name: test-email" in md
        assert "### `send`" in md
        assert "### `accounts`" in md
        assert "### `health`" in md
        assert "### `stats`" in md
        assert "| `--to` |" in md
        assert "| `--subject` |" in md

    def test_parser_structure(self, email_skill: Skill) -> None:
        parser = email_skill.build_parser()
        # Should parse valid args without error
        ns = parser.parse_args(["send", "--to", "x@y.com", "--subject", "S", "--body", "B"])
        assert ns.command == "send"
        assert ns.to == "x@y.com"

    def test_parser_from_flag(self, email_skill: Skill) -> None:
        parser = email_skill.build_parser()
        ns = parser.parse_args(["send", "--to", "x", "--subject", "s", "--body", "b", "--from", "me"])
        assert ns.from_ == "me"


class TestSubprocessExecution:
    """Test that a skill works when executed as a subprocess."""

    def test_subprocess_json_output(self, tmp_path: object) -> None:
        """Write a mini skill script and run it in a subprocess."""
        # Find the cmdop_skill package source
        pkg_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        src_dir = os.path.join(pkg_dir, "src")

        script = textwrap.dedent(f"""\
            import sys
            sys.path.insert(0, {src_dir!r})
            from cmdop_skill import Skill, Arg

            skill = Skill(name="sub-test", version="0.1.0", auto_sys_path=False)

            @skill.command
            def echo(msg: str = Arg(required=True)) -> dict:
                \"\"\"Echo a message.\"\"\"
                return {{"echo": msg}}

            if __name__ == "__main__":
                skill.run()
        """)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(script)
            script_path = f.name

        try:
            result = subprocess.run(
                [sys.executable, script_path, "echo", "--msg", "hello world"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            assert result.returncode == 0, f"stderr: {result.stderr}"
            data = json.loads(result.stdout)
            assert data["ok"] is True
            assert data["echo"] == "hello world"
        finally:
            os.unlink(script_path)
