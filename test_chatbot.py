import unittest
from chatbot import (
    detect_crisis,
    detect_crisis_message,
    crisis_message_detection,
    check_crisis_message,
    detect_intent,
    detect_mood,
    get_chatbot_response,
    INTENT_GREETING,
    INTENT_STRESS,
    INTENT_ANXIETY,
    INTENT_SADNESS,
    INTENT_SLEEP_PROBLEMS,
    INTENT_EXAM_STUDY_STRESS,
    INTENT_ANGER,
    INTENT_THANKS,
    INTENT_GOODBYE,
    INTENT_UNKNOWN,
    INTENT_CRISIS,
    MOOD_HAPPY,
    MOOD_SAD,
    MOOD_ANXIOUS,
    MOOD_STRESSED,
    MOOD_ANGRY,
    MOOD_NEUTRAL,
    MOOD_CRISIS,
    ALL_INTENTS,
    ALL_MOODS,
)


class TestChatbotLogic(unittest.TestCase):

    def test_all_10_intents_exist(self):
        self.assertEqual(len(ALL_INTENTS), 10)
        expected = [
            "greeting", "stress", "anxiety", "sadness", "sleep_problems",
            "exam_study_stress", "anger", "thanks", "goodbye", "unknown"
        ]
        self.assertEqual(ALL_INTENTS, expected)

    def test_all_moods_exist(self):
        self.assertIn(MOOD_CRISIS, ALL_MOODS)
        for mood in ["happy", "sad", "anxious", "stressed", "angry", "neutral", "crisis"]:
            self.assertIn(mood, ALL_MOODS)

    # -------------------------------------------------------------
    # Crisis Detection Function Tests
    # -------------------------------------------------------------
    def test_detect_crisis_suicide(self):
        phrases = [
            "I am having thoughts of suicide",
            "I feel suicidal today",
            "I want to commit suicide",
            "thinking of suicide constantly",
        ]
        for p in phrases:
            with self.subTest(phrase=p):
                self.assertTrue(detect_crisis(p))

    def test_detect_crisis_wanting_to_die(self):
        phrases = [
            "I want to die",
            "I wanna die right now",
            "I wish I was dead",
            "I'm better off dead",
            "I don't want to live anymore",
            "There is no reason to live",
            "I am going to die",
            "I'm going to die",
            "going to die",
            "gonna die",
            "I feel like dying",
        ]
        for p in phrases:
            with self.subTest(phrase=p):
                self.assertTrue(detect_crisis(p))

    def test_detect_crisis_killing_oneself(self):
        phrases = [
            "I'm going to kill myself",
            "kill myself",
            "killing myself tonight",
            "gonna kill myself",
            "hang myself",
            "overdose on pills",
        ]
        for p in phrases:
            with self.subTest(phrase=p):
                self.assertTrue(detect_crisis(p))

    def test_detect_crisis_self_harm(self):
        phrases = [
            "I have self-harm urges",
            "I am self-harming",
            "struggling with selfharm",
            "self injury",
        ]
        for p in phrases:
            with self.subTest(phrase=p):
                self.assertTrue(detect_crisis(p))

    def test_detect_crisis_hurting_oneself(self):
        phrases = [
            "I feel like hurting myself",
            "I want to hurt myself",
            "harming myself",
            "I have been cutting myself",
            "inflict pain on myself",
        ]
        for p in phrases:
            with self.subTest(phrase=p):
                self.assertTrue(detect_crisis(p))

    def test_detect_crisis_ending_ones_life(self):
        phrases = [
            "I want to end my life",
            "thinking of ending my life",
            "I will take my own life",
            "I just want to end it all",
        ]
        for p in phrases:
            with self.subTest(phrase=p):
                self.assertTrue(detect_crisis(p))

    def test_detect_crisis_negative_cases(self):
        non_crisis_phrases = [
            "I have so much work stress",
            "I am anxious about my exam",
            "I feel sad today",
            "Can't sleep due to insomnia",
            "I'm so angry at my brother",
            "Hello, how are you?",
            "Thank you for your help",
        ]
        for p in non_crisis_phrases:
            with self.subTest(phrase=p):
                self.assertFalse(detect_crisis(p))

    def test_crisis_response_content_and_mood(self):
        crisis_query = "I want to kill myself, I want to die"
        res = get_chatbot_response(crisis_query)

        # 1. Flagged as crisis
        self.assertTrue(res["is_crisis"])
        self.assertEqual(res["intent"], INTENT_CRISIS)

        # 2. Mood returned as crisis
        self.assertEqual(res["mood"], MOOD_CRISIS)
        self.assertEqual(detect_mood(crisis_query), MOOD_CRISIS)

        # 3. Emergency number 112 mentioned for India
        self.assertIn("112", res["response"])
        self.assertIn("India", res["response"])

        # 4. Advises contacting emergency services, trusted person, qualified professional
        response_text = res["response"].lower()
        self.assertIn("emergency services", response_text)
        self.assertIn("trusted person", response_text)
        self.assertIn("qualified professional", response_text)

        # 5. Does NOT provide medical treatment or clinical instructions
        self.assertIn("cannot provide medical treatment", response_text)

    def test_detect_crisis_message_function(self):
        """Verify the separate detect_crisis_message function directly."""
        crisis_samples = [
            "I am thinking of suicide",
            "I want to die right now",
            "I am killing myself",
            "I have self-harm urges",
            "I feel like hurting myself",
            "I want to end my life",
        ]
        for phrase in crisis_samples:
            with self.subTest(phrase=phrase):
                result = detect_crisis_message(phrase)
                self.assertIsNotNone(result)

                # Return mood as 'crisis'
                self.assertEqual(result["mood"], "crisis")
                self.assertEqual(result.mood, "crisis")
                self.assertTrue(result["is_crisis"])

                # Supportive emergency response
                response = result["response"]
                self.assertIsInstance(response, str)
                resp_lower = response.lower()

                # Does NOT provide medical treatment or instructions
                self.assertIn("cannot provide medical treatment", resp_lower)

                # Advises contacting emergency services, trusted person, qualified professional
                self.assertIn("emergency services", resp_lower)
                self.assertIn("trusted person", resp_lower)
                self.assertIn("qualified professional", resp_lower)

                # For users in India, mentions emergency number 112
                self.assertIn("112", response)
                self.assertIn("India", response)

                # Test tuple unpacking support (resp, mood)
                unpacked_resp, unpacked_mood = result
                self.assertEqual(unpacked_resp, response)
                self.assertEqual(unpacked_mood, "crisis")

    def test_detect_crisis_message_non_crisis_returns_none(self):
        """Verify detect_crisis_message returns None for non-crisis inputs."""
        non_crisis_inputs = [
            "I have so much work stress",
            "I am anxious about my exam",
            "Hello, how are you?",
            "Thank you for helping me",
            "",
            "   ",
        ]
        for query in non_crisis_inputs:
            with self.subTest(query=query):
                self.assertIsNone(detect_crisis_message(query))
                self.assertIsNone(crisis_message_detection(query))
                self.assertIsNone(check_crisis_message(query))

    # -------------------------------------------------------------
    # Intent Detection Tests (10 intents)
    # -------------------------------------------------------------
    def test_intent_greeting(self):
        for p in ["Hi", "Hello", "Hey there", "Good morning!", "Good evening", "Howdy friend"]:
            self.assertEqual(detect_intent(p), INTENT_GREETING)

    def test_intent_stress(self):
        for p in ["I am feeling so stressed out", "Work burnout is overwhelming me", "Too much work and pressure"]:
            self.assertEqual(detect_intent(p), INTENT_STRESS)

    def test_intent_anxiety(self):
        for p in ["I am having a panic attack", "My heart is racing and I feel anxious", "I am terrified"]:
            self.assertEqual(detect_intent(p), INTENT_ANXIETY)

    def test_intent_sadness(self):
        for p in ["I feel so sad today", "I've been crying and feel hopeless", "I'm depressed and lonely"]:
            self.assertEqual(detect_intent(p), INTENT_SADNESS)

    def test_intent_sleep_problems(self):
        for p in ["I can't sleep at all", "Having terrible insomnia", "Tossing and turning all night long"]:
            self.assertEqual(detect_intent(p), INTENT_SLEEP_PROBLEMS)

    def test_intent_exam_study_stress(self):
        for p in ["I am stressed about my exam tomorrow", "Studying for finals is giving me anxiety", "Midterms stress"]:
            self.assertEqual(detect_intent(p), INTENT_EXAM_STUDY_STRESS)

    def test_intent_anger(self):
        for p in ["I am so angry right now", "I'm furious with my boss", "I feel frustrated and pissed off"]:
            self.assertEqual(detect_intent(p), INTENT_ANGER)

    def test_intent_thanks(self):
        for p in ["Thank you so much!", "Thanks for your help", "I really appreciate it"]:
            self.assertEqual(detect_intent(p), INTENT_THANKS)

    def test_intent_goodbye(self):
        for p in ["Goodbye!", "Bye bye", "See you later", "Good night, going to sleep", "Farewell"]:
            self.assertEqual(detect_intent(p), INTENT_GOODBYE)

    def test_intent_unknown(self):
        for p in ["", "   ", "What is the capital of France?", "42"]:
            self.assertEqual(detect_intent(p), INTENT_UNKNOWN)

    # -------------------------------------------------------------
    # Mood Detection Tests (6 standard + crisis)
    # -------------------------------------------------------------
    def test_detect_mood_happy(self):
        self.assertEqual(detect_mood("I am feeling great and happy!"), MOOD_HAPPY)
        self.assertEqual(detect_mood("Feeling peaceful and relaxed 😊"), MOOD_HAPPY)

    def test_detect_mood_sad(self):
        self.assertEqual(detect_mood("I am so sad and depressed"), MOOD_SAD)
        self.assertEqual(detect_mood("I am not happy today"), MOOD_SAD)

    def test_detect_mood_anxious(self):
        self.assertEqual(detect_mood("I'm panicking and my heart is racing"), MOOD_ANXIOUS)
        self.assertEqual(detect_mood("Terrified and so anxious 😰"), MOOD_ANXIOUS)

    def test_detect_mood_stressed(self):
        self.assertEqual(detect_mood("Too many deadlines, I am overwhelmed and stressed"), MOOD_STRESSED)

    def test_detect_mood_angry(self):
        self.assertEqual(detect_mood("I am so mad and furious 😡"), MOOD_ANGRY)
        self.assertEqual(detect_mood("I'm pissed off and frustrated"), MOOD_ANGRY)

    def test_detect_mood_neutral(self):
        self.assertEqual(detect_mood("Hello"), MOOD_NEUTRAL)
        self.assertEqual(detect_mood("What time is it?"), MOOD_NEUTRAL)

    def test_detect_mood_crisis(self):
        self.assertEqual(detect_mood("I want to end my life"), MOOD_CRISIS)
        self.assertEqual(detect_mood("I am having thoughts of suicide"), MOOD_CRISIS)
        self.assertEqual(detect_mood("I feel like hurting myself"), MOOD_CRISIS)


if __name__ == "__main__":
    unittest.main()
