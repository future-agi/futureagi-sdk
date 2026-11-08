"""JailbreakScanner load ml model operations."""
from __future__ import annotations

from typing import TYPE_CHECKING
from fi.evals.guardrails.scanners.jailbreak import (
    Any, Dict, List, Optional, ScanMatch, ScanResult, Tuple,
)

if TYPE_CHECKING:
    from fi.evals.guardrails.scanners.jailbreak import JailbreakScanner


class _JailbreakScannerLoadMlModelMethods:
    __slots__ = ()

    def _load_ml_model(self) -> bool:
        """
        Lazy load the ML model for jailbreak detection.

        Returns:
            True if model loaded successfully, False otherwise
        """
        if self._model is not None:
            return self._ml_available

        try:
            import torch
            from transformers import AutoModelForSequenceClassification, AutoTokenizer

            # Determine device
            if self.device:
                device = self.device
            elif torch.cuda.is_available():
                device = "cuda"
            elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                device = "mps"
            else:
                device = "cpu"

            # Load tokenizer and model
            try:
                self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
                self._model = AutoModelForSequenceClassification.from_pretrained(
                    self.model_name
                ).to(device)
                self._model.eval()
            except Exception as e:
                # Try fallback model
                if self.model_name != self.FALLBACK_MODEL:
                    self._tokenizer = AutoTokenizer.from_pretrained(self.FALLBACK_MODEL)
                    self._model = AutoModelForSequenceClassification.from_pretrained(
                        self.FALLBACK_MODEL
                    ).to(device)
                    self._model.eval()
                    self.model_name = self.FALLBACK_MODEL
                else:
                    raise e

            self._device = device
            self._ml_available = True
            return True

        except ImportError as e:
            self._ml_load_error = f"transformers/torch not installed: {e}"
            self._ml_available = False
            return False
        except Exception as e:
            self._ml_load_error = f"Failed to load model {self.model_name}: {e}"
            self._ml_available = False
            return False


    def _ml_predict(self, content: str) -> Tuple[float, Dict[str, Any]]:
        """
        Run ML model prediction on content.

        Args:
            content: Text to classify

        Returns:
            Tuple of (jailbreak_probability, metadata)
        """
        from fi.evals.guardrails.scanners.jailbreak import (Any, Dict, Tuple)
        if not self._ml_available or self._model is None:
            return 0.0, {"ml_error": self._ml_load_error or "Model not loaded"}

        try:
            import torch

            # Tokenize
            inputs = self._tokenizer(
                content,
                return_tensors="pt",
                truncation=True,
                max_length=512,
                padding=True,
            )

            # Move to device
            inputs = {k: v.to(self._device) for k, v in inputs.items()}

            # Inference
            with torch.no_grad():
                outputs = self._model(**inputs)
                logits = outputs.logits

                # Apply softmax to get probabilities
                probs = torch.nn.functional.softmax(logits, dim=-1)

                # Get the jailbreak/injection probability
                # Most models have label 1 as the positive (jailbreak) class
                if probs.shape[-1] == 2:
                    jailbreak_prob = probs[0, 1].item()
                else:
                    # For single class, use sigmoid
                    jailbreak_prob = torch.sigmoid(logits[0, 0]).item()

            return jailbreak_prob, {
                "ml_model": self.model_name,
                "ml_confidence": jailbreak_prob,
                "ml_device": str(self._device),
            }

        except Exception as e:
            return 0.0, {"ml_error": str(e)}


    def _pattern_scan(self, content: str) -> Tuple[List[ScanMatch], float]:
        """
        Run pattern-based scanning.

        Returns:
            Tuple of (matches, max_confidence)
        """
        from fi.evals.guardrails.scanners.jailbreak import (List, ScanMatch, Tuple)
        matches = []
        max_confidence = 0.0

        for pattern, name, confidence in self._compiled_patterns:
            for match in pattern.finditer(content):
                matches.append(ScanMatch(
                    pattern_name=name,
                    matched_text=match.group(),
                    start=match.start(),
                    end=match.end(),
                    confidence=confidence,
                ))
                max_confidence = max(max_confidence, confidence)

        return matches, max_confidence


    def scan(self, content: str, context: Optional[str] = None) -> ScanResult:
        """
        Scan content for jailbreak attempts.

        Uses pattern matching, ML detection, or both depending on configuration.

        Args:
            content: Content to scan
            context: Optional context (not used)

        Returns:
            ScanResult with detection details
        """
        from fi.evals.guardrails.scanners.jailbreak import (Optional, ScanMatch, ScanResult, time)
        start = time.perf_counter()
        metadata: Dict[str, Any] = {}

        # Run pattern-based scan
        pattern_matches, pattern_score = self._pattern_scan(content)

        # Run ML-based scan if enabled
        ml_score = 0.0
        if self.use_ml:
            ml_score, ml_metadata = self._ml_predict(content)
            metadata.update(ml_metadata)

        # Calculate final score
        if self.use_ml and self._ml_available:
            if self.combine_scores:
                # Hybrid: weighted combination
                final_score = (
                    self.ml_weight * ml_score +
                    self.pattern_weight * pattern_score
                )
                metadata["scoring_mode"] = "hybrid"
                metadata["pattern_score"] = pattern_score
                metadata["ml_score"] = ml_score
            else:
                # ML-only when available
                final_score = ml_score
                metadata["scoring_mode"] = "ml_only"
        else:
            # Pattern-only
            final_score = pattern_score
            metadata["scoring_mode"] = "pattern_only"

        # Add ML match if significant
        matches = pattern_matches.copy()
        if self.use_ml and ml_score >= self.threshold:
            matches.append(ScanMatch(
                pattern_name="ml_jailbreak_detection",
                matched_text=content[:100] + "..." if len(content) > 100 else content,
                start=0,
                end=len(content),
                confidence=ml_score,
                metadata={"model": self.model_name},
            ))

        latency = (time.perf_counter() - start) * 1000

        # Filter by threshold
        significant_matches = [m for m in matches if m.confidence >= self.threshold]

        if significant_matches or final_score >= self.threshold:
            detected_types = set(m.pattern_name for m in significant_matches)
            return self._create_result(
                passed=False,
                matches=significant_matches,
                score=final_score,
                reason=f"Jailbreak attempt detected: {', '.join(detected_types) if detected_types else 'ML detection'}",
                latency_ms=latency,
                metadata=metadata,
            )

        return self._create_result(
            passed=True,
            matches=[],
            score=final_score,
            reason="No jailbreak patterns detected",
            latency_ms=latency,
            metadata=metadata,
        )


    @classmethod
    def with_ml(
        cls,
        model_name: Optional[str] = None,
        threshold: float = 0.7,
        **kwargs,
    ) -> "JailbreakScanner":
        """
        Factory method to create an ML-enabled jailbreak scanner.

        Args:
            model_name: Model to use (defaults to Prompt-Guard-86M)
            threshold: Detection threshold
            **kwargs: Additional arguments passed to __init__

        Returns:
            Configured JailbreakScanner with ML enabled
        """
        from fi.evals.guardrails.scanners.jailbreak import (Optional)
        return cls(
            use_ml=True,
            model_name=model_name,
            threshold=threshold,
            **kwargs,
        )
