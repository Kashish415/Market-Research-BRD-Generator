import asyncio
import unittest

import httpx

from market_research_agent.amp_api import extract_brd_text, get_status, start_execution


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
                return httpx.Response(200, json={"state": "SUCCESS", "result": "Final BRD"})

            transport = httpx.MockTransport(handler)
            async with httpx.AsyncClient(transport=transport) as client:
                return await get_status(
                    client,
                    "https://example.crewai.com",
                    "test-token",
                    "test-id",
                )

        status = asyncio.run(run_test())
        self.assertEqual(status["state"], "SUCCESS")

    def test_extract_brd_text_supports_result_and_result_json(self):
        self.assertEqual(
            extract_brd_text({"result": "BRD from result"}),
            "BRD from result",
        )
        self.assertEqual(
            extract_brd_text({"result_json": {"output": "BRD from JSON"}}),
            "BRD from JSON",
        )


if __name__ == "__main__":
    unittest.main()
