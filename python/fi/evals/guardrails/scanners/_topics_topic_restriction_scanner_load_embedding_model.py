"""TopicRestrictionScanner load embedding model operations."""
from __future__ import annotations

from fi.evals.guardrails.scanners.topics import (Any, Dict)


class _TopicRestrictionScannerLoadEmbeddingModelMethods:
    __slots__ = ()

    def _load_embedding_model(self) -> bool:
        """
        Lazy load the embedding model and compute topic embeddings.

        Returns:
            True if model loaded successfully, False otherwise
        """
        if self._embedding_model is not None:
            return self._embeddings_available

        try:
            from sentence_transformers import SentenceTransformer

            # Determine device
            device = self.device
            if device is None:
                try:
                    import torch
                    if torch.cuda.is_available():
                        device = "cuda"
                    elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                        device = "mps"
                    else:
                        device = "cpu"
                except ImportError:
                    device = "cpu"

            # Load embedding model
            self._embedding_model = SentenceTransformer(
                self.embedding_model_name,
                device=device,
            )
            self._device = device

            # Pre-compute topic embeddings
            self._compute_topic_embeddings()

            self._embeddings_available = True
            return True

        except ImportError as e:
            self._embeddings_load_error = f"sentence-transformers not installed: {e}"
            self._embeddings_available = False
            return False
        except Exception as e:
            self._embeddings_load_error = f"Failed to load embedding model: {e}"
            self._embeddings_available = False
            return False


    def _compute_topic_embeddings(self) -> None:
        """Pre-compute embeddings for all topic descriptions."""
        if self._embedding_model is None:
            return

        self._topic_embeddings = {}

        # Determine which topics to compute embeddings for
        relevant_topics = set()
        if self.allowed_topics:
            relevant_topics.update(self.allowed_topics)
        if self.denied_topics:
            relevant_topics.update(self.denied_topics)
        if not relevant_topics:
            # Compute for all topics if no specific restriction
            relevant_topics = set(self.topic_descriptions.keys())

        for topic in relevant_topics:
            if topic in self.topic_descriptions:
                description = self.topic_descriptions[topic]
            else:
                # Fallback to keywords as description
                keywords = self.topics.get(topic, set())
                description = " ".join(keywords) if keywords else topic

            embedding = self._embedding_model.encode(
                description,
                convert_to_tensor=True,
                normalize_embeddings=True,
            )
            self._topic_embeddings[topic] = embedding


    def _semantic_similarity(
        self, content: str
    ) -> Dict[str, Dict[str, Any]]:
        """
        Compute semantic similarity between content and topic descriptions.

        Args:
            content: Text to analyze

        Returns:
            Dict of {topic: {similarity, confidence}}
        """
        from fi.evals.guardrails.scanners.topics import (Any, Dict)
        if not self._embeddings_available or self._embedding_model is None:
            return {}

        try:
            from sentence_transformers import util

            # Encode content
            content_embedding = self._embedding_model.encode(
                content,
                convert_to_tensor=True,
                normalize_embeddings=True,
            )

            results = {}
            for topic, topic_embedding in self._topic_embeddings.items():
                # Compute cosine similarity
                similarity = util.cos_sim(content_embedding, topic_embedding).item()

                # Normalize to 0-1 range (cosine similarity can be negative)
                confidence = max(0.0, (similarity + 1.0) / 2.0)

                results[topic] = {
                    "similarity": similarity,
                    "confidence": confidence,
                    "method": "semantic",
                }

            return results

        except Exception as e:
            # Return empty on error
            return {}


    def _detect_topics_keywords(self, text: str) -> Dict[str, Dict]:
        """
        Detect topics in text based on keyword matching.

        Returns:
            Dict of {topic: {count, keywords, confidence, method}}
        """
        from fi.evals.guardrails.scanners.topics import (Dict)
        detected = {}

        for topic, patterns in self._topic_patterns.items():
            matched_keywords = []
            for pattern in patterns:
                matches = pattern.findall(text)
                if matches:
                    matched_keywords.extend(matches)

            if len(matched_keywords) >= self.min_keyword_matches:
                # Calculate confidence based on keyword density
                total_keywords = len(self.topics[topic])
                unique_matches = len(set(kw.lower() for kw in matched_keywords))
                confidence = min(unique_matches / total_keywords * 2, 1.0)

                detected[topic] = {
                    "count": len(matched_keywords),
                    "unique_count": unique_matches,
                    "keywords": list(set(matched_keywords)),
                    "confidence": confidence,
                    "method": "keyword",
                }

        return detected


    def _detect_topics(self, text: str) -> Dict[str, Dict]:
        """
        Detect topics using configured method(s).

        Returns:
            Dict of {topic: {confidence, method, ...}}
        """
        from fi.evals.guardrails.scanners.topics import (Dict)
        # Get keyword-based detection
        keyword_results = self._detect_topics_keywords(text)

        # Get semantic detection if enabled
        semantic_results = {}
        if self.use_embeddings and self._embeddings_available:
            semantic_results = self._semantic_similarity(text)

        # Combine results
        if not self.use_embeddings or not self._embeddings_available:
            return keyword_results

        if not self.combine_scores:
            # Semantic-only mode (filter by threshold)
            return {
                topic: info
                for topic, info in semantic_results.items()
                if info["confidence"] >= self.semantic_threshold
            }

        # Hybrid mode: combine scores
        all_topics = set(keyword_results.keys()) | set(semantic_results.keys())
        combined = {}

        for topic in all_topics:
            kw_info = keyword_results.get(topic, {})
            sem_info = semantic_results.get(topic, {})

            kw_conf = kw_info.get("confidence", 0.0)
            sem_conf = sem_info.get("confidence", 0.0)

            # Weighted combination
            combined_confidence = (
                self.keyword_weight * kw_conf +
                self.embedding_weight * sem_conf
            )

            combined[topic] = {
                "confidence": combined_confidence,
                "keyword_confidence": kw_conf,
                "semantic_confidence": sem_conf,
                "method": "hybrid",
            }

            # Include keyword details if available
            if kw_info:
                combined[topic]["keywords"] = kw_info.get("keywords", [])
                combined[topic]["count"] = kw_info.get("count", 0)

            # Include semantic similarity if available
            if sem_info:
                combined[topic]["similarity"] = sem_info.get("similarity", 0.0)

        return combined
