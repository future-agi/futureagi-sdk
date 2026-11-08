"""Protect sanitize reason operations."""
from __future__ import annotations

from fi.evals.protect import (Dict, List, Optional, ProtectInputAdapter, Tuple, ValidationError)


class _ProtectSanitizeReasonMethods:
    __slots__ = ()

    def _sanitize_reason(self, text: Optional[str]) -> Optional[str]:
        """Ensure the traceback or server URL doesn't reach the end user."""
        from fi.evals.protect import (Optional, re)
        if not text:
            return None
        # Strip URLs, tracebacks, and noisy client errors
        text = re.sub(r'https?://\S+', '[redacted]', text)
        text = re.sub(r'(Traceback.*?$)', '[redacted]', text, flags=re.I|re.S)
        text = re.sub(r'\b\d{3}\s+(Client|Server)\s+Error:.*', 'Request failed.', text, flags=re.I)
        # Also redact bare hostnames/IPs (defense-in-depth)
        text = re.sub(r'\b([a-z0-9-]+\.)+[a-z]{2,}\b', '[redacted]', text, flags=re.I)
        text = re.sub(r'\b\d{1,3}(?:\.\d{1,3}){3}\b', '[redacted]', text)
        return text.strip()


    def _check_rule_sync(
        self, rule: Dict, test_case: ProtectInputAdapter
    ) -> Tuple[str, bool, Optional[str], Optional[str]]:
        """
        Synchronous version of rule checking

        Returns:
            Tuple[str, bool, Optional[str], Optional[str]]:
        """
        from fi.evals.protect import (
            Dict, EvalResponseHandler, HttpMethod, Optional, ProtectInputAdapter, RequestConfig,
            Routes, Tuple,
        )
        # thread_name = threading.current_thread().name
        # start_time = time.time()
        # print(f"Starting rule check for {rule['metric']} in thread {thread_name} at {start_time}")

        template_class = self.metric_map[rule["metric"]]
        if rule["metric"] == "Data Privacy":
            template = template_class(
                config={"call_type": "protect", "check_internet": False}
            )
            # template = template_class(config={"check_internet": False})
        else:
            template = template_class(config={"call_type": "protect"})
            # template = template_class(config={})

        payload = {
            "inputs": [test_case.model_dump()],
            "config": {
                template.eval_id: template.config
            },
        }
        # print("sending the request to: ", f"{self.evaluator._base_url}/{Routes.evaluate.value}")
        # print("payload: ", payload["inputs"][0]["input"][:100])

        try:
            eval_result = self.evaluator.request(
                config=RequestConfig(
                    method=HttpMethod.POST,
                    url=f"{self.evaluator._base_url}/{Routes.evaluate.value}",
                    json=payload,
                    timeout=3000
                ),
                response_handler=EvalResponseHandler,
            )
        except Exception as e:
            err_msg = (
                "We couldn't process this request. Check your input or your credit balance."
                "If it keeps failing, contact support."
            )
            # Return a synthetic “failed” for this rule so the outer loop can present a clean error.
            return rule["metric"], True, err_msg, None

        # end_time = time.time()
        # print(f"Completed rule check for {rule['metric']} in thread {thread_name} at {end_time} (took {end_time - start_time:.2f}s)")

        reason_text: Optional[str] = None

        if eval_result.eval_results:
            result = eval_result.eval_results[0]
            detected_values = [result.output]

            should_trigger = False
            if rule["type"] == "any":
                should_trigger = any(
                    value in rule["contains"] for value in detected_values
                )
            elif rule["type"] == "all":
                should_trigger = all(
                    value in rule["contains"] for value in detected_values
                )

            if should_trigger:
                if rule["_internal_reason_flag"]:
                    # message = rule['action'] + f' Reason: {result.reason}'
                    message = rule["action"]
                    reason_text = self._sanitize_reason(result.reason) if rule["_internal_reason_flag"] else None
                else:
                    message = rule["action"]
                return rule["metric"], True, message, reason_text

        return rule["metric"], False, None, None


    def _process_rules_batch(
        self, rules: List[Dict], test_case: ProtectInputAdapter, remaining_time: float
    ) -> Tuple[List[str], List[str], List[str], List[str], List[str]]:
        """
        Process a batch of rules in parallel

        Args:
            rules: List of rules to process
            test_case: Test case to evaluate
            remaining_time: Time remaining for processing

        Returns:
            Tuple[List[str], List[str], List[str], List[str], List[str]]:
                (failure_messages, completed_rules, uncompleted_rules, failure_reasons, failed_rule)
        """
        from fi.evals.protect import (
            Dict, List, ProtectInputAdapter, ThreadPoolExecutor, TimeoutError, Tuple, as_completed,
        )
        # print(f"\nProcessing batch of {len(rules)} rules")
        # batch_start = time.time()

        completed_rules = []
        uncompleted_rules = [rule["metric"] for rule in rules]
        failure_messages = []
        failure_reasons = []
        failed_rule = []

        with ThreadPoolExecutor(max_workers=5) as executor:
            # Submit all rules to the thread pool
            future_to_rule = {
                executor.submit(self._check_rule_sync, rule, test_case): rule["metric"]
                for rule in rules
            }

            try:
                # Wait for futures to complete with timeout
                for future in as_completed(future_to_rule, timeout=remaining_time):
                    rule_name = future_to_rule[future]
                    try:
                        metric, triggered, message, reason_text = future.result()
                        # Update tracking lists
                        completed_rules.append(metric)
                        if rule_name in uncompleted_rules:
                            uncompleted_rules.remove(rule_name)

                        if triggered:
                            failure_messages.append(message)
                            if reason_text:
                                failure_reasons.append(reason_text)
                            failed_rule.append(rule_name)
                            # Cancel remaining futures if a rule fails
                            for f_key, f_val in future_to_rule.items():
                                if not f_key.done():
                                    f_key.cancel()

                    except Exception as e:
                        if rule_name in uncompleted_rules:
                            # uncompleted_rules.remove(rule_name) # Errored rule should remain uncompleted
                            pass

            except TimeoutError:
                # print(
                #     f"Timeout reached. {len(completed_rules)} rules completed, "
                #     f"{len(uncompleted_rules)} rules incomplete"
                # )
                all_submitted_rules = [r["metric"] for r in rules]
                uncompleted_rules = [r for r in all_submitted_rules if r not in completed_rules]

        # batch_end = time.time()
        # print(f"Batch processing completed in {batch_end - batch_start:.2f}s\n")

        return (
            failure_messages,
            completed_rules,
            uncompleted_rules,
            failure_reasons,
            failed_rule,
        )


    def _is_url(self, text: str) -> bool:
        """
        Check if the input text is a URL or URL-like string.

        Args:
            text: String to check

        Returns:
            bool: True if input appears to be a URL, False otherwise
        """
        from fi.evals.protect import (urlparse)
        # Check if it's an explicit URL with a scheme
        parsed_url = urlparse(text)
        if parsed_url.scheme in ['http', 'https']:
            return True

        # Check for URL-like patterns without scheme
        text_lower = text.lower()
        # Check for common TLDs
        common_tlds = ['.com', '.org', '.net', '.edu', '.gov', '.io', '.co']
        has_tld = any(tld in text_lower for tld in common_tlds)

        # Check for patterns like "www." at the beginning
        starts_with_www = text_lower.startswith('www.')

        # Check for domain-like pattern (example.com)
        has_domain_pattern = '.' in text_lower and not text_lower.startswith('.') and not text_lower.endswith('.')

        return (has_tld and has_domain_pattern) or starts_with_www


    def _is_only_url(self, text: str) -> bool:
        """
        Check if the input text is solely a URL without additional content.

        Args:
            text: String to check

        Returns:
            bool: True if the entire input appears to be just a URL, False otherwise
        """
        # Remove whitespace for checking
        text = text.strip()

        # If the string contains spaces, it's not only a URL
        if ' ' in text:
            return False

        # Check if what remains is a URL
        return self._is_url(text)


    def _format_adapter_error(self, ve: ValidationError) -> str:
        """
        Convert Pydantic validation errors into a single, user-friendly line.
        No stack traces, no class names, no internal URLs.
        """
        from fi.evals.protect import (ValidationError)
        # Default fallback:
        friendly = (
            "We couldn't read that input. Please use text, a direct media URL, "
            "or a supported file type (MP3/WAV for audio; JPG/PNG/WebP/GIF/BMP/TIFF/SVG for images)."
        )

        try:
            for err in ve.errors():
                msg = (err.get("msg") or "").lower()

                # Specific: unsupported local file type (e.g., .ogg)
                if "unsupported local file type" in msg:
                    return (
                        "Unsupported file type. Supported audio: MP3, WAV. "
                        "Supported image: JPG, PNG, WebP, GIF, BMP, TIFF, SVG."
                    )

                # Specific: data: URI with non-media
                if "unsupported data uri mime" in msg:
                    return "Only audio/* or image/* data: URIs are supported."

                # Specific: empty/whitespace
                if "input cannot be empty" in msg:
                    return "Input cannot be empty."

                # Specific: looks like a preview page not a raw file
                if "preview page, not a direct file" in msg:
                    return (
                        "This link looks like a preview page. Please use a direct download URL "
                        "(e.g., raw.githubusercontent.com for GitHub; export=download for Google Drive; "
                        "dl.dropboxusercontent.com for Dropbox)."
                    )
        except Exception:
            pass

        return friendly
