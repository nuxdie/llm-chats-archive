from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from app.adapters import parse_export


class KimiCaptureShardTests(unittest.TestCase):
    def test_compact_shard_without_raw_pages_is_importable(self) -> None:
        payload = {
            "provider": "kimi",
            "schema_version": "kimi-capture-v1",
            "export_id": "example-export",
            "part": 2,
            "total_parts": 3,
            "history_groups": [
                {
                    "label": "This Month",
                    "items": [
                        {
                            "chat_id": "chat-1",
                            "title": "Compact shard",
                            "created_at": "2026-11-18T08:00:00Z",
                            "updated_at": "2026-11-18T08:01:00Z",
                        }
                    ],
                }
            ],
            "chats": [
                {
                    "chat_id": "chat-1",
                    "history": {
                        "chat_id": "chat-1",
                        "title": "Compact shard",
                        "group_label": "This Month",
                    },
                    "chat": {"name": "Compact shard"},
                    "message_pages": [],
                    "messages": [
                        {
                            "message_id": "message-1",
                            "role": "user",
                            "author_name": "You",
                            "created_at": "2026-11-18T08:00:00Z",
                            "text": "Export every conversation.",
                            "attachments": [],
                            "metadata": {},
                        },
                        {
                            "message_id": "message-2",
                            "role": "assistant",
                            "author_name": "Kimi",
                            "created_at": "2026-11-18T08:01:00Z",
                            "text": "The export is ready.",
                            "attachments": [
                                {
                                    "filename": "result.json",
                                    "mime_type": "application/json",
                                    "metadata": {
                                        "source": "kimi_remote_attachment",
                                        "source_url": "https://www.kimi.com/file/result.json",
                                    },
                                }
                            ],
                            "metadata": {"status": "completed"},
                        },
                    ],
                    "warnings": [],
                }
            ],
            "warnings": [],
        }

        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as temporary_directory:
            export_path = Path(temporary_directory) / "kimi-export-part-002-of-003.json"
            export_path.write_text(json.dumps(payload), encoding="utf-8")
            parsed = parse_export(export_path)

        self.assertEqual(parsed["provider"], "kimi")
        self.assertEqual(parsed["summary"]["conversation_count"], 1)
        self.assertEqual(parsed["summary"]["message_count"], 2)
        self.assertEqual(parsed["summary"]["attachment_count"], 1)

        conversation = parsed["conversations"][0]
        self.assertEqual(conversation["provider_conversation_id"], "chat-1")
        self.assertEqual(conversation["title"], "Compact shard")
        self.assertEqual(conversation["messages"][0]["text"], "Export every conversation.")
        attachment = conversation["messages"][1]["attachments"][0]
        self.assertEqual(attachment["filename"], "result.json")
        self.assertEqual(
            attachment["metadata"]["source_url"],
            "https://www.kimi.com/file/result.json",
        )


if __name__ == "__main__":
    unittest.main()
