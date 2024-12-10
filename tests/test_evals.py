from typing import Union

import pytest

from fi.evals import EvalClient
from fi.evals.templates import (
    PII,
    AnswerRelevance,
    AnswerSimilarity,
    BiasDetection,
    ChunkAttribution,
    ChunkUtilization,
    Completeness,
    ContentModeration,
    ContextAdherence,
    ContextRelevance,
    ContextRetrieval,
    ContextSimilarity,
    ConversationCoherence,
    ConversationResolution,
    Correctness,
    CulturalSensitivity,
    Deterministic,
    FactualAccuracy,
    ImageInputOutput,
    ImageInstruction,
    LegalCompliance,
    LLMFunctionCalling,
    Output,
    PromptAdherence,
    PromptPerplexity,
    Ranking,
    ReasoningChain,
    SummaryQuality,
    Tone,
    Toxicity,
    TranslationAccuracy,
)
from fi.evals.types import Comparator
from fi.testcases import (
    ConversationalTestCase,
    LLMTestCase,
    MLLMImage,
    MLLMTestCase,
    TestCase,
)


@pytest.fixture
def evaluator():
    return EvalClient()


def test_answer_similarity(evaluator):
    test_case = LLMTestCase(
        query="Who is Prime Minister of India?",
        response="Narendra Modi",
        context=["Narendra Modi is the Prime Minister of India"],
        expected_response="Narendra Modi",
    )
    template = AnswerSimilarity(
        config={"comparator": Comparator.COSINE.value, "failure_threshold": 0.8}
    )
    response = evaluator.evaluate(eval_templates=[template], inputs=[test_case])

    assert response is not None
    assert len(response.eval_results) > 0
    assert response.eval_results[0].metrics[0].value >= 0.8


def test_image_instruction(evaluator):
    test_case = MLLMTestCase(
        image_url="https://fastly.picsum.photos/id/199/200/300.jpg?hmac=GOJRy6ngeR2kvgwCS-aTH8bNUTZuddrykqXUW6AF2XQ",
        input=(
            "This is a serene beach landscape photo taken from a wooden boardwalk or "
            "stairs leading down to the sand. The composition shows the wooden railings in "
            "the foreground framing a view of a pristine sandy beach, turquoise-blue "
            "ocean waters, and a distant island or landmass on the horizon. The sky "
            "features soft, wispy clouds creating a peaceful atmosphere. The colors are "
            "somewhat muted and natural, giving the image a calm, tranquil feeling. The "
            "wooden structure appears to be weathered, suggesting it's a beach access "
            "point or viewing platform."
        ),
    )
    template = ImageInstruction(
        config={
            "criteria": (
                "The image should be a low angle close up shot of Aksel Adomas holding a "
                "box of cereal in a supermarket aisle with a confused expression."
            )
        }
    )
    response = evaluator.evaluate(eval_templates=[template], inputs=[test_case])

    assert response is not None
    assert len(response.eval_results) > 0
    assert response.eval_results[0].metrics[0].value is not None


def test_deterministic_evaluation(evaluator):
    class DeterministicTestCase(TestCase):
        response: str
        expected_response: str

    test_case = DeterministicTestCase(
        response="Hello world", expected_response="Hello world"
    )
    template = Deterministic(
        config={
            "multi_choice": False,
            "choices": ["Yes", "No"],
            "rule_prompt": "Evaluate if {{input_key1}} and {{input_key2}} are deterministic",
            "input": {"input_key1": "response", "input_key2": "expected_response"},
        }
    )
    response = evaluator.evaluate(eval_templates=[template], inputs=[test_case])

    assert response is not None
    assert len(response.eval_results) > 0
    assert response.eval_results[0].data[0] in ["Yes", "No"]


def test_deterministic_image_evaluation(evaluator):
    # Define test case class with image URLs
    class ImageDeterministicTestCase(MLLMTestCase):
        image_url: Union[str, MLLMImage]
        expected_label: str

    # Initialize the deterministic evaluator
    deterministic_eval = Deterministic(
        config={
            "multi_choice": False,
            "choices": ["Yes", "No"],
            "rule_prompt": "Does the image at {{input_key1}} depict a stunning natural landscape featuring a narrow river winding through a deep canyon? Compare with expected answer {{input_key2}}",
            "input": {"input_key1": "image_url", "input_key2": "expected_label"},
        }
    )

    # Create a test case
    test_case = ImageDeterministicTestCase(
        image_url="https://fastly.picsum.photos/id/511/200/300.jpg?hmac=3pjxomHmNfWivxE47hYNY3VdnJTTJtcRJmQ3ihqJcBA",
        expected_label="Yes",
    )

    # Run the evaluation
    response = evaluator.evaluate(
        eval_templates=[deterministic_eval], inputs=[test_case]
    )

    assert response is not None
    assert len(response.eval_results) > 0
    assert response.eval_results[0].data[0] in ["Yes", "No"]


def test_content_moderation(evaluator):
    test_case = TestCase(text="This is a sample text to check for content moderation.")
    template = ContentModeration()
    response = evaluator.evaluate(eval_templates=[template], inputs=[test_case])

    assert response is not None
    assert len(response.eval_results) > 0
    assert response.eval_results[0].metrics[0].value == 1.0


def test_context_adherence(evaluator):
    test_case = TestCase(
        input="What is the capital of France?",
        output="Paris is the capital of France",
        context="Paris is the capital and largest city of France.",
    )
    template = ContextAdherence(config={"check_internet": False})
    response = evaluator.evaluate(eval_templates=[template], inputs=[test_case])

    assert response is not None
    assert len(response.eval_results) > 0
    assert isinstance(response.eval_results[0].metrics[0].value, float)


def test_correctness(evaluator):
    test_case = TestCase(
        context="Paris is the capital of France.",
        input="What is the capital of France?",
        output="Paris is the capital of France.",
    )
    template = Correctness(config={"model": "gpt-4o-mini"})
    response = evaluator.evaluate(eval_templates=[template], inputs=[test_case])

    assert response is not None
    assert len(response.eval_results) > 0
    assert isinstance(response.eval_results[0].metrics[0].value, float)


def test_prompt_perplexity(evaluator):
    test_case = TestCase(
        input="Write a poem",
        output="Roses are red\nViolets are blue",
        prompt="Create a simple rhyming poem",
        context="User wants a basic rhyming poem",
    )
    template = PromptPerplexity(config={"check_internet": False})
    response = evaluator.evaluate(eval_templates=[template], inputs=[test_case])

    assert response is not None
    assert len(response.eval_results) > 0
    assert isinstance(response.eval_results[0].metrics[0].value, float)


def test_context_relevance(evaluator):
    test_case = TestCase(
        query="What is the weather like?",
        context="The current temperature is 72°F with partly cloudy skies.",
    )
    template = ContextRelevance(config={"model": "gpt-4o-mini"})
    response = evaluator.evaluate(eval_templates=[template], inputs=[test_case])

    assert response is not None
    assert len(response.eval_results) > 0
    assert isinstance(response.eval_results[0].metrics[0].value, float)


def test_completeness(evaluator):
    test_case = LLMTestCase(
        query="What are the primary colors?",
        response="The primary colors are red, blue, and yellow.",
    )
    template = Completeness(config={"model": "gpt-4o-mini"})
    response = evaluator.evaluate(eval_templates=[template], inputs=[test_case])

    assert response is not None
    assert len(response.eval_results) > 0
    assert response.eval_results[0].metrics[0].value in ["Pass", "Fail"]


def test_cultural_sensitivity(evaluator):
    test_case = TestCase(
        input="Describe traditional Japanese customs",
        output="In Japanese culture, bowing is a respectful greeting. The depth and duration of the bow can indicate different levels of respect.",
        context="Japanese etiquette includes various forms of bowing as traditional greetings.",
    )
    template = CulturalSensitivity(config={"check_internet": False})
    response = evaluator.evaluate(eval_templates=[template], inputs=[test_case])

    assert response is not None
    assert len(response.eval_results) > 0
    assert isinstance(response.eval_results[0].metrics[0].value, float)


def test_bias_detection(evaluator):
    test_case = TestCase(
        input="What are the differences between men and women in the workplace?",
        output="Men and women have equal capabilities in the workplace and should be evaluated based on their individual skills and qualifications rather than gender.",
        context="Workplace diversity and equality studies show that performance and capability are not gender-dependent.",
    )
    template = BiasDetection(config={"check_internet": False})
    response = evaluator.evaluate(eval_templates=[template], inputs=[test_case])

    assert response is not None
    assert len(response.eval_results) > 0
    assert isinstance(response.eval_results[0].metrics[0].value, float)


def test_conversation_coherence(evaluator):
    test_case = ConversationalTestCase(
        messages=[
            LLMTestCase(
                query="Hi, how are you?",
                response="I'm doing well, thank you! How can I help you today?",
            ),
            LLMTestCase(
                query="I need help with my homework",
                response="I'd be happy to help. What subject are you working on?",
            ),
        ]
    )
    template = ConversationCoherence(config={"model": "gpt-4o-mini"})
    response = evaluator.evaluate(eval_templates=[template], inputs=[test_case])

    assert response is not None
    assert len(response.eval_results) > 0
    assert isinstance(response.eval_results[0].metrics[0].value, float)


def test_legal_compliance(evaluator):
    test_case = TestCase(
        input="What are GDPR requirements?",
        output="GDPR requires explicit consent for data collection, right to access personal data, and right to be forgotten.",
        context="GDPR is EU's data protection regulation that governs personal data handling.",
    )
    template = LegalCompliance(config={"check_internet": False})
    response = evaluator.evaluate(eval_templates=[template], inputs=[test_case])

    assert response is not None
    assert len(response.eval_results) > 0
    assert isinstance(response.eval_results[0].metrics[0].value, float)


def test_translation_accuracy(evaluator):
    test_case = TestCase(
        input="Translate 'Hello, how are you?' to French",
        output="Bonjour, comment allez-vous?",
        context="Standard French greetings and conversational phrases.",
    )
    template = TranslationAccuracy(config={"check_internet": False})
    response = evaluator.evaluate(eval_templates=[template], inputs=[test_case])

    assert response is not None
    assert len(response.eval_results) > 0
    assert isinstance(response.eval_results[0].metrics[0].value, float)


def test_reasoning_chain(evaluator):
    test_case = TestCase(
        input="Why does ice float in water?",
        output="Ice floats in water because it is less dense than liquid water. This happens because water molecules form a crystalline structure when frozen, creating spaces between molecules.",
        context="Water's unique properties include its solid form being less dense than its liquid form.",
    )
    template = ReasoningChain(config={"check_internet": False})
    response = evaluator.evaluate(eval_templates=[template], inputs=[test_case])

    assert response is not None
    assert len(response.eval_results) > 0
    assert isinstance(response.eval_results[0].metrics[0].value, float)


def test_llm_function_calling(evaluator):
    test_case = TestCase(
        input="Get the weather for London",
        output='{"function": "get_weather", "parameters": {"city": "London", "country": "UK"}}',
        context="Available functions: get_weather(city, country)",
    )
    template = LLMFunctionCalling(config={"check_internet": False})
    response = evaluator.evaluate(eval_templates=[template], inputs=[test_case])

    assert response is not None
    assert len(response.eval_results) > 0
    assert isinstance(response.eval_results[0].metrics[0].value, float)


def test_summary_quality(evaluator):
    test_case = TestCase(
        input="Summarize the text about photosynthesis",
        output="Photosynthesis is the process where plants convert sunlight into energy, producing oxygen as a byproduct.",
        context="Photosynthesis is a complex biological process where plants and other organisms convert light energy into chemical energy. This process produces glucose and oxygen while consuming carbon dioxide and water.",
    )
    template = SummaryQuality(config={"check_internet": False})
    response = evaluator.evaluate(eval_templates=[template], inputs=[test_case])

    assert response is not None
    assert len(response.eval_results) > 0
    assert isinstance(response.eval_results[0].metrics[0].value, float)


def test_prompt_adherence(evaluator):
    test_case = TestCase(
        input="Write a haiku about spring",
        output="Cherry blossoms fall\nPink petals dance in the breeze\nSpring awakens now",
        prompt="Write a haiku (5-7-5 syllable pattern) about spring",
        context="A haiku is a Japanese poem with three lines following a 5-7-5 syllable pattern",
    )
    template = PromptAdherence(config={"check_internet": False})
    response = evaluator.evaluate(eval_templates=[template], inputs=[test_case])

    assert response is not None
    assert len(response.eval_results) > 0
    assert isinstance(response.eval_results[0].metrics[0].value, float)


def test_factual_accuracy(evaluator):
    test_case = TestCase(
        input="What is the capital of France?",
        output="Paris is the capital of France",
        context="Paris has been the capital of France since 508 CE",
    )
    template = FactualAccuracy(config={"check_internet": True})
    response = evaluator.evaluate(eval_templates=[template], inputs=[test_case])

    assert response is not None
    assert len(response.eval_results) > 0
    assert isinstance(response.eval_results[0].metrics[0].value, float)


def test_chunk_attribution(evaluator):
    test_case = TestCase(
        input="What is quantum computing?",
        output="Quantum computing uses quantum mechanics principles like superposition and entanglement to perform computations.",
        context=[
            "Quantum computing leverages quantum mechanical phenomena",
            "Superposition and entanglement are key quantum principles",
        ],
    )
    template = ChunkAttribution(config={"check_internet": False})
    response = evaluator.evaluate(eval_templates=[template], inputs=[test_case])

    assert response is not None
    assert len(response.eval_results) > 0
    assert isinstance(response.eval_results[0].metrics[0].value, float)


def test_chunk_utilization(evaluator):
    test_case = TestCase(
        input="Explain climate change",
        output="Climate change refers to long-term shifts in global weather patterns and temperatures.",
        context=[
            "Climate change affects global temperatures",
            "Weather patterns are changing due to global warming",
        ],
    )
    template = ChunkUtilization(config={"check_internet": False})
    response = evaluator.evaluate(eval_templates=[template], inputs=[test_case])

    assert response is not None
    assert len(response.eval_results) > 0
    assert isinstance(response.eval_results[0].metrics[0].value, float)


def test_context_similarity(evaluator):
    test_case = TestCase(
        context="The Earth orbits around the Sun in an elliptical path.",
        response="The Earth's orbit around the Sun is not perfectly circular but elliptical.",
    )
    template = ContextSimilarity(
        config={"comparator": Comparator.COSINE.value, "failure_threshold": 0.7}
    )
    response = evaluator.evaluate(eval_templates=[template], inputs=[test_case])

    assert response is not None
    assert len(response.eval_results) > 0
    assert isinstance(response.eval_results[0].metrics[0].value, float)


def test_pii_detection(evaluator):
    test_case = TestCase(
        text="My email is john.doe@example.com and my phone is 123-456-7890"
    )
    template = PII()
    response = evaluator.evaluate(eval_templates=[template], inputs=[test_case])

    assert response is not None
    assert len(response.eval_results) > 0
    assert response.eval_results[0].metrics[0].value == 0.0


def test_toxicity(evaluator):
    test_case = TestCase(
        input="Write a friendly greeting",
        output="Hello! Hope you're having a wonderful day!",
        context="Maintain positive and respectful communication",
    )
    template = Toxicity(config={"check_internet": False})
    response = evaluator.evaluate(eval_templates=[template], inputs=[test_case])

    assert response is not None
    assert len(response.eval_results) > 0
    assert isinstance(response.eval_results[0].metrics[0].value, float)


def test_tone_evaluation(evaluator):
    test_case = TestCase(
        input="Write a professional email",
        output="Dear Sir/Madam, I hope this email finds you well. I am writing to inquire about...",
        context="Maintain formal business communication tone",
    )
    template = Tone(config={"check_internet": False})
    response = evaluator.evaluate(eval_templates=[template], inputs=[test_case])

    assert response is not None
    assert len(response.eval_results) > 0
    assert isinstance(response.eval_results[0].metrics[0].value, float)


def test_image_input_output(evaluator):
    test_case = MLLMTestCase(
        input="Convert the image with laptop to image with a person working on it",
        input_image_url="https://fastly.picsum.photos/id/0/5000/3333.jpg?hmac=_j6ghY5fCfSD6tvtcV74zXivkJSPIfR9B8w34XeQmvU",
        output_image_url="https://fastly.picsum.photos/id/1/5000/3333.jpg?hmac=Asv2DU3rA_5D1xSe22xZK47WEAN0wjWeFOhzd13ujW4",
    )
    template = ImageInputOutput(
        config={
            "criteria": "Check if the output image is a proper transformation of the input image"
        }
    )
    response = evaluator.evaluate(eval_templates=[template], inputs=[test_case])

    assert response is not None
    assert len(response.eval_results) > 0
    assert isinstance(response.eval_results[0].metrics[0].value, float)


def test_output_evaluation(evaluator):
    test_case = TestCase(
        input="Write a weather forecast",
        output="Tomorrow will be sunny with a high of 75°F and light winds.",
        context="Weather forecasting should be clear and specific",
    )
    template = Output(
        config={
            "criteria": "Check if the forecast includes temperature and wind conditions",
            "check_internet": False,
        }
    )
    response = evaluator.evaluate(eval_templates=[template], inputs=[test_case])

    assert response is not None
    assert len(response.eval_results) > 0
    assert isinstance(response.eval_results[0].metrics[0].value, float)


def test_context_retrieval(evaluator):
    test_case = TestCase(
        input="What are black holes?",
        output="Black holes are regions of spacetime where gravity is so strong that nothing can escape.",
        context="Black holes are cosmic objects with extremely strong gravitational fields",
    )
    template = ContextRetrieval(config={"check_internet": False})
    response = evaluator.evaluate(eval_templates=[template], inputs=[test_case])

    assert response is not None
    assert len(response.eval_results) > 0
    assert isinstance(response.eval_results[0].metrics[0].value, float)


def test_ranking(evaluator):
    test_case = TestCase(
        input="What is the solar system?",
        context=[
            "The solar system consists of the Sun and celestial objects bound to it",
            "Our solar system formed 4.6 billion years ago",
        ],
    )
    template = Ranking(
        config={
            "criteria": "Rank contexts based on relevance to the query about the solar system"
        }
    )
    response = evaluator.evaluate(eval_templates=[template], inputs=[test_case])

    assert response is not None
    assert len(response.eval_results) > 0
    assert isinstance(response.eval_results[0].metrics[0].value, float)


def test_conversation_resolution(evaluator):
    test_case = ConversationalTestCase(
        messages=[
            LLMTestCase(
                query="I need help with my math homework",
                response="I'd be happy to help! What specific math problem are you working on?",
            ),
            LLMTestCase(
                query="I'm trying to solve this equation: 2x + 5 = 13",
                response="Let's solve this step by step:\n1. Subtract 5 from both sides: 2x = 8\n2. Divide both sides by 2: x = 4\nThe solution is x = 4. Would you like me to verify this answer with you?",
            ),
            LLMTestCase(
                query="Yes, please check if it's correct",
                response="Let's verify:\nIf x = 4, then:\n2(4) + 5 = 8 + 5 = 13\nThe equation balances, so x = 4 is correct! Is there anything else you'd like help with?",
            ),
            LLMTestCase(
                query="No, that's all. Thank you!",
                response="You're welcome! Good luck with your math studies. Feel free to ask if you need help with any other problems.",
            ),
        ]
    )
    template = ConversationResolution(config={"model": "gpt-4o-mini"})
    response = evaluator.evaluate(eval_templates=[template], inputs=[test_case])

    assert response is not None
    assert len(response.eval_results) > 0
    assert isinstance(response.eval_results[0].metrics[0].value, float)


def test_answer_relevance(evaluator):
    test_case = LLMTestCase(
        query="What is the capital of Japan?",
        response="Tokyo is the capital and largest city of Japan. It serves as the country's political, economic, and cultural center.",
        context="Tokyo has been Japan's capital since 1868, taking over from Kyoto.",
    )
    template = AnswerRelevance(config={"model": "gpt-4o-mini"})
    response = evaluator.evaluate(eval_templates=[template], inputs=[test_case])

    assert response is not None
    assert len(response.eval_results) > 0
    assert isinstance(response.eval_results[0].metrics[0].value, float)
