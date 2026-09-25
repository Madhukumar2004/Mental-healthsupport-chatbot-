import unittest
import os
import tempfile
import app
import database
from chatbot import (
    INTENT_GREETING,
    INTENT_STRESS,
    INTENT_ANXIETY,
    INTENT_SADNESS,
    INTENT_SLEEP_PROBLEMS,
    INTENT_EXAM_STUDY_STRESS,
    INTENT_ANGER,
    INTENT_CRISIS,
    MOOD_HAPPY,
    MOOD_SAD,
    MOOD_ANXIOUS,
    MOOD_STRESSED,
    MOOD_ANGRY,
    MOOD_CRISIS,
    MOOD_NEUTRAL,
)


class TestCompleteMindCareApp(unittest.TestCase):

    def setUp(self):
        app.app.config["TESTING"] = True
        self.client = app.app.test_client()
        self.temp_db_fd, self.temp_db_path = tempfile.mkstemp(suffix=".db")
        self.orig_db_path = database.DB_PATH
        database.DB_PATH = self.temp_db_path
        database.init_db(self.temp_db_path)

    def tearDown(self):
        database.DB_PATH = self.orig_db_path
        os.close(self.temp_db_fd)
        if os.path.exists(self.temp_db_path):
            os.remove(self.temp_db_path)

    # 1. Opening the homepage
    def test_1_open_homepage(self):
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        html = res.get_data(as_text=True)
        self.assertIn("MindCare", html)
        self.assertIn("chatViewport", html)
        self.assertIn("chatInput", html)
        self.assertIn("btnSend", html)
        self.assertIn("btnClearChat", html)

    # 2. Sending a normal message
    def test_2_send_normal_message(self):
        res = self.client.post("/chat", json={"message": "What is mindfulness?"})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("response", data)
        self.assertTrue(len(data["response"]) > 0)
        self.assertIn("mood", data)

    # 3. Greeting detection
    def test_3_greeting_detection(self):
        res = self.client.post("/chat", json={"message": "Hello there! Good morning"})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["intent"], INTENT_GREETING)

    # 4. Stress detection
    def test_4_stress_detection(self):
        res = self.client.post("/chat", json={"message": "I am so overwhelmed by work pressure and deadlines"})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["intent"], INTENT_STRESS)
        self.assertEqual(data["mood"], MOOD_STRESSED)

    # 5. Anxiety detection
    def test_5_anxiety_detection(self):
        res = self.client.post("/chat", json={"message": "I am having a panic attack, my heart is racing and I feel anxious"})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["intent"], INTENT_ANXIETY)
        self.assertEqual(data["mood"], MOOD_ANXIOUS)

    # 6. Sadness detection
    def test_6_sadness_detection(self):
        res = self.client.post("/chat", json={"message": "I feel so sad and lonely today, I have been crying"})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["intent"], INTENT_SADNESS)
        self.assertEqual(data["mood"], MOOD_SAD)

    # 7. Sleep detection
    def test_7_sleep_detection(self):
        res = self.client.post("/chat", json={"message": "I can't sleep at all tonight, my insomnia is back"})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["intent"], INTENT_SLEEP_PROBLEMS)

    # 8. Exam stress detection
    def test_8_exam_stress_detection(self):
        res = self.client.post("/chat", json={"message": "I am stressed about my exam syllabus and finals test"})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["intent"], INTENT_EXAM_STUDY_STRESS)
        self.assertEqual(data["mood"], MOOD_STRESSED)

    # 9. Anger detection
    def test_9_anger_detection(self):
        res = self.client.post("/chat", json={"message": "I am so furious and angry right now, I hate this situation"})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["intent"], INTENT_ANGER)
        self.assertEqual(data["mood"], MOOD_ANGRY)

    # 10. Crisis detection
    def test_10_crisis_detection(self):
        crisis_phrases = [
            "I am having thoughts of suicide",
            "I want to die right now",
            "I feel like killing myself",
            "I struggle with self-harm urges",
            "I want to hurt myself",
            "I want to end my life",
        ]
        for phrase in crisis_phrases:
            with self.subTest(phrase=phrase):
                res = self.client.post("/chat", json={"message": phrase})
                self.assertEqual(res.status_code, 200)
                data = res.get_json()
                self.assertEqual(data["intent"], INTENT_CRISIS)
                self.assertEqual(data["mood"], MOOD_CRISIS)
                self.assertTrue(data["is_crisis"])
                self.assertIn("112", data["response"])
                self.assertIn("cannot provide medical treatment", data["response"].lower())

    # 11. Mood display & detection
    def test_11_mood_display_values(self):
        mood_tests = [
            ("I am feeling great, peaceful, and happy today!", MOOD_HAPPY),
            ("I feel so depressed, sad, and down", MOOD_SAD),
            ("I am panicking and terrified", MOOD_ANXIOUS),
            ("Burnout and endless pressure is exhausting me", MOOD_STRESSED),
            ("I am so mad and furious", MOOD_ANGRY),
            ("I want to end my life", MOOD_CRISIS),
        ]
        for message, expected_mood in mood_tests:
            with self.subTest(msg=message):
                res = self.client.post("/chat", json={"message": message})
                self.assertEqual(res.status_code, 200)
                data = res.get_json()
                self.assertEqual(data["mood"], expected_mood)

    # 12. Saving chat history
    def test_12_saving_chat_history(self):
        res = self.client.post("/chat", json={"message": "Testing save chat message"})
        self.assertEqual(res.status_code, 200)
        history = database.retrieve_chat_history(db_path=self.temp_db_path)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["user_message"], "Testing save chat message")
        self.assertTrue(len(history[0]["bot_response"]) > 0)
        self.assertIsNotNone(history[0]["created_at"])

    # 13. Loading chat history
    def test_13_loading_chat_history(self):
        self.client.post("/chat", json={"message": "First message to load"})
        self.client.post("/chat", json={"message": "Second message to load"})
        res = self.client.get("/history")
        self.assertEqual(res.status_code, 200)
        history = res.get_json()
        records = history if isinstance(history, list) else history.get("history", [])
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]["user_message"], "First message to load")
        self.assertEqual(records[1]["user_message"], "Second message to load")

    # 14. Clear Chat
    def test_14_clear_chat(self):
        self.client.post("/chat", json={"message": "Message to be cleared"})
        self.assertEqual(len(database.retrieve_chat_history(db_path=self.temp_db_path)), 1)

        res = self.client.delete("/clear")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data.get("status"), "success")
        self.assertEqual(len(database.retrieve_chat_history(db_path=self.temp_db_path)), 0)

    # 15. Empty message handling
    def test_15_empty_message_handling(self):
        invalid_cases = [
            {"message": ""},
            {"message": "   "},
            {"message": "\n\t  "},
            {"message": None},
            {},
        ]
        for payload in invalid_cases:
            with self.subTest(payload=payload):
                res = self.client.post("/chat", json=payload)
                self.assertEqual(res.status_code, 400)
                data = res.get_json()
                self.assertIn("error", data)


if __name__ == "__main__":
    unittest.main()
