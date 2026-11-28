"""TopicRestrictionScanner scan operations."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict
from fi.evals.guardrails.scanners.topics import (List, Optional, ScanResult)

if TYPE_CHECKING:
    from fi.evals.guardrails.scanners.topics import TopicRestrictionScanner


class _TopicRestrictionScannerScanMethods:
    __slots__ = ()

    def scan(self, content: str, context: Optional[str] = None) -> ScanResult:
        """
        Scan content for topic violations.

        Uses keyword matching, semantic similarity, or both depending on config.

        Args:
            content: Content to scan
            context: Optional context

        Returns:
            ScanResult with topic detection details
        """
        from fi.evals.guardrails.scanners.topics import (Optional, ScanMatch, ScanResult, time)
        start = time.perf_counter()
        matches = []
        issues = []
        metadata: Dict[str, Any] = {}

        # Record detection mode
        if self.use_embeddings and self._embeddings_available:
            metadata["detection_mode"] = "hybrid" if self.combine_scores else "semantic"
            metadata["embedding_model"] = self.embedding_model_name
        else:
            metadata["detection_mode"] = "keyword"
            if self.use_embeddings and not self._embeddings_available:
                metadata["embedding_error"] = self._embeddings_load_error

        # Detect topics
        detected_topics = self._detect_topics(content)

        # Also check context if provided
        if context:
            context_topics = self._detect_topics(context)
            for topic, info in context_topics.items():
                if topic in detected_topics:
                    # Merge: take max confidence
                    if info["confidence"] > detected_topics[topic]["confidence"]:
                        detected_topics[topic] = info
                else:
                    detected_topics[topic] = info

        # Check topic restrictions
        violation = False

        # Whitelist mode: only allowed topics are permitted
        if self.allowed_topics:
            for topic, info in detected_topics.items():
                if info["confidence"] >= self.threshold:
                    if topic not in self.allowed_topics:
                        matches.append(ScanMatch(
                            pattern_name="off_topic",
                            matched_text=f"Topic: {topic}",
                            start=0,
                            end=len(content),
                            confidence=info["confidence"],
                            metadata={
                                "topic": topic,
                                "keywords": info.get("keywords", []),
                                "method": info.get("method", "unknown"),
                            },
                        ))
                        issues.append(f"Off-topic: {topic}")
                        violation = True

            # Also flag if no allowed topic was detected
            allowed_detected = any(
                topic in self.allowed_topics and info["confidence"] >= self.threshold
                for topic, info in detected_topics.items()
            )
            if not allowed_detected and not violation and detected_topics:
                # Content doesn't match any allowed topic
                matches.append(ScanMatch(
                    pattern_name="no_allowed_topic",
                    matched_text="No allowed topic detected",
                    start=0,
                    end=len(content),
                    confidence=0.6,
                ))
                issues.append("No allowed topic detected")
                violation = True

        # Blacklist mode: denied topics are blocked
        if self.denied_topics:
            for topic, info in detected_topics.items():
                if topic in self.denied_topics and info["confidence"] >= self.threshold:
                    matches.append(ScanMatch(
                        pattern_name="denied_topic",
                        matched_text=f"Topic: {topic}",
                        start=0,
                        end=len(content),
                        confidence=info["confidence"],
                        metadata={
                            "topic": topic,
                            "keywords": info.get("keywords", []),
                            "method": info.get("method", "unknown"),
                        },
                    ))
                    issues.append(f"Denied topic: {topic}")
                    violation = True

        latency = (time.perf_counter() - start) * 1000

        # Determine result
        max_confidence = max([m.confidence for m in matches], default=0.0)

        metadata["detected_topics"] = {
            k: v for k, v in detected_topics.items()
            if v["confidence"] >= self.threshold
        }

        if violation:
            return self._create_result(
                passed=False,
                matches=matches,
                score=max_confidence,
                reason="; ".join(issues),
                latency_ms=latency,
                metadata=metadata,
            )

        return self._create_result(
            passed=True,
            matches=[],
            score=0.0,
            reason="Content is on-topic",
            latency_ms=latency,
            metadata=metadata,
        )


    @classmethod
    def with_embeddings(
        cls,
        allowed_topics: Optional[List[str]] = None,
        denied_topics: Optional[List[str]] = None,
        embedding_model: Optional[str] = None,
        threshold: float = 0.5,
        **kwargs,
    ) -> "TopicRestrictionScanner":
        """
        Factory method to create an embedding-enabled topic scanner.

        Args:
            allowed_topics: Allowed topic list
            denied_topics: Denied topic list
            embedding_model: Model to use (defaults to all-MiniLM-L6-v2)
            threshold: Detection threshold
            **kwargs: Additional arguments passed to __init__

        Returns:
            Configured TopicRestrictionScanner with embeddings enabled
        """
        from fi.evals.guardrails.scanners.topics import (List, Optional)
        return cls(
            allowed_topics=allowed_topics,
            denied_topics=denied_topics,
            use_embeddings=True,
            embedding_model=embedding_model,
            threshold=threshold,
            **kwargs,
        )


    @classmethod
    def semantic_only(
        cls,
        allowed_topics: Optional[List[str]] = None,
        denied_topics: Optional[List[str]] = None,
        embedding_model: Optional[str] = None,
        threshold: float = 0.5,
        **kwargs,
    ) -> "TopicRestrictionScanner":
        """
        Factory method to create a semantic-only topic scanner (no keywords).

        Args:
            allowed_topics: Allowed topic list
            denied_topics: Denied topic list
            embedding_model: Model to use
            threshold: Detection threshold
            **kwargs: Additional arguments

        Returns:
            Configured TopicRestrictionScanner using semantic-only detection
        """
        from fi.evals.guardrails.scanners.topics import (List, Optional)
        return cls(
            allowed_topics=allowed_topics,
            denied_topics=denied_topics,
            use_embeddings=True,
            combine_scores=False,
            embedding_model=embedding_model,
            threshold=threshold,
            **kwargs,
        )
