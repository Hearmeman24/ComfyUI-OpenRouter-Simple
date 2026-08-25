import asyncio
import shutil
import tempfile
import unittest
from pathlib import Path

import torch

from openrouter_simple.cancellation import NodeDeadline, run_process
from openrouter_simple.media import (
    AUDIO_LIMIT,
    IMAGE_LIMIT,
    VIDEO_LIMIT,
    prepare_audio,
    prepare_image,
    prepare_video,
)


class FileVideo:
    def __init__(self, path: str):
        self.path = path

    def get_stream_source(self):
        return self.path

    def get_active_trim_window(self):
        return 0.0, 0.0


class MediaIntegrationTests(unittest.IsolatedAsyncioTestCase):
    async def test_image_is_webp_below_cap(self):
        image = torch.rand((1, 1024, 1024, 3))
        prepared = await prepare_image(NodeDeadline(15), image)
        self.assertEqual(prepared.mime_type, "image/webp")
        self.assertLessEqual(len(prepared.data), IMAGE_LIMIT)

    async def test_audio_is_mp3_below_cap(self):
        sample_rate = 48_000
        waveform = torch.sin(torch.arange(sample_rate * 3) * (440 * 2 * torch.pi / sample_rate)).reshape(1, 1, -1)
        prepared = await prepare_audio(
            NodeDeadline(15), {"waveform": waveform, "sample_rate": sample_rate}
        )
        self.assertEqual(prepared.mime_type, "audio/mpeg")
        self.assertLessEqual(len(prepared.data), AUDIO_LIMIT)

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "ffmpeg is required")
    async def test_video_is_mp4_below_cap(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.mp4"
            await run_process(
                NodeDeadline(15),
                shutil.which("ffmpeg"),
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
                "-f",
                "lavfi",
                "-i",
                "testsrc2=size=640x360:rate=24",
                "-f",
                "lavfi",
                "-i",
                "sine=frequency=440:sample_rate=48000",
                "-t",
                "1.5",
                "-c:v",
                "libx264",
                "-c:a",
                "aac",
                str(source),
            )
            prepared = await prepare_video(NodeDeadline(30), FileVideo(str(source)))
        self.assertEqual(prepared.mime_type, "video/mp4")
        self.assertLessEqual(len(prepared.data), VIDEO_LIMIT)


if __name__ == "__main__":
    unittest.main()
