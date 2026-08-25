import asyncio
import os
import time
import unittest
from unittest import mock

from aiohttp import web

from openrouter_simple.cancellation import NodeDeadline, NodeTimeoutError
from openrouter_simple.client import OpenRouterRequestError, create_chat, lookup_credits


class ClientTests(unittest.IsolatedAsyncioTestCase):
    async def start_server(self, routes):
        app = web.Application()
        for method, path, handler in routes:
            app.router.add_route(method, path, handler)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "127.0.0.1", 0)
        await site.start()
        port = site._server.sockets[0].getsockname()[1]
        self.addAsyncCleanup(runner.cleanup)
        return f"http://127.0.0.1:{port}"

    async def test_stalled_chat_obeys_total_deadline(self):
        release = asyncio.Event()

        async def stalled(_request):
            await release.wait()
            return web.json_response({"choices": [{"message": {"content": "late"}}]})

        base = await self.start_server([("POST", "/chat/completions", stalled)])
        started = time.monotonic()
        try:
            with mock.patch.dict(os.environ, {"OPENROUTER_BASE_URL": base}):
                with self.assertRaises(NodeTimeoutError):
                    await create_chat(NodeDeadline(0.2, poll_interval=0.02), {"model": "x"}, "secret")
        finally:
            release.set()
        self.assertLess(time.monotonic() - started, 1.0)

    async def test_rejection_is_friendly_and_redacted(self):
        secret = "sk-or-v1-SUPERSECRET"

        async def rejected(_request):
            return web.json_response({"error": {"message": f"bad Bearer {secret}"}}, status=401)

        base = await self.start_server([("POST", "/chat/completions", rejected)])
        with mock.patch.dict(os.environ, {"OPENROUTER_BASE_URL": base}):
            with self.assertRaises(OpenRouterRequestError) as raised:
                await create_chat(NodeDeadline(2), {"model": "x"}, secret)
        message = str(raised.exception)
        self.assertIn("authentication failed", message)
        self.assertNotIn(secret, message)
        self.assertIn("[REDACTED]", message)

    async def test_credits_failure_is_non_fatal(self):
        async def failed(_request):
            return web.json_response({}, status=500)

        base = await self.start_server([("GET", "/key", failed)])
        with mock.patch.dict(os.environ, {"OPENROUTER_BASE_URL": base}, clear=False):
            with mock.patch.dict(os.environ, {"OPENROUTER_MANAGEMENT_KEY": ""}, clear=False):
                result = await lookup_credits(NodeDeadline(1), "generation-key")
        self.assertTrue(result.startswith("Credits unavailable"))


if __name__ == "__main__":
    unittest.main()
