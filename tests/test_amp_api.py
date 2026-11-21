import asyncio
import unittest

import httpx

from market_research_agent.amp_api import (
    extract_brd_text,
    get_status,
    normalize_execution_status,
    progress_summary,
    start_execution,
)


class AmpApiTests(unittest.TestCase):
    def test_kickoff_sends_inputs_and_returns_kickoff_id(self):
        async def run_test():
            async def handler(request: httpx.Request) -> httpx.Response:
                self.assertEqual(request.url.path, "/kickoff")
                self.assertEqual(request.headers["authorization"], "Bearer test-token")
                self.assertEqual(
                    request.content,
                    b'{"inputs":{"project_brief":"Test idea","additional_context":"Test context"}}',
                )
                return httpx.Response(200, json={"kickoff_id": "test-id"})

            transport = httpx.MockTransport(handler)
            async with httpx.AsyncClient(transport=transport) as client:
                return await start_execution(
                    client,
                    "https://example.crewai.com",
                    "test-token",
                    {
                        "project_brief": "Test idea",
                        "additional_context": "Test context",
                    },
                )

        self.assertEqual(asyncio.run(run_test()), "test-id")

    def test_status_request_uses_kickoff_id(self):
        async def run_test():
            async def handler(request: httpx.Request) -> httpx.Response:
                self.assertEqual(request.url.path, "/status/test-id")
                return httpx.Response(
                    200,
                    json={
                        "status": "completed",
                        "progress": {
                            "completed_tasks": 5,
                            "total_tasks": 5,
                        },
                        "result": {"output": "Final BRD"},
                    },
                )

            transport = httpx.MockTransport(handler)
            async with httpx.AsyncClient(transport=transport) as client:
                return await get_status(
                    client,
                    "https://example.crewai.com",
                    "test-token",
                    "test-id",
                )

        status = asyncio.run(run_test())
        self.assertEqual(normalize_execution_status(status), "completed")
        self.assertEqual(progress_summary(status), "5/5 tasks")

    def test_extract_brd_text_supports_result_and_result_json(self):
        self.assertEqual(
            extract_brd_text({"result": "BRD from result"}),
            "BRD from result",
        )
        self.assertEqual(
            extract_brd_text({"result_json": {"output": "BRD from JSON"}}),
            "BRD from JSON",
        )

    def test_status_supports_new_state_format(self):
        self.assertEqual(
            normalize_execution_status({"state": "RUNNING"}),
            "running",
        )
        self.assertEqual(
            normalize_execution_status({"state": "SUCCESS"}),
            "completed",
        )

    def test_progress_supports_new_field_names(self):
        summary = progress_summary(
            {
                "progress": {
                    "completed": 3,
                    "total": 5,
                    "current": "Business Requirements",
                }
            }
        )
        self.assertEqual(summary, "3/5 tasks | Business Requirements")


if __name__ == "__main__":
    unittest.main()
