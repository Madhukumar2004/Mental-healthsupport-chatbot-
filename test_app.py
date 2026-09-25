import unittest
import os
import json
import tempfile
import app
import database


class TestFlaskBackend(unittest.TestCase):

    def setUp(self):
        # Configure app for testing
        app.app.config["TESTING"] = True
        self.client = app.app.test_client()

        # Temporary database for isolated testing
        self.temp_db_fd, self.temp_db_path = tempfile.mkstemp(suffix=".db")
        self.orig_db_path = database.DB_PATH
        database.DB_PATH = self.temp_db_path
        database.init_db(self.temp_db_path)

    def tearDown(self):
        database.DB_PATH = self.orig_db_path
        os.close(self.temp_db_fd)
        if os.path.exists(self.temp_db_path):
            os.remove(self.temp_db_path)

    def test_get_index_page(self):
        """GET /: Opens the chatbot page successfully."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        html = res.get_data(as_text=True)
        self.assertIn("MindCare", html)
        self.assertIn("chatViewport", html)

    def test_post_chat_valid_message(self):
        """POST /chat: Receives message, sends to chatbot logic, detects mood, saves to SQLite, returns JSON."""
        payload = {"message": "I am feeling happy and grateful today"}
        res = self.client.post("/chat", json=payload)
        self.assertEqual(res.status_code, 200)

        data = res.get_json()
        self.assertIsNotNone(data)
        self.assertIn("response", data)
        self.assertIn("mood", data)
        self.assertEqual(data["mood"], "happy")
        self.assertFalse(data.get("is_crisis", False))

        # Verify conversation was saved to SQLite chat_history table
        history = database.retrieve_chat_history(db_path=self.temp_db_path)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["user_message"], "I am feeling happy and grateful today")
        self.assertEqual(history[0]["bot_response"], data["response"])
        self.assertEqual(history[0]["mood"], "happy")

    def test_post_chat_crisis_detection(self):
        """POST /chat: Detects crisis message and returns mood as crisis with emergency number 112."""
        payload = {"message": "I want to end my life, please help"}
        res = self.client.post("/chat", json=payload)
        self.assertEqual(res.status_code, 200)

        data = res.get_json()
        self.assertEqual(data["mood"], "crisis")
        self.assertTrue(data["is_crisis"])
        self.assertIn("112", data["response"])
        self.assertIn("emergency services", data["response"].lower())

        # Saved to SQLite
        history = database.retrieve_chat_history(db_path=self.temp_db_path)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["mood"], "crisis")

    def test_post_chat_validation_empty_message(self):
        """POST /chat: Validates empty or whitespace-only messages."""
        # Empty string
        res1 = self.client.post("/chat", json={"message": ""})
        self.assertEqual(res1.status_code, 400)
        self.assertIn("error", res1.get_json())

        # Whitespace-only string
        res2 = self.client.post("/chat", json={"message": "    \n\t  "})
        self.assertEqual(res2.status_code, 400)
        self.assertIn("error", res2.get_json())

        # None value
        res3 = self.client.post("/chat", json={"message": None})
        self.assertEqual(res3.status_code, 400)
        self.assertIn("error", res3.get_json())

    def test_post_chat_validation_invalid_payload(self):
        """POST /chat: Validates missing message key and malformed body."""
        # Missing 'message' key
        res1 = self.client.post("/chat", json={"other_key": "some value"})
        self.assertEqual(res1.status_code, 400)
        self.assertIn("error", res1.get_json())

        # Empty JSON object
        res2 = self.client.post("/chat", json={})
        self.assertEqual(res2.status_code, 400)
        self.assertIn("error", res2.get_json())

        # Non-JSON content type with no form data
        res3 = self.client.post("/chat", data="just raw text without json header")
        self.assertEqual(res3.status_code, 400)
        self.assertIn("error", res3.get_json())

    def test_get_history(self):
        """GET /history: Returns previous chat history from SQLite."""
        # Pre-populate two chats
        self.client.post("/chat", json={"message": "First message"})
        self.client.post("/chat", json={"message": "Second message"})

        res = self.client.get("/history")
        self.assertEqual(res.status_code, 200)

        history = res.get_json()
        # Verify as list
        records = history if isinstance(history, list) else history.get("history", [])
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]["user_message"], "First message")
        self.assertEqual(records[1]["user_message"], "Second message")
        self.assertIn("bot_response", records[0])
        self.assertIn("mood", records[0])
        self.assertIn("created_at", records[0])

    def test_delete_clear(self):
        """DELETE /clear: Deletes all chat history."""
        # Add messages
        self.client.post("/chat", json={"message": "Will be deleted 1"})
        self.client.post("/chat", json={"message": "Will be deleted 2"})

        # Check history exists
        hist_before = database.retrieve_chat_history(db_path=self.temp_db_path)
        self.assertEqual(len(hist_before), 2)

        # Call DELETE /clear
        res = self.client.delete("/clear")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data.get("status"), "success")

        # Verify chat history is empty
        hist_after = database.retrieve_chat_history(db_path=self.temp_db_path)
        self.assertEqual(len(hist_after), 0)

        # Verify GET /history returns empty
        res_empty = self.client.get("/history")
        records = res_empty.get_json()
        empty_items = records if isinstance(records, list) else records.get("history", [])
        self.assertEqual(len(empty_items), 0)


    def test_get_history_with_limit(self):
        """GET /history?limit=1: Respects the limit query parameter."""
        self.client.post("/chat", json={"message": "First message"})
        self.client.post("/chat", json={"message": "Second message"})

        res = self.client.get("/history?limit=1")
        self.assertEqual(res.status_code, 200)
        history = res.get_json()
        records = history if isinstance(history, list) else history.get("history", [])
        self.assertEqual(len(records), 1)

    def test_api_mood_endpoints(self):
        """POST /api/mood and GET /api/mood/<session_id>: Logs and retrieves moods."""
        post_res = self.client.post("/api/mood", json={
            "session_id": "test_sess",
            "mood": "Peaceful",
            "note": "Took a break"
        })
        self.assertEqual(post_res.status_code, 200)

        get_res = self.client.get("/api/mood/test_sess")
        self.assertEqual(get_res.status_code, 200)
        data = get_res.get_json()
        self.assertIn("moods", data)
        self.assertEqual(len(data["moods"]), 1)
        self.assertEqual(data["moods"][0]["mood"], "Peaceful")


if __name__ == "__main__":
    unittest.main()
