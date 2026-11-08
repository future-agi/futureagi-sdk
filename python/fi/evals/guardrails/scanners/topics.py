"""
Topic Restriction Scanner for Guardrails.

Restricts conversations to allowed topics and detects off-topic content.
Supports both keyword-based and semantic embedding-based detection.
"""

import re
import time
from typing import Any, Dict, List, Optional, Set, Tuple

from fi.evals.guardrails.scanners.base import (
    BaseScanner,
    ScanResult,
    ScanMatch,
    ScannerAction,
    register_scanner,
)


# Topic descriptions for semantic embedding matching
TOPIC_DESCRIPTIONS: Dict[str, str] = {
    "politics": "Political discussions about elections, voting, government, political parties, politicians, legislation, and policy debates",
    "religion": "Religious discussions about faith, worship, God, spiritual beliefs, churches, mosques, temples, and religious texts",
    "violence": "Violent content including weapons, attacks, murder, assault, warfare, fighting, and physical harm",
    "drugs": "Drug-related content about narcotics, illegal substances, drug use, addiction, and trafficking",
    "adult_content": "Adult or sexual content including pornography, explicit material, and NSFW topics",
    "gambling": "Gambling discussions about casinos, betting, poker, lottery, and wagering",
    "medical_advice": "Medical advice about diagnoses, treatments, medications, symptoms, and health conditions",
    "financial_advice": "Financial advice about investments, stocks, trading, cryptocurrency, and portfolio management",
    "legal_advice": "Legal advice about lawsuits, attorneys, court cases, litigation, and legal proceedings",
    "customer_support": "Customer support topics like orders, shipping, refunds, account issues, and billing questions",
    "product_info": "Product information about features, specifications, pricing, availability, and warranties",
    "technical_support": "Technical support for software errors, bugs, installation, configuration, and troubleshooting",
    "general_knowledge": "General knowledge questions about facts, history, science, geography, and explanations",
}

# Predefined topic keywords for common restrictions
TOPIC_KEYWORDS: Dict[str, Set[str]] = {
    # Sensitive topics often restricted
    "politics": {
        "election", "vote", "democrat", "republican", "liberal", "conservative",
        "president", "congress", "senate", "parliament", "politician", "government",
        "left-wing", "right-wing", "campaign", "ballot", "trump", "biden", "party",
    },
    "religion": {
        "god", "jesus", "allah", "buddha", "church", "mosque", "temple", "prayer",
        "bible", "quran", "torah", "christian", "muslim", "jewish", "hindu",
        "atheist", "agnostic", "faith", "worship", "salvation", "sin", "heaven", "hell",
    },
    "violence": {
        "kill", "murder", "attack", "assault", "weapon", "gun", "bomb", "terrorist",
        "violence", "violent", "hurt", "harm", "blood", "death", "dead", "shoot",
        "stab", "fight", "war", "battle", "combat",
    },
    "drugs": {
        "cocaine", "heroin", "marijuana", "cannabis", "weed", "meth", "lsd", "mdma",
        "drug", "narcotic", "overdose", "addiction", "dealer", "cartel", "trafficking",
    },
    "adult_content": {
        "sex", "porn", "nude", "naked", "erotic", "explicit", "xxx", "nsfw",
        "fetish", "intimate", "sexual", "genitals",
    },
    "gambling": {
        "casino", "bet", "betting", "gamble", "gambling", "poker", "blackjack",
        "slot", "lottery", "wager", "odds", "bookie", "sportsbook",
    },
    "medical_advice": {
        "diagnosis", "treatment", "medication", "prescription", "dosage", "symptom",
        "disease", "illness", "cure", "therapy", "doctor", "patient",
    },
    "financial_advice": {
        "invest", "investment", "stock", "bond", "portfolio", "trading", "forex",
        "crypto", "bitcoin", "dividend", "retirement", "pension",
    },
    "legal_advice": {
        "lawsuit", "attorney", "lawyer", "court", "judge", "verdict", "settlement",
        "litigation", "defendant", "plaintiff", "legal", "illegal",
    },

    # Common allowed topics
    "customer_support": {
        "order", "shipping", "delivery", "refund", "return", "exchange", "tracking",
        "account", "password", "login", "subscription", "billing", "payment",
        "help", "support", "issue", "problem", "question",
    },
    "product_info": {
        "product", "feature", "specification", "price", "availability", "warranty",
        "size", "color", "model", "version", "compatible",
    },
    "technical_support": {
        "error", "bug", "crash", "install", "update", "download", "configure",
        "setup", "troubleshoot", "debug", "fix", "issue", "problem",
    },
    "general_knowledge": {
        "what", "how", "why", "when", "where", "who", "explain", "describe",
        "define", "meaning", "history", "science", "math", "geography",
    },
}


from fi.evals._extracted import bind_owner as _bind_owner
from ._topics_topic_restriction_scanner_load_embedding_model import _TopicRestrictionScannerLoadEmbeddingModelMethods
from ._topics_topic_restriction_scanner_scan import _TopicRestrictionScannerScanMethods

@register_scanner("topics")
class TopicRestrictionScanner(
    _TopicRestrictionScannerLoadEmbeddingModelMethods,
    _TopicRestrictionScannerScanMethods,
    BaseScanner,
):
    """
    Scanner for topic restriction and off-topic detection.

    Supports two detection modes:
    - Keyword-based: Fast pattern matching (default)
    - Semantic: Embedding-based similarity matching

    Restricts conversations to allowed topics or blocks denied topics.

    Usage:
        # Keyword-based (fast, no dependencies)
        scanner = TopicRestrictionScanner(
            allowed_topics=["customer_support", "product_info"],
        )

        # Semantic embedding-based (requires sentence-transformers)
        scanner = TopicRestrictionScanner(
            denied_topics=["politics", "religion"],
            use_embeddings=True,
        )

        # Hybrid mode - combines both approaches
        scanner = TopicRestrictionScanner(
            allowed_topics=["customer_support"],
            use_embeddings=True,
            combine_scores=True,
        )

        # Custom topic descriptions for semantic matching
        scanner = TopicRestrictionScanner(
            custom_topic_descriptions={
                "insurance_claims": "Insurance claim processing, policy coverage, claim status",
            },
            allowed_topics=["insurance_claims"],
            use_embeddings=True,
        )

        result = scanner.scan("Who should I vote for in the election?")
        if not result.passed:
            print(f"Off-topic: {result.metadata.get('detected_topics')}")
    """

    name = "topics"
    category = "topic_restriction"
    description = "Restricts conversations to allowed topics"
    default_action = ScannerAction.FLAG

    # Default embedding model
    DEFAULT_EMBEDDING_MODEL = "all-MiniLM-L6-v2"

    def __init__(
        self,
        action: Optional[ScannerAction] = None,
        enabled: bool = True,
        threshold: float = 0.5,
        allowed_topics: Optional[List[str]] = None,
        denied_topics: Optional[List[str]] = None,
        custom_topics: Optional[Dict[str, Set[str]]] = None,
        custom_topic_descriptions: Optional[Dict[str, str]] = None,
        min_keyword_matches: int = 2,
        case_sensitive: bool = False,
        use_embeddings: bool = False,
        embedding_model: Optional[str] = None,
        combine_scores: bool = True,
        embedding_weight: float = 0.6,
        keyword_weight: float = 0.4,
        semantic_threshold: float = 0.5,
        device: Optional[str] = None,
    ):
        """
        Initialize topic restriction scanner.

        Args:
            action: Action on detection
            enabled: Whether scanner is enabled
            threshold: Confidence threshold (based on keyword match ratio)
            allowed_topics: List of allowed topic names (whitelist mode)
            denied_topics: List of denied topic names (blacklist mode)
            custom_topics: Custom topic definitions {topic_name: {keywords}}
            custom_topic_descriptions: Custom descriptions for semantic matching
            min_keyword_matches: Minimum keyword matches to detect a topic
            case_sensitive: Whether matching is case-sensitive
            use_embeddings: Enable semantic embedding-based detection
            embedding_model: Model name for embeddings (default: all-MiniLM-L6-v2)
            combine_scores: Combine keyword and embedding scores (hybrid mode)
            embedding_weight: Weight for embedding score in combined mode
            keyword_weight: Weight for keyword score in combined mode
            semantic_threshold: Similarity threshold for semantic matching
            device: Device for embedding model ('cpu', 'cuda', 'mps', or None)
        """
        super().__init__(action, enabled)
        self.threshold = threshold
        self.allowed_topics = set(allowed_topics) if allowed_topics else None
        self.denied_topics = set(denied_topics) if denied_topics else None
        self.min_keyword_matches = min_keyword_matches
        self.case_sensitive = case_sensitive

        # Embedding settings
        self.use_embeddings = use_embeddings
        self.embedding_model_name = embedding_model or self.DEFAULT_EMBEDDING_MODEL
        self.combine_scores = combine_scores
        self.embedding_weight = embedding_weight
        self.keyword_weight = keyword_weight
        self.semantic_threshold = semantic_threshold
        self.device = device

        # Build topic dictionaries
        self.topics = TOPIC_KEYWORDS.copy()
        if custom_topics:
            self.topics.update(custom_topics)

        self.topic_descriptions = TOPIC_DESCRIPTIONS.copy()
        if custom_topic_descriptions:
            self.topic_descriptions.update(custom_topic_descriptions)

        # Compile patterns for keyword matching
        self._topic_patterns: Dict[str, List[re.Pattern]] = {}
        for topic, keywords in self.topics.items():
            flags = 0 if case_sensitive else re.IGNORECASE
            patterns = [
                re.compile(r'\b' + re.escape(kw) + r'\b', flags)
                for kw in keywords
            ]
            self._topic_patterns[topic] = patterns

        # Lazy-loaded embedding components
        self._embedding_model: Optional[Any] = None
        self._topic_embeddings: Optional[Dict[str, Any]] = None
        self._embeddings_available = False
        self._embeddings_load_error: Optional[str] = None

        # Pre-load embeddings if requested
        if use_embeddings:
            self._load_embedding_model()


_bind_owner(TopicRestrictionScanner)
