import re
import random

# ==============================================================================
# Intent Constants
# ==============================================================================
INTENT_GREETING = "greeting"
INTENT_STRESS = "stress"
INTENT_ANXIETY = "anxiety"
INTENT_SADNESS = "sadness"
INTENT_SLEEP_PROBLEMS = "sleep_problems"
INTENT_EXAM_STUDY_STRESS = "exam_study_stress"
INTENT_ANGER = "anger"
INTENT_THANKS = "thanks"
INTENT_GOODBYE = "goodbye"
INTENT_UNKNOWN = "unknown"
INTENT_CRISIS = "crisis"

# Convenient alias
INTENT_EXAM_STRESS = INTENT_EXAM_STUDY_STRESS

ALL_INTENTS = [
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
]

# ==============================================================================
# Mood Constants
# ==============================================================================
MOOD_HAPPY = "happy"
MOOD_SAD = "sad"
MOOD_ANXIOUS = "anxious"
MOOD_STRESSED = "stressed"
MOOD_ANGRY = "angry"
MOOD_NEUTRAL = "neutral"
MOOD_CRISIS = "crisis"

ALL_MOODS = [
    MOOD_HAPPY,
    MOOD_SAD,
    MOOD_ANXIOUS,
    MOOD_STRESSED,
    MOOD_ANGRY,
    MOOD_NEUTRAL,
    MOOD_CRISIS,
]

# ==============================================================================
# Crisis-Message Detection Patterns
# Covers:
# 1. Suicide
# 2. Wanting to die
# 3. Killing oneself
# 4. Self-harm
# 5. Hurting oneself
# 6. Ending one's life
# ==============================================================================
CRISIS_PATTERNS = {
    # 1. Suicide
    "suicide": [
        r"\b(suicide|suicidal|commit\s+suicide|committing\s+suicide|committed\s+suicide|attempt(ing|ed)?\s+suicide|(thought|thoughts|thinking)\s+of\s+suicide)\b",
    ],
    # 2. Wanting to die
    "wanting_to_die": [
        r"\b(want\s+to\s+die|wanna\s+die|wanting\s+to\s+die|wish\s+to\s+die)\b",
        r"\b(going\s+to\s+die|gonna\s+die|about\s+to\s+die|ready\s+to\s+die|will\s+die|should\s+just\s+die)\b",
        r"\b(feel(ing)?\s+like\s+dying|thinking\s+of\s+dying)\b",
        r"\b(wish\s+i\s+(were|was)\s+dead|wishing\s+i\s+(were|was)\s+dead|better\s+off\s+dead|rather\s+be\s+dead)\b",
        r"\b(do\s*not\s+want\s+to\s+live|don'?t\s+want\s+to\s+live|don'?t\s+wanna\s+live|don'?t\s+want\s+to\s+wake\s+up|no\s+reason\s+to\s+live|nothing\s+to\s+live\s+for|done\s+with\s+life|tired\s+of\s+living|can'?t\s+go\s+on\s+living)\b",
    ],
    # 3. Killing oneself
    "killing_oneself": [
        r"\b(kill\s+(my|one|your|him|her)?self|kill\s+themselves|killing\s+(my|one|your|him|her)?self|killing\s+themselves|gonna\s+kill\s+myself|going\s+to\s+kill\s+myself)\b",
        r"\b(hang\s+(my|one|your|him|her)?self|hanging\s+(my|one|your|him|her)?self|overdose|overdosing|shoot\s+(my|one|your|him|her)?self)\b",
    ],
    # 4. Self-harm
    "self_harm": [
        r"\b(self[\s\-]harm(ing)?|selfharm|self[\s\-]injury|self[\s\-]injurious|self[\s\-]mutilat(e|ion|ing)?)\b",
    ],
    # 5. Hurting oneself
    "hurting_oneself": [
        r"\b(hurt\s+(my|one|your|him|her)?self|hurting\s+(my|one|your|him|her)?self)\b",
        r"\b(harm\s+(my|one|your|him|her)?self|harming\s+(my|one|your|him|her)?self)\b",
        r"\b(cut\s+(my|one|your|him|her)?self|cutting\s+(my|one|your|him|her)?self)\b",
        r"\b(inflict(ing)?\s+pain\s+on\s+(my|one|your|him|her)?self)\b",
        r"\b(burn\s+(my|one|your|him|her)?self|burning\s+(my|one|your|him|her)?self)\b",
    ],
    # 6. Ending one's life
    "ending_ones_life": [
        r"\b(end\s+(my|one'?s|your|his|her|their)\s+life|ending\s+(my|one'?s|your|his|her|their)\s+life)\b",
        r"\b(take\s+(my|one'?s|your|his|her|their)\s+(own\s+)?life|taking\s+(my|one'?s|your|his|her|their)\s+(own\s+)?life)\b",
        r"\b(end\s+it\s+all|ending\s+it\s+all)\b",
    ],
}

# Flatted list of all regex patterns for rapid evaluation
CRISIS_PATTERNS_FLAT = [pattern for sublist in CRISIS_PATTERNS.values() for pattern in sublist]

CRISIS_RESPONSE_TEXT = (
    "I hear how much pain you are going through right now, and I care deeply about your safety and well-being. "
    "Please know that you do not have to carry this alone.\n\n"
    "As an AI peer companion, I cannot provide medical treatment, clinical diagnosis, or medical instructions. "
    "Your life is precious, and compassionate human help is available right now. Please reach out immediately to:\n\n"
    "• **Emergency Services:** If you or someone you know is in immediate danger, contact emergency services right away. "
    "For users in India, please call **112** for immediate emergency assistance.\n"
    "• **A Trusted Person:** Reach out to a family member, close friend, mentor, or someone in your life who cares about you.\n"
    "• **A Qualified Professional or 24/7 Helpline:** Speak with a licensed doctor, qualified mental health professional, or trained crisis counselor:\n"
    "  - **In India:** Call **112** (National Emergency) or **14416** / **1800-891-4416** (Tele-MANAS Mental Health Helpline, 24/7 Free)\n"
    "  - **In the US & Canada:** Call or text **988** (Suicide & Crisis Lifeline, 24/7 Free & Confidential)\n"
    "  - **In the UK:** Call **111** (NHS) or text **SHOUT** to **85258**\n"
    "  - **International:** Find confidential, free support in your country at [findahelpline.com](https://findahelpline.com)\n\n"
    "Please take this moment to connect with emergency services, a trusted person, or a qualified professional who can support you safely."
)

CRISIS_RESPONSE = {
    "response": CRISIS_RESPONSE_TEXT,
    "intent": INTENT_CRISIS,
    "mood": MOOD_CRISIS,
    "is_crisis": True,
    "suggested_actions": ["Emergency Helplines (112)", "Talk to Someone You Trust", "Grounding Technique"],
}

# ==============================================================================
# Rule-Based Intent Patterns
# ==============================================================================
INTENT_PATTERNS = {
    INTENT_GOODBYE: [
        r"\b(bye|goodbye|bye\s+bye|byebye)\b",
        r"\b(see\s+you|see\s+ya|talk\s+later|talk\s+to\s+you\s+later|cya)\b",
        r"\b(good\s+night|goodnight|nighty\s+night)\b",
        r"\b(have\s+a\s+good\s+(day|night|evening|weekend)|have\s+a\s+nice\s+day)\b",
        r"\b(leaving\s+now|gotta\s+go|got\s+to\s+go|farewell|take\s+care)\b",
    ],
    INTENT_THANKS: [
        r"\b(thank\s+you|thanks|thank\s+u|thx|thnx)\b",
        r"\b(appreciate\s+(it|you)|much\s+appreciated|appreciated)\b",
        r"\b(grateful|gratitude|thankful)\b",
        r"\b(that\s+helped|you\s+helped\s+a\s+lot|thanks\s+a\s+lot|feeling\s+better\s+now)\b",
    ],
    INTENT_EXAM_STUDY_STRESS: [
        r"\b(exam|exams|test|tests|midterm|midterms|finals|quiz|quizzes)\b",
        r"\b(studying|study|revision|revising|syllabus|coursework)\b",
        r"\b(homework|assignment|assignments|project\s+submission|dissertation|thesis)\b",
        r"\b(failing|fail\s+my|pass\s+my|grade|grades|gpa|academic\s+pressure)\b",
        r"\b(school\s+stress|college\s+stress|university\s+stress)\b",
    ],
    INTENT_SLEEP_PROBLEMS: [
        r"\b(can'?t\s+sleep|cannot\s+sleep|trouble\s+sleeping|unable\s+to\s+sleep|hard\s+to\s+sleep|struggling\s+to\s+sleep)\b",
        r"\b(insomnia|sleepless|sleeplessness|insomniac)\b",
        r"\b(wake\s+up\s+at\s+night|waking\s+up\s+at\s+night|woke\s+up\s+and\s+can'?t\s+sleep)\b",
        r"\b(nightmare|nightmares|bad\s+dreams?|night\s+terror)\b",
        r"\b(toss(ing)?\s+and\s+turn(ing)?)\b",
        r"\b(lying\s+awake|staying\s+awake|racing\s+thoughts\s+at\s+night)\b",
        r"\b(sleep\s+issue|sleep\s+problem|sleep\s+depriv(ed|ation)|poor\s+sleep)\b",
    ],
    INTENT_ANGER: [
        r"\b(angry|anger|mad|furious|infuriated|pissed|pissed\s+off)\b",
        r"\b(frustrated|frustration|irritated|irritation|annoyed|annoyance)\b",
        r"\b(rage|outrage|enraged|livid|fuming|resentful|bitter)\b",
        r"\b(lost\s+my\s+temper|lose\s+my\s+temper|screaming|yelling)\b",
        r"\b(hate\s+everything|hate\s+everyone|so\s+mad|makes\s+me\s+mad|pisses\s+me\s+off)\b",
    ],
    INTENT_ANXIETY: [
        r"\b(anxious|anxiety|panic|panic\s+attack|panicking)\b",
        r"\b(nervous|nervousness|scared|terrified|freaking\s+out|frightened)\b",
        r"\b(heart\s+racing|heart\s+pounding|can'?t\s+breathe|hyperventilat(ing|e))\b",
        r"\b(dread|feeling\s+dread|on\s+edge|uneasy|restless|restlessness)\b",
        r"\b(trembling|shaking\s+with\s+fear|worried\s+sick|worrying|worries)\b",
        r"\b(phobia|agoraphobia|social\s+anxiety)\b",
    ],
    INTENT_SADNESS: [
        r"\b(sad|sadness|depressed|depression|depressing)\b",
        r"\b(crying|cried|tears|weeping|sob(bing)?)\b",
        r"\b(lonely|loneliness|alone|isolated|isolation|nobody\s+cares)\b",
        r"\b(hopeless|hopelessness|empty|emptiness|numb|numbness)\b",
        r"\b(heartbroken|heartbreak|grief|grieving|mourning|loss)\b",
        r"\b(miserable|down\s+in\s+the\s+dumps|feeling\s+low|feeling\s+down)\b",
        r"\b(unhappy|sorrow|hurting\s+inside|worthless|gloomy)\b",
    ],
    INTENT_STRESS: [
        r"\b(stress|stressed|stressful|stressing)\b",
        r"\b(burnout|burned\s+out|burnt\s+out)\b",
        r"\b(overwhelmed|overwhelming|overloaded|overload)\b",
        r"\b(exhausted|exhaustion|drained|fatigued|depleted)\b",
        r"\b(too\s+much\s+work|workload|pressure|deadline(s)?|overworked)\b",
        r"\b(swamped|breaking\s+point|tension|tense|hectic)\b",
    ],
    INTENT_GREETING: [
        r"\b(hi|hello|hey|heyy+|howdy|greetings|hola)\b",
        r"\b(good\s+(morning|afternoon|evening))\b",
        r"\b(what'?s\s+up|sup)\b",
        r"\b(hey\s+there|hi\s+there|hello\s+there)\b",
    ],
}

# ==============================================================================
# Rule-Based Mood Patterns & Scoring
# ==============================================================================
MOOD_PATTERNS = {
    MOOD_HAPPY: [
        r"\b(happy|happiness|joy|joyful|glad|great|awesome|wonderful|fantastic|cheerful|content|delighted|excited|ecstatic|blessed|peaceful|smiling|laughing|relaxed|feeling\s+good|feeling\s+great|feeling\s+better|positive|loved|optimistic)\b",
        r"[😊😄😃😁🥰❤️✨🎉🥳]",
    ],
    MOOD_SAD: [
        r"\b(sad|sadness|unhappy|depressed|depression|crying|cried|tears|sob(bing)?|down|lonely|alone|isolated|hopeless|heartbroken|grief|mourning|loss|miserable|gloomy|sorrow|hurting|empty|worthless|unloved|blue)\b",
        r"[😢😭😔😞💔]",
    ],
    MOOD_ANXIOUS: [
        r"\b(anxious|anxiety|panic|panicking|nervous|nervousness|scared|terrified|frightened|fear|dread|on\s+edge|freaking\s+out|heart\s+racing|hyperventilat(ing|e)|trembling|shaking|worried|worrying|uneasy|restless)\b",
        r"[😰😨😱😖]",
    ],
    MOOD_STRESSED: [
        r"\b(stressed|stress|stressful|overwhelmed|burnout|burned\s+out|exhausted|drained|overloaded|swamped|too\s+much\s+work|pressure|deadline(s)?|overworked|hectic|tension|strained|fatigued|depleted)\b",
        r"[😫😩🤯]",
    ],
    MOOD_ANGRY: [
        r"\b(angry|anger|mad|furious|infuriated|pissed|pissed\s+off|annoyed|annoying|irritated|irritation|frustrated|frustration|rage|enraged|livid|fuming|hate|resentful|bitter|temper)\b",
        r"[😡😠🤬💢]",
    ],
}

# Negations that invert positive sentiment into sadness/neutral
NEGATION_PATTERN = r"\b(not|never|hardly|barely|n't)\s+(happy|glad|good|great|fine|okay|peaceful|content|relaxed)\b"

# ==============================================================================
# Supportive Responses & Suggested Actions for Each Intent
# ==============================================================================
INTENT_RESPONSES = {
    INTENT_GREETING: {
        "responses": [
            (
                "Hello, and welcome to MindCare! 🌸 I am here to provide a safe, calm, and non-judgmental "
                "space for you to share whatever is on your mind. How are you feeling in your heart and body today?"
            ),
            (
                "Hi there! Welcome. Whether you're navigating stress, looking for a grounding moment, "
                "or just wanting a compassionate ear, I am here for you. How has your day been treating you?"
            ),
            (
                "Hello! I'm glad you took a moment to connect. Remember that there is no pressure here—you can take "
                "things at your own pace. What is on your mind today?"
            ),
        ],
        "suggested_actions": ["I'm feeling stressed", "I'm feeling anxious", "Need to vent", "Start Breathing Exercise"],
    },
    INTENT_STRESS: {
        "responses": [
            (
                "Burnout and stress are your mind and body's way of signaling that you've been carrying too much for too long. "
                "Give yourself permission to pause for just a moment. Drop your shoulders away from your ears, unclench your jaw, "
                "and take one slow breath. What is the single thing creating the most pressure for you right now?"
            ),
            (
                "I hear how much pressure you're under. When everything feels urgent, our nervous system gets stuck in overdrive. "
                "Remember: your worth is not defined by endless productivity. Can you identify one task today that you can postpone, "
                "delegate, or step away from for a little while?"
            ),
            (
                "It sounds like you have an immense load on your shoulders right now. Take a gentle breath with me. "
                "The world can wait while you reclaim your peace. Would you like to do a quick 3-minute reset together, "
                "or talk through what's making you feel overwhelmed?"
            ),
        ],
        "suggested_actions": ["3-Minute Reset", "Boundary Tips", "Start Breathing Exercise", "Talk about what's pressing"],
    },
    INTENT_ANXIETY: {
        "responses": [
            (
                "I sense that you're feeling anxious right now. Let's take a slow, gentle moment together. "
                "Anxiety can feel intensely physical and scary, but remember: you are safe in this present moment, "
                "and this surge will pass. Would you like to do a quick 4-7-8 breathing exercise with me or try the 5-4-3-2-1 grounding technique?"
            ),
            (
                "It is completely okay to feel overwhelmed. When anxiety peaks, our body's alarm system is just trying to protect us. "
                "Place your feet flat on the floor, feel the ground supporting you, and take one slow breath in through your nose, "
                "and a long exhale out through your mouth. Tell me, what is worrying you most right now?"
            ),
            (
                "Anxiety is like an ocean wave—it rises, peaks, and then naturally recedes. You don't have to fight it; "
                "we can ride it out together safely. Focus on the physical feeling of your hands resting in your lap. "
                "I am right here with you."
            ),
        ],
        "suggested_actions": ["Start Breathing Exercise", "5-4-3-2-1 Grounding", "Talk about what's worrying me", "Daily Affirmation"],
    },
    INTENT_SADNESS: {
        "responses": [
            (
                "I'm so sorry things feel heavy right now. It takes courage to acknowledge sadness, and your feelings are completely valid. "
                "You don't have to force yourself to feel positive or 'fix' everything today. "
                "I'm right here listening if you want to share what's on your heart."
            ),
            (
                "Feeling down or emotionally drained can feel deeply isolating, but please be gentle with yourself. "
                "Even taking one small step—like wrapping up in a warm blanket, taking a sip of water, or simply resting—is an accomplishment. "
                "Would you like to talk through what feels heaviest right now?"
            ),
            (
                "Your sadness is valid, and you don't have to carry this burden all alone. Remember that feelings, like weather patterns, "
                "do change over time. Be kind to yourself today. What is one gentle comfort you can give yourself right now?"
            ),
        ],
        "suggested_actions": ["Talk about my feelings", "Gentle self-care tips", "Give me an affirmation", "Start Breathing Exercise"],
    },
    INTENT_SLEEP_PROBLEMS: {
        "responses": [
            (
                "Struggling to sleep can be deeply frustrating, especially when your body is tired but your mind keeps racing. "
                "Try unclenching your jaw, letting your tongue rest at the bottom of your mouth, and relaxing your forehead. "
                "A gentle technique is the 'Cognitive Shuffle': think of a random letter (like 'B') and picture words starting with it "
                "(Ball, Bridge, Breeze...) until your mind drifts. Would you like a sleep relaxation guide?"
            ),
            (
                "Nighttime often magnifies our worries because the world goes quiet. "
                "If you've been tossing and turning for more than 20 minutes, consider sitting in dim light and taking slow, soft breaths "
                "until drowsiness returns naturally. What thoughts seem to be keeping you awake tonight?"
            ),
            (
                "When sleep won't come, trying to force it often creates more tension. Instead of focusing on sleeping, "
                "just focus on resting your body and feeling the softness of your pillow. Let's do a gentle 4-7-8 breathing exercise "
                "to help calm your nervous system."
            ),
        ],
        "suggested_actions": ["Sleep Relaxation Guide", "Start Breathing Exercise", "Calm my racing thoughts", "Bedtime Wind-Down"],
    },
    INTENT_EXAM_STUDY_STRESS: {
        "responses": [
            (
                "Exam and study pressure can feel completely overwhelming, but please remember: your worth as a human being "
                "is never defined by a test score, GPA, or grade. Let's take a deep breath together. "
                "You don't have to conquer the entire syllabus in one go. What specific exam or subject is stressing you out most right now?"
            ),
            (
                "It is very common to feel anxious when exams and deadlines pile up. Try using the Pomodoro technique: "
                "commit to just 25 minutes of focused studying, followed by a mandatory 5-minute break away from your desk. "
                "Remember to stay hydrated and stretch your shoulders. How can I help you break your work into smaller, manageable steps?"
            ),
            (
                "When exam stress kicks in, our minds often run to worst-case scenarios. Let's counter that anxiety: "
                "you are capable, you have learned so much already, and you can take this one question and one hour at a time. "
                "Take a slow breath. What is one small study goal we can focus on for today?"
            ),
        ],
        "suggested_actions": ["Study Break Reset", "Break into small steps", "Start Breathing Exercise", "Exam Affirmation"],
    },
    INTENT_ANGER: {
        "responses": [
            (
                "It is completely valid to feel angry. Anger is a natural and important human emotion—it often tells us "
                "that a boundary was crossed, an injustice happened, or we feel unheard. Let's give you a safe, non-judgmental space to vent. "
                "Take a deep breath, unclench your fists, and tell me: what triggered this anger?"
            ),
            (
                "I hear how frustrated and mad you are right now. When anger surges, our heart rate spikes and adrenaline kicks in. "
                "Before responding or reacting to anyone, try taking three long, cooling exhales—like blowing out a stubborn candle. "
                "You have every right to feel upset, and I'm right here listening to whatever you need to get off your chest."
            ),
            (
                "Intense anger can feel like a storm inside. Acknowledge that the feeling is there without judging yourself for having it. "
                "Sometimes writing out raw thoughts or stepping away to splash cool water on your face helps reset the nervous system. "
                "Would you like to vent about what happened, or focus on cooling down first?"
            ),
        ],
        "suggested_actions": ["Vent what happened", "Cooling Breath Technique", "5-4-3-2-1 Grounding", "Release tension tips"],
    },
    INTENT_THANKS: {
        "responses": [
            (
                "You are so very welcome! 🌸 It warms my heart to know you're feeling even a little lighter. "
                "Remember to acknowledge yourself for taking time to care for your mental wellness today. "
                "I am always right here whenever you need a moment of calm."
            ),
            (
                "I'm really glad to hear that! Celebrating small victories and peaceful moments is an important part "
                "of mental wellness. You're doing great, and keep taking gentle care of yourself!"
            ),
            (
                "You're most welcome! Seeking support and reflecting on your well-being is a sign of strength. "
                "MindCare is always here as your safe space whenever you'd like to return."
            ),
        ],
        "suggested_actions": ["Daily Affirmation", "Save a happy mood", "Start Breathing Exercise"],
    },
    INTENT_GOODBYE: {
        "responses": [
            (
                "Take gentle care of yourself! May the rest of your day or night bring you peace, restorative rest, and calm. "
                "MindCare is always here whenever you want to return. 🕊️"
            ),
            (
                "Goodbye for now! Remember to drink some water, take gentle deep breaths, and be kind to yourself. "
                "Wishing you calm and clarity."
            ),
            (
                "Farewell for now! Thank you for spending time and sharing with me today. "
                "Remember you are stronger than you think, and I'm always here whenever you need support."
            ),
        ],
        "suggested_actions": ["Emergency Helplines", "Quick Affirmation"],
    },
    INTENT_UNKNOWN: {
        "responses": [
            (
                "Thank you for sharing that with me. Even if I don't have the perfect answer, I'm here to listen without judgment. "
                "Could you tell me a little more about how that is making you feel inside?"
            ),
            (
                "I hear you. Sometimes it's difficult to find the exact words for what we're going through, and that's okay. "
                "Would it help to focus on calming exercises, or would you like to explore what you're thinking right now?"
            ),
            (
                "I appreciate you opening up. When you think about this situation, where do you feel the tension in your body? "
                "We can take a pause to breathe, or unpack it together step-by-step."
            ),
        ],
        "suggested_actions": ["Try Breathing Exercise", "5-4-3-2-1 Grounding", "I'm feeling anxious", "Daily Affirmation"],
    },
}

# ==============================================================================
# Crisis, Intent & Mood Detection Functions
# ==============================================================================
class CrisisResult(dict):
    """
    Dedicated crisis response container returned when a crisis message is detected.
    Behaves as a dictionary:
        result["response"] -> supportive emergency response string
        result["mood"]     -> "crisis"
        result["is_crisis"]-> True
        result["intent"]   -> "crisis"
    Supports property access:
        result.response, result.mood
    Supports index access and 2-tuple unpacking:
        resp, mood = result
        result[0] -> response
        result[1] -> mood
    """

    def __init__(
        self,
        response: str = CRISIS_RESPONSE_TEXT,
        mood: str = MOOD_CRISIS,
        is_crisis: bool = True,
        intent: str = INTENT_CRISIS,
        suggested_actions: list = None,
    ):
        super().__init__(
            response=response,
            mood=mood,
            is_crisis=is_crisis,
            intent=intent,
            suggested_actions=suggested_actions or list(CRISIS_RESPONSE["suggested_actions"]),
        )

    def __iter__(self):
        yield self["response"]
        yield self["mood"]

    def __getitem__(self, key):
        if key == 0:
            return self["response"]
        elif key == 1:
            return self["mood"]
        return super().__getitem__(key)

    @property
    def response(self) -> str:
        return self["response"]

    @property
    def mood(self) -> str:
        return self["mood"]


def detect_crisis_message(text: str):
    """
    Separate crisis-message detection function.
    Detects acute crisis phrases related to:
    - suicide
    - wanting to die
    - killing oneself
    - self-harm
    - hurting oneself
    - ending one's life

    When detected, does not provide medical treatment or instructions.
    Instead, returns a supportive emergency response telling the user to
    contact emergency services, a trusted person, or a qualified professional.
    For users in India, mentions emergency number 112.
    Also returns the mood as 'crisis'.

    Returns a CrisisResult (dict-like with ['response'] and ['mood']='crisis',
    also unpackable as (response, mood)) if detected, or None if not detected.
    """
    if not text:
        return None
    text_lower = text.lower()
    for pattern in CRISIS_PATTERNS_FLAT:
        if re.search(pattern, text_lower, re.IGNORECASE):
            return CrisisResult()
    return None


def detect_crisis(text: str) -> bool:
    """
    Checks if a message contains acute crisis phrases.
    Returns True if any crisis pattern is detected, otherwise False.
    """
    return detect_crisis_message(text) is not None


# Backward-compatibility & alternative name aliases
crisis_message_detection = detect_crisis_message
check_crisis_message = detect_crisis_message
check_crisis = detect_crisis


def detect_intent(text: str) -> str:
    """
    Rule-based intent detection that classifies user message into one of 10 intents:
    1. greeting
    2. stress
    3. anxiety
    4. sadness
    5. sleep_problems
    6. exam_study_stress
    7. anger
    8. thanks
    9. goodbye
    10. unknown
    """
    if not text or not text.strip():
        return INTENT_UNKNOWN

    text_lower = text.strip().lower()

    # Priority 1: Goodbye departures
    for pattern in INTENT_PATTERNS[INTENT_GOODBYE]:
        if re.search(pattern, text_lower):
            return INTENT_GOODBYE

    # Priority 2: Expressions of gratitude
    for pattern in INTENT_PATTERNS[INTENT_THANKS]:
        if re.search(pattern, text_lower):
            return INTENT_THANKS

    # Priority 3: Specific situational triggers (Exam & Sleep before general stress/anxiety)
    for pattern in INTENT_PATTERNS[INTENT_EXAM_STUDY_STRESS]:
        if re.search(pattern, text_lower):
            return INTENT_EXAM_STUDY_STRESS

    for pattern in INTENT_PATTERNS[INTENT_SLEEP_PROBLEMS]:
        if re.search(pattern, text_lower):
            return INTENT_SLEEP_PROBLEMS

    # Priority 4: Emotional states (Anger, Anxiety, Sadness, Stress)
    for pattern in INTENT_PATTERNS[INTENT_ANGER]:
        if re.search(pattern, text_lower):
            return INTENT_ANGER

    for pattern in INTENT_PATTERNS[INTENT_ANXIETY]:
        if re.search(pattern, text_lower):
            return INTENT_ANXIETY

    for pattern in INTENT_PATTERNS[INTENT_SADNESS]:
        if re.search(pattern, text_lower):
            return INTENT_SADNESS

    for pattern in INTENT_PATTERNS[INTENT_STRESS]:
        if re.search(pattern, text_lower):
            return INTENT_STRESS

    # Priority 5: Pure Greeting (checked after emotional intents so 'Hi, I'm stressed' detects stress)
    for pattern in INTENT_PATTERNS[INTENT_GREETING]:
        if re.search(pattern, text_lower):
            return INTENT_GREETING

    # Fallback: Unknown
    return INTENT_UNKNOWN


def detect_mood(text: str) -> str:
    """
    Rule-based mood detection returning one of:
    - 'crisis' (when crisis phrases are detected)
    - 'happy'
    - 'sad'
    - 'anxious'
    - 'stressed'
    - 'angry'
    - 'neutral'
    """
    if not text or not text.strip():
        return MOOD_NEUTRAL

    # Crisis detection takes top priority
    if detect_crisis(text):
        return MOOD_CRISIS

    text_lower = text.strip().lower()

    # Check for negated positive sentiments (e.g. "not happy", "not feeling good")
    has_negated_positive = bool(re.search(NEGATION_PATTERN, text_lower))

    scores = {
        MOOD_HAPPY: 0,
        MOOD_SAD: 0,
        MOOD_ANXIOUS: 0,
        MOOD_STRESSED: 0,
        MOOD_ANGRY: 0,
    }
    first_match_index = {}

    for mood, patterns in MOOD_PATTERNS.items():
        # If positive sentiment is negated, do not score towards happy
        if mood == MOOD_HAPPY and has_negated_positive:
            scores[MOOD_SAD] += 1
            continue

        for pattern in patterns:
            for match in re.finditer(pattern, text_lower):
                scores[mood] += 1
                if mood not in first_match_index or match.start() < first_match_index[mood]:
                    first_match_index[mood] = match.start()

    # Determine highest score
    max_score = max(scores.values())
    if max_score == 0:
        return MOOD_NEUTRAL

    # In case of tie, select mood whose keyword appeared earliest in the input
    top_moods = [m for m, s in scores.items() if s == max_score]
    if len(top_moods) == 1:
        return top_moods[0]

    return min(top_moods, key=lambda m: first_match_index.get(m, 999999))


# ==============================================================================
# Main Chatbot Response Engine
# ==============================================================================
def get_chatbot_response(user_message: str) -> dict:
    """
    Analyzes user message and generates an empathetic, supportive response
    with rule-based intent detection, mood detection, and relevant suggested actions.
    """
    clean_text = (user_message or "").strip()
    if not clean_text:
        return {
            "response": "I'm right here listening whenever you're ready to share.",
            "intent": INTENT_UNKNOWN,
            "mood": MOOD_NEUTRAL,
            "is_crisis": False,
            "suggested_actions": ["I'm feeling stressed", "Try breathing exercise", "Give me an affirmation"],
        }

    # Step 1: Immediate Crisis Check (Highest Priority Safety Check)
    crisis_result = detect_crisis_message(clean_text)
    if crisis_result:
        return crisis_result

    # Step 2: Rule-Based Intent Detection
    intent = detect_intent(clean_text)

    # Step 3: Rule-Based Mood Detection
    mood = detect_mood(clean_text)

    # Step 4: Fetch Intent Response and Suggested Actions
    intent_data = INTENT_RESPONSES.get(intent, INTENT_RESPONSES[INTENT_UNKNOWN])
    chosen_response = random.choice(intent_data["responses"])
    suggested_actions = intent_data.get("suggested_actions", [])

    return {
        "response": chosen_response,
        "intent": intent,
        "mood": mood,
        "is_crisis": False,
        "suggested_actions": suggested_actions,
    }


# ==============================================================================
# Quick Verification / CLI Test
# ==============================================================================
if __name__ == "__main__":
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    test_queries = [
        ("Hello there!", INTENT_GREETING, MOOD_NEUTRAL),
        ("I'm so burned out and stressed with endless deadlines", INTENT_STRESS, MOOD_STRESSED),
        ("I am having a huge panic attack my heart is racing", INTENT_ANXIETY, MOOD_ANXIOUS),
        ("I feel so sad and lonely, I've been crying", INTENT_SADNESS, MOOD_SAD),
        ("I can't sleep tonight, insomnia is terrible", INTENT_SLEEP_PROBLEMS, MOOD_NEUTRAL),
        ("I'm stressed about my final exam tomorrow and might fail", INTENT_EXAM_STUDY_STRESS, MOOD_STRESSED),
        ("I am so mad and furious right now, I hate this", INTENT_ANGER, MOOD_ANGRY),
        ("Thank you so much for your help!", INTENT_THANKS, MOOD_NEUTRAL),
        ("Goodbye, talk to you later!", INTENT_GOODBYE, MOOD_NEUTRAL),
        ("What is the distance to Jupiter?", INTENT_UNKNOWN, MOOD_NEUTRAL),
        ("I'm really happy and excited today!", INTENT_UNKNOWN, MOOD_HAPPY),
        ("I want to end my life, please help", INTENT_CRISIS, MOOD_CRISIS),
    ]

    print("Running Chatbot Intent & Mood Detection Verification...\n" + "=" * 60)
    for query, expected_intent, expected_mood in test_queries:
        res = get_chatbot_response(query)
        intent_match = "PASS" if res["intent"] == expected_intent else f"FAIL (got {res['intent']})"
        mood_match = "PASS" if res["mood"] == expected_mood else f"FAIL (got {res['mood']})"
        print(f"Query: {query}")
        print(f"Intent: {res['intent']} [{intent_match}] | Mood: {res['mood']} [{mood_match}] | Crisis: {res['is_crisis']}")
        print(f"Bot: {res['response'][:90]}...")
        print("-" * 60)
