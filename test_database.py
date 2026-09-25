import unittest
import os
import sqlite3
import tempfile
import database
from database import (
    init_db,
    save_chat,
    retrieve_chat_history,
    clear_chat_history,
    get_chat_history,
    get_db_connection,
    DB_PATH,
    DB_DIR,
)


class TestDatabaseLogic(unittest.TestCase):

    def setUp(self):
        # Create a temporary database for test isolation
        self.temp_db_fd, self.temp_db_path = tempfile.mkstemp(suffix=".db")
        init_db(self.temp_db_path)

    def tearDown(self):
        os.close(self.temp_db_fd)
        if os.path.exists(self.temp_db_path):
            os.remove(self.temp_db_path)

    def test_database_path_and_directory(self):
        """Verify default database path points to database/chatbot.db."""
        expected_suffix = os.path.join("database", "chatbot.db")
        self.assertTrue(DB_PATH.endswith(expected_suffix))
        self.assertTrue(os.path.exists(DB_DIR))

    def test_automatic_database_creation(self):
        """Verify database and directory are created automatically."""
        # Clean default DB if exists to test auto-creation
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)
        init_db()
        self.assertTrue(os.path.exists(DB_PATH))

    def test_chat_history_table_schema(self):
        """Verify table chat_history has columns: id, user_message, bot_response, mood, created_at."""
        conn = get_db_connection(self.temp_db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(chat_history)")
        columns = {row["name"]: row["type"] for row in cursor.fetchall()}
        conn.close()

        expected_columns = ["id", "user_message", "bot_response", "mood", "created_at"]
        for col in expected_columns:
            self.assertIn(col, columns, f"Column '{col}' missing from chat_history schema")

    def test_save_chat_and_retrieve_history(self):
        """Verify save_chat stores messages and retrieve_chat_history fetches them."""
        # 1. Insert chat 1
        id1 = save_chat(
            user_message="Hello, I feel stressed",
            bot_response="Take a deep breath, you are not alone.",
            mood="stressed",
            db_path=self.temp_db_path
        )
        self.assertIsInstance(id1, int)
        self.assertGreater(id1, 0)

        # 2. Insert chat 2
        id2 = save_chat(
            user_message="Thank you for helping",
            bot_response="You are very welcome!",
            mood="happy",
            db_path=self.temp_db_path
        )
        self.assertIsInstance(id2, int)
        self.assertGreater(id2, id1)

        # 3. Retrieve history
        history = retrieve_chat_history(db_path=self.temp_db_path)
        self.assertEqual(len(history), 2)

        # Verify record 1
        self.assertEqual(history[0]["id"], id1)
        self.assertEqual(history[0]["user_message"], "Hello, I feel stressed")
        self.assertEqual(history[0]["bot_response"], "Take a deep breath, you are not alone.")
        self.assertEqual(history[0]["mood"], "stressed")
        self.assertIsNotNone(history[0]["created_at"])

        # Verify record 2
        self.assertEqual(history[1]["id"], id2)
        self.assertEqual(history[1]["user_message"], "Thank you for helping")
        self.assertEqual(history[1]["bot_response"], "You are very welcome!")
        self.assertEqual(history[1]["mood"], "happy")
        self.assertIsNotNone(history[1]["created_at"])

    def test_save_chat_with_crisis_mood(self):
        """Verify saving a crisis chat correctly records crisis mood."""
        row_id = save_chat(
            user_message="I want to end my life",
            bot_response="Please call 112 immediately.",
            mood="crisis",
            db_path=self.temp_db_path
        )
        history = retrieve_chat_history(db_path=self.temp_db_path)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["mood"], "crisis")
        self.assertIn("112", history[0]["bot_response"])

    def test_clear_chat_history(self):
        """Verify clear_chat_history empties the table."""
        save_chat("Msg 1", "Resp 1", "neutral", db_path=self.temp_db_path)
        save_chat("Msg 2", "Resp 2", "anxious", db_path=self.temp_db_path)

        before = retrieve_chat_history(db_path=self.temp_db_path)
        self.assertEqual(len(before), 2)

        deleted = clear_chat_history(db_path=self.temp_db_path)
        self.assertEqual(deleted, 2)

        after = retrieve_chat_history(db_path=self.temp_db_path)
        self.assertEqual(len(after), 0)

    def test_parameterized_query_sql_injection_defense(self):
        """Verify SQL injection payloads are handled safely via parameterization."""
        injection_payload = "test'; DROP TABLE chat_history; --"
        row_id = save_chat(
            user_message=injection_payload,
            bot_response="Safe response",
            mood="neutral",
            db_path=self.temp_db_path
        )
        self.assertIsInstance(row_id, int)

        history = retrieve_chat_history(db_path=self.temp_db_path)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["user_message"], injection_payload)

        # Table must still exist and be intact
        conn = get_db_connection(self.temp_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT count(*) as cnt FROM chat_history")
        count = cursor.fetchone()["cnt"]
        conn.close()
        self.assertEqual(count, 1)

    def test_get_chat_history_alias(self):
        """Verify get_chat_history without session_id retrieves chat_history."""
        save_chat("Hello", "Hi", "neutral", db_path=self.temp_db_path)
        res = get_chat_history(db_path=self.temp_db_path)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["user_message"], "Hello")

    def test_mood_logging_and_retrieval(self):
        """Verify save_mood logs entries and get_mood_logs retrieves them."""
        database.save_mood("sess_123", "Peaceful", "Feeling calm after breathing", db_path=self.temp_db_path)
        database.save_mood("sess_123", "Grateful", note=None, db_path=self.temp_db_path)

        logs = database.get_mood_logs("sess_123", db_path=self.temp_db_path)
        self.assertEqual(len(logs), 2)
        # Should be ordered newest first (id DESC)
        self.assertEqual(logs[0]["mood"], "Grateful")
        self.assertEqual(logs[1]["mood"], "Peaceful")
        self.assertEqual(logs[1]["note"], "Feeling calm after breathing")

    def test_session_message_and_clear_history(self):
        """Verify save_message, get_chat_history(session_id), and clear_history."""
        database.save_message("sess_abc", "user", "Hi bot", db_path=self.temp_db_path)
        database.save_message("sess_abc", "bot", "Hello user!", db_path=self.temp_db_path)

        msgs = database.get_chat_history("sess_abc", db_path=self.temp_db_path)
        self.assertEqual(len(msgs), 2)
        self.assertEqual(msgs[0]["message"], "Hi bot")
        self.assertEqual(msgs[1]["message"], "Hello user!")

        # Clear specific session
        database.clear_history("sess_abc", db_path=self.temp_db_path)
        msgs_after = database.get_chat_history("sess_abc", db_path=self.temp_db_path)
        self.assertEqual(len(msgs_after), 0)

    def test_retrieve_chat_history_with_limit(self):
        """Verify limit parameter caps returned results."""
        for i in range(5):
            save_chat(f"User {i}", f"Bot {i}", "neutral", db_path=self.temp_db_path)

        all_records = retrieve_chat_history(limit=10, db_path=self.temp_db_path)
        self.assertEqual(len(all_records), 5)

        limited_records = retrieve_chat_history(limit=3, db_path=self.temp_db_path)
        self.assertEqual(len(limited_records), 3)


if __name__ == "__main__":
    unittest.main()
