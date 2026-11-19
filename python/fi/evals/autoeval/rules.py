"""Rule-based analyzer for AutoEval.

Provides keyword-based analysis when LLM is unavailable.
"""

from typing import List, Dict, Set, Tuple
from .types import (
    AppAnalysis,
    AppCategory,
    RiskLevel,
    DomainSensitivity,
    AppRequirement,
)


# Keyword mappings for category detection
from ._rules_keywords import CATEGORY_KEYWORDS

# Domain sensitivity keywords
from ._rules_keywords import DOMAIN_SENSITIVITY_KEYWORDS

# Feature detection patterns
FEATURE_PATTERNS: Dict[str, List[str]] = {
    "tool_use": [
        "tool",
        "function call",
        "api",
        "execute",
        "action",
        "plugin",
        "integration",
    ],
    "rag": [
        "retrieval",
        "rag",
        "context",
        "knowledge base",
        "document",
        "vector",
        "embedding",
    ],
    "multi_turn": [
        "conversation",
        "chat",
        "dialogue",
        "multi-turn",
        "history",
        "session",
        "follow-up",
    ],
    "code_generation": [
        "code",
        "generate code",
        "programming",
        "script",
        "implement",
    ],
    "image_processing": [
        "image",
        "vision",
        "visual",
        "picture",
        "photo",
        "screenshot",
        "diagram",
    ],
    "safety_critical": [
        "safety",
        "critical",
        "harm",
        "dangerous",
        "risk",
        "sensitive",
    ],
    "real_time": [
        "real-time",
        "realtime",
        "low latency",
        "streaming",
        "live",
    ],
    "batch_processing": [
        "batch",
        "bulk",
        "large scale",
        "mass processing",
    ],
}

# Requirement generators based on category
from ._rules_requirements import CATEGORY_REQUIREMENTS

# Default requirements for all apps
from ._rules_requirements import DEFAULT_REQUIREMENTS


class RuleBasedAnalyzer:
    """Rule-based fallback analyzer for when LLM is unavailable.

    Uses keyword matching to detect:
    - Application category
    - Domain sensitivity
    - Risk level
    - Required features

    Example:
        analyzer = RuleBasedAnalyzer()
        analysis = analyzer.analyze(
            "A customer support chatbot for healthcare that answers patient questions."
        )
        print(analysis.category)  # AppCategory.CUSTOMER_SUPPORT
        print(analysis.risk_level)  # RiskLevel.HIGH (due to healthcare)
    """

    def analyze(self, description: str) -> AppAnalysis:
        """
        Analyze description using keyword matching and rules.

        Args:
            description: Application description

        Returns:
            AppAnalysis with detected attributes
        """
        description_lower = description.lower()

        # Detect category
        category = self._detect_category(description_lower)

        # Detect domain sensitivity
        sensitivity = self._detect_sensitivity(description_lower)

        # Determine risk level based on sensitivity
        risk_level = self._determine_risk_level(sensitivity, description_lower)

        # Detect features
        features = self._detect_features(description_lower)

        # Generate requirements based on analysis
        requirements = self._generate_requirements(
            category, sensitivity, risk_level, features
        )

        return AppAnalysis(
            category=category,
            risk_level=risk_level,
            domain_sensitivity=sensitivity,
            requirements=requirements,
            detected_features=features,
            confidence=0.6,  # Rule-based has lower confidence
            explanation=self._generate_explanation(category, sensitivity, features),
        )

    def _detect_category(self, text: str) -> AppCategory:
        """Detect app category from keywords."""
        scores: Dict[AppCategory, int] = {}

        for category, keywords in CATEGORY_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text)
            if score > 0:
                scores[category] = score

        if scores:
            return max(scores, key=scores.get)
        return AppCategory.UNKNOWN

    def _detect_sensitivity(self, text: str) -> DomainSensitivity:
        """Detect domain sensitivity from keywords."""
        scores: Dict[DomainSensitivity, int] = {}

        for sensitivity, keywords in DOMAIN_SENSITIVITY_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text)
            if score > 0:
                scores[sensitivity] = score

        if scores:
            return max(scores, key=scores.get)
        return DomainSensitivity.GENERAL

    def _determine_risk_level(
        self,
        sensitivity: DomainSensitivity,
        text: str,
    ) -> RiskLevel:
        """Determine risk level based on sensitivity and keywords."""
        # High-risk domains
        high_risk_domains = {
            DomainSensitivity.HEALTHCARE,
            DomainSensitivity.FINANCIAL,
            DomainSensitivity.LEGAL,
            DomainSensitivity.CHILDREN,
            DomainSensitivity.GOVERNMENT,
        }

        if sensitivity in high_risk_domains:
            # Check for critical keywords
            critical_keywords = ["critical", "life-saving", "emergency", "classified"]
            if any(kw in text for kw in critical_keywords):
                return RiskLevel.CRITICAL
            return RiskLevel.HIGH

        # Medium risk for PII-sensitive
        if sensitivity == DomainSensitivity.PII_SENSITIVE:
            return RiskLevel.MEDIUM

        # Context-based risk detection
        if any(kw in text for kw in ["production", "public", "customer", "external"]):
            return RiskLevel.MEDIUM

        if any(kw in text for kw in ["internal", "development", "testing", "prototype"]):
            return RiskLevel.LOW

        return RiskLevel.MEDIUM

    def _detect_features(self, text: str) -> List[str]:
        """Detect application features from keywords."""
        features = []

        for feature, patterns in FEATURE_PATTERNS.items():
            if any(p in text for p in patterns):
                features.append(feature)

        return features

    def _generate_requirements(
        self,
        category: AppCategory,
        sensitivity: DomainSensitivity,
        risk_level: RiskLevel,
        features: List[str],
    ) -> List[AppRequirement]:
        """Generate requirements based on analysis."""
        requirements: List[AppRequirement] = []

        # Add category-specific requirements
        if category in CATEGORY_REQUIREMENTS:
            requirements.extend(CATEGORY_REQUIREMENTS[category])

        # Add default requirements if not already covered
        eval_names = {
            e for r in requirements for e in r.suggested_evals
        }
        for default_req in DEFAULT_REQUIREMENTS:
            if not any(e in eval_names for e in default_req.suggested_evals):
                requirements.append(default_req)

        # Add sensitivity-based requirements
        if sensitivity in {
            DomainSensitivity.PII_SENSITIVE,
            DomainSensitivity.HEALTHCARE,
            DomainSensitivity.FINANCIAL,
        }:
            requirements.append(
                AppRequirement(
                    category="pii_protection",
                    importance="required",
                    reason=f"{sensitivity.value} applications must protect sensitive data",
                    suggested_scanners=["pii", "secrets"],
                )
            )

        # Add risk-level based requirements
        if risk_level in {RiskLevel.HIGH, RiskLevel.CRITICAL}:
            requirements.append(
                AppRequirement(
                    category="safety",
                    importance="required",
                    reason="High-risk applications require comprehensive safety evaluation",
                    suggested_scanners=["jailbreak", "toxicity"],
                )
            )

        return requirements

    def _generate_explanation(
        self,
        category: AppCategory,
        sensitivity: DomainSensitivity,
        features: List[str],
    ) -> str:
        """Generate explanation for the analysis."""
        parts = []

        if category != AppCategory.UNKNOWN:
            parts.append(f"Detected application type: {category.value}")
        else:
            parts.append("Could not determine specific application type")

        if sensitivity != DomainSensitivity.GENERAL:
            parts.append(f"Domain sensitivity: {sensitivity.value}")

        if features:
            parts.append(f"Detected features: {', '.join(features)}")

        parts.append("Analysis performed using rule-based keyword matching.")

        return " ".join(parts)
