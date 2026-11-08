"""Evaluator evaluate operations."""
from __future__ import annotations

from fi.evals.evaluator import (Any, BatchRunResult, Dict, EvalTemplate, Optional, Union)


class _EvaluatorEvaluateMethods:
    __slots__ = ()

    def evaluate(
        self,
        eval_templates: Union[str, type[EvalTemplate]],
        inputs: Dict[str, Any],
        timeout: Optional[int] = None,
        model_name: Optional[str] = None,
        custom_eval_name: Optional[str] = None,
        trace_eval: Optional[bool] = False,
        platform: Optional[str] = None,
        is_async: Optional[bool] = False,
        error_localizer: Optional[bool] = False,
        eval_config: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> BatchRunResult:
        """
        Run a single or batch of evaluations independently

        Args:
            eval_templates: Evaluation name string (e.g., "Factual Accuracy")
            inputs: Single test case or list of test cases
            timeout: Optional timeout value for the evaluation
            model_name: Optional model name to use for the evaluation for Future AGI Agents
            span_id: Optional span_id to attach to the evaluation. If not provided, it will be retrieved from the OpenTelemetry context if available.
            custom_eval_name: Optional custom evaluation name to use for the evaluation. If not provided, eval will not be added to the span.
        Returns:
            BatchRunResult containing evaluation results

        Raises:
            ValidationError: If the inputs do not match the evaluation templates
            Exception: If the API request fails
        """
        from fi.evals.evaluator import (
            Any, BatchRunResult, Dict, EvalResponseHandler, EvalResult, EvalTemplate, HttpMethod,
            Optional, RequestConfig, Routes, ThreadPoolExecutor, TimeoutError, Union,
            _coerce_to_api_input, as_completed, inspect, logging,
        )
        if platform:
            if isinstance(eval_templates, str) and isinstance(inputs, dict) and custom_eval_name:
                return self._configure_evaluations(
                    eval_templates=eval_templates,
                    inputs=inputs,
                    platform=platform,
                    custom_eval_name=custom_eval_name,
                    model_name=model_name,
                    **kwargs
                )
            else:
                raise ValueError("Invalid arguments for platform configuration")


        def _extract_name(t) -> str | None:
            if isinstance(t, str):
                return t
            if isinstance(t, EvalTemplate):
                return t.eval_name
            if inspect.isclass(t) and issubclass(t, EvalTemplate):
                return t.eval_name
            return None

        eval_name = _extract_name(
            eval_templates[0] if isinstance(eval_templates, list) else eval_templates
        )

        span_id = None
        project_name = None
        if trace_eval:
            if not custom_eval_name:
                trace_eval = False
                logging.warning("Failed to trace the evaluation. Please set the custom_eval_name.")
            else:
                try:
                    from opentelemetry import trace

                    current_span = trace.get_current_span()
                    if current_span and current_span.is_recording():
                        span_context = current_span.get_span_context()
                        if span_context.is_valid:
                            span_id = format(span_context.span_id, "016x")
                            tracer_provider = trace.get_tracer_provider()
                            if hasattr(tracer_provider, "resource"):
                                attributes = tracer_provider.resource.attributes
                                project_name = attributes.get("project_name")

                    if not project_name:
                        trace_eval = False
                        logging.warning(
                            "Could not determine project_name from OpenTelemetry context. "
                            "Skipping trace_eval for this evaluation."
                        )

                except ImportError as exc:
                    logging.error(
                        "Future AGI SDK not found. "
                        "Please install 'fi-instrumentation-otel' to automatically enrich the evaluation with project context. "
                        "Evaluation: %s; error type: %s",
                        eval_name, type(exc).__name__,
                    )
                    return

        if eval_name is None:
            raise TypeError(
                "Unsupported eval_templates argument. "
                "Expect eval template class/obj or name str."
            )

        # Dynamic registry: filter user-supplied inputs to only the keys the
        # backend currently accepts for this eval. The api rejects supersets
        # (e.g. {output,input,context} for a template that only wants
        # {output}), so this can't be a pass-through. If the registry fetch
        # fails or the name is unknown, leave inputs untouched.
        if kwargs.get("skip_input_mapping") is not True and isinstance(inputs, dict):
            try:
                from fi.evals.core.cloud_registry import map_inputs_to_backend
                inputs = map_inputs_to_backend(
                    eval_name,
                    inputs,
                    base_url=self._base_url,
                    api_key=self._fi_api_key,
                    secret_key=self._fi_secret_key,
                    session=getattr(self, "_registry_session", None),
                )
            except Exception as exc:
                logging.debug(
                    "Dynamic input mapping skipped for evaluation %s; error type: %s",
                    eval_name, type(exc).__name__,
                )

        # The api validator accepts only strings, list[str], or list[list[str]].
        # JSON-serialize dict / list-of-dicts values (e.g. conversation messages)
        # so users can pass native Python objects without manually stringifying.
        if isinstance(inputs, dict):
            inputs = {k: _coerce_to_api_input(v) for k, v in inputs.items()}

        final_api_payload = {
            "eval_name": eval_name,
            "inputs": inputs,
            "model": model_name,
            "span_id": span_id,
            "custom_eval_name": custom_eval_name,
            "trace_eval": trace_eval,
            "is_async": is_async,
            "error_localizer": error_localizer,
        }

        if eval_config:
            final_api_payload["config"] = {"params": eval_config}


        all_results = []
        failed_inputs = []
        with ThreadPoolExecutor(max_workers=self._max_workers) as executor:
            # Submit the batch only once
            future = executor.submit(
                self.request,
                config=RequestConfig(
                    method=HttpMethod.POST,
                    url=f"{self._base_url}/{Routes.evaluatev2.value}",
                    json=final_api_payload,
                    timeout=timeout or self._default_timeout,
                ),
                response_handler=EvalResponseHandler,
            )
            future_to_input = {future: inputs}  # map single future to all inputs

            for future in as_completed(future_to_input):
                try:
                    response: BatchRunResult = future.result(timeout=timeout or self._default_timeout)
                    all_results.extend(response.eval_results)
                except TimeoutError as exc:
                    input_case = future_to_input[future]
                    logging.error(
                        "Evaluation %s timed out after %ss; error type: %s",
                        eval_name, timeout or self._default_timeout, type(exc).__name__,
                    )
                    failed_inputs.append(input_case)
                    all_results.append(
                        EvalResult(
                            name=eval_name,
                            output=None,
                            reason=f"Evaluation timed out after {timeout or self._default_timeout}s",
                            runtime=0,
                        )
                    )
                except Exception as exc:
                    input_case = future_to_input[future]
                    logging.error(
                        "Evaluation %s failed; error type: %s",
                        eval_name, type(exc).__name__,
                    )
                    failed_inputs.append(input_case)
                    all_results.append(
                        EvalResult(
                            name=eval_name,
                            output=None,
                            reason=str(exc),
                            runtime=0,
                        )
                    )

        if failed_inputs:
            logging.warning(f"Failed to evaluate {len(failed_inputs)} inputs out of {len(inputs)} total inputs")

        # Automatically enrich current span with evaluation results
        result = BatchRunResult(eval_results=all_results)
        try:
            from fi.evals.otel.enrichment import enrich_span_with_batch_result, is_auto_enrichment_enabled
            if is_auto_enrichment_enabled():
                enriched_count = enrich_span_with_batch_result(result)
                if enriched_count > 0:
                    logging.debug(f"Enriched active span with {enriched_count} evaluation results")
        except ImportError:
            pass  # OTEL enrichment not available
        except Exception as e:
            logging.debug(
                "Failed to enrich span for evaluation %s; error type: %s",
                eval_name, type(e).__name__,
            )

        return result


    def get_eval_result(self, eval_id: str):
        """
        Get the raw evaluation status payload by ID (unparsed).

        For a higher-level handle that understands the status envelope
        and can be awaited, see :py:meth:`get_execution`.
        """
        from fi.evals.evaluator import (HttpMethod, RequestConfig, Routes)
        url = f"{self._base_url}/{Routes.get_eval_result.value}"
        response = self.request(
            config=RequestConfig(
                method=HttpMethod.GET,
                url=url,
                params={"eval_id": eval_id},
                timeout=self._default_timeout,
            ),
        )

        return response.json()
