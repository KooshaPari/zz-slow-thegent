"""CodexProxyRunner — runs agents via Codex CLI pointing at CLIProxyAPIPlus.

Supports multi-agent on-device workflows with instance isolation,
resource-aware spawning, structured JSONL output parsing, config injection,
and typed error handling.
"""

import logging
import os
import shutil
import subprocess
import tempfile
from collections.abc import Callable
from pathlib import Path

from thegent.agents.base import AgentRunner, RunResult
from thegent.agents.cliproxy_manager import ensure_proxy_running
from thegent.agents.codex_proxy_base import (
    _LITELLM_CONTEXT_WINDOW_MAX,
    _PROXY_MODEL,
    CodexInstanceError,
    _build_config_flags,
    _check_and_track_instance,
    _create_isolated_home,
    _get_next_instance_id,
    _get_provider_retry_config,
    _isolate_codex_state,
    _normalize_context_usage_ratio,
    _resolve_codex,
    _run_with_retry,
    _write_config_override,
)
from thegent.agents.context_compactor import ContextCompactionResult, ContextCompactor
from thegent.agents.resilience import TransientAgentError
from thegent.config import ThegentSettings
from thegent.discovery import _is_triggered_by_agent_process
from thegent.governance.post_agent_run_hook import dispatch_post_agent_run_hook
from thegent.utils.routing_impl.circuit_breaker import (
    CircuitOpenError,
    ProviderCircuitBreakerRegistry,
    record_deployment_failure,
    record_deployment_success,
)
from thegent.utils.routing_impl.models import TaskMetadata
from thegent.utils.routing_impl.provider_types import ExecutionPath, get_execution_path

logger = logging.getLogger(__name__)


class CodexProxyRunner(AgentRunner):
    """Runs agents via Codex CLI pointing at CLIProxyAPIPlus.

    Supports multi-agent on-device workflows with:
    - Instance isolation via CODEX_HOME (isolated SQLite state)
    - Resource-aware spawning with max_concurrent limits
    - Structured JSONL output parsing (tokens, model, cost)
    - Config injection via temporary config.toml files
    - Typed error handling (AuthError, SandboxError, etc.)
    """

    def __init__(
        self,
        agent_name: str,
        settings: ThegentSettings | None = None,
        model: str = "",
        use_litellm_router: bool | None = None,
        codex_home: Path | None = None,
        memory_limit_mb: int = 512,
        max_concurrent_instances: int = 8,
        config_overrides: dict[str, str] | None = None,
        keep_isolated_home: bool = False,
    ) -> None:
        if agent_name not in _PROXY_MODEL:
            raise ValueError(f"Unknown proxy agent: {agent_name}")
        self.agent_name = agent_name
        self._settings = settings or ThegentSettings()
        self._model = model or _PROXY_MODEL[agent_name]
        self._use_litellm_router = (
            use_litellm_router if use_litellm_router is not None else self._settings.use_litellm_router
        )
        self.codex_home = codex_home
        self.memory_limit_mb = memory_limit_mb
        self.max_concurrent_instances = max_concurrent_instances
        self.config_overrides = config_overrides or {}
        self.keep_isolated_home = keep_isolated_home
        self.instance_id = _get_next_instance_id()

    def run_lightweight(
        self,
        prompt: str,
        cwd: Path | None,
        timeout: int = 600,
        *,
        agent_index: int = 0,
        use_stream: bool = True,
        live_output: bool = False,
        on_stdout: Callable[[str], None] | None = None,
        on_stderr: Callable[[str], None] | None = None,
        agent_model: str | None = None,
        config: dict[str, str | int | bool] | None = None,
        env: dict[str, str] | None = None,
    ) -> RunResult:
        """Run Codex in lightweight mode optimized for multi-agent orchestration.

        Automatically isolates state, uses workspace-write sandbox, and enables JSON streaming.
        Suitable for running 5-10 concurrent instances on a single machine.

        Args:
            prompt: User task/prompt
            cwd: Working directory
            timeout: Timeout in seconds (default 10 min for lightweight tasks)
            agent_index: Unique agent ID (0-9 for pool of 10) for state isolation
            use_stream: Whether to use JSON streaming (default True)
            live_output: Callback-based live output (default False)
            on_stdout: Callback for stdout lines
            on_stderr: Callback for stderr lines
            agent_model: Override default model
            config: Additional Codex config overrides (dict of key=value)
            env: Additional environment variables

        Returns:
            RunResult with exit code, stdout, stderr, timed_out flag

        # @trace FR-AGT-005
        """
        # Isolate state directory
        isolated_home = _isolate_codex_state(agent_index)

        full_env = os.environ.copy()
        if env:
            full_env.update(env)
        full_env["HOME"] = str(isolated_home)

        model = agent_model or self._model

        # Lightweight config defaults
        lightweight_config: dict[str, str | int | bool] = {
            "agent.mode": "lightweight",
            "performance.disable_semantic_indexing": "true",
            "context.max_context_window": "50000",
        }
        if config:
            lightweight_config.update(config)

        codex_cmd = _resolve_codex()
        cmd = [codex_cmd, "exec", "-", "--skip-git-repo-check", "--dangerously-bypass-approvals-and-sandbox"]

        # Add lightweight config flags
        cmd.extend(_build_config_flags(lightweight_config))

        if cwd:
            cmd.extend(["--cd", str(cwd)])
        if use_stream:
            cmd.append("--json")
        if model:
            cmd.extend(["--model", model])

        # Always use workspace-write for lightweight (safer than full-auto)
        cmd.extend(["--sandbox", "workspace-write"])

        try:
            return _run_with_retry(
                cmd,
                prompt,
                cwd,
                timeout,
                full_env,
                max_idle_seconds=self._settings.max_idle_seconds,
                max_wall_time=self._settings.max_wall_time,
                live_output=live_output,
                on_stdout=on_stdout,
                on_stderr=on_stderr,
            )
        except TransientAgentError as e:
            return e.result
        except FileNotFoundError:
            return RunResult(
                exit_code=1,
                stdout="",
                stderr=("codex CLI not found. Install: npm i -g @openai/codex\nOr add codex to PATH."),
                timed_out=False,
            )
        except subprocess.TimeoutExpired:
            return RunResult(
                exit_code=124,
                stdout="",
                stderr=f"Agent timed out after {timeout}s",
                timed_out=True,
            )

    def run(
        self,
        prompt: str,
        cwd: Path | None,
        mode: str,
        timeout: int,
        *,
        use_stream: bool = True,
        live_output: bool = False,
        on_stdout: Callable[[str], None] | None = None,
        on_stderr: Callable[[str], None] | None = None,
        agent_model: str | None = None,
        enable_search: bool = True,
        run_id: str | None = None,
        session_id: str | None = None,
        image_paths: list[str] | None = None,
        audio_paths: list[str] | None = None,
        env: dict[str, str] | None = None,
    ) -> RunResult:
        model = agent_model or self._model

        # WL-116: Handle audio transcript inputs
        audio_transcript: str | None = None
        if audio_paths:
            from thegent.agents.audio_inputs import (
                inject_transcript_into_prompt,
                load_transcripts,
            )

            audio_transcript, _audio_sources = load_transcripts(audio_paths)
            if audio_transcript:
                # Inject transcript into prompt for Codex
                prompt = inject_transcript_into_prompt(prompt, audio_transcript)
                logger.info("WL-116: Injected audio transcript into Codex prompt")

        # Check concurrent instance limit (Improvement 2)
        try:
            _check_and_track_instance(self.max_concurrent_instances)
        except CodexInstanceError as e:
            return RunResult(
                exit_code=1,
                stdout="",
                stderr=str(e),
                timed_out=False,
            )

        # Route via LiteLLM Router if enabled and not zen
        if self._use_litellm_router and self.agent_name != "zen":
            result = self._run_via_litellm_router(
                prompt, cwd, mode, timeout, model, use_stream, live_output, on_stdout, on_stderr, env=env
            )
            # WL-116: Add audio_transcript to result if audio was processed
            if audio_transcript:
                result = RunResult(
                    exit_code=result.exit_code,
                    stdout=result.stdout,
                    stderr=result.stderr,
                    timed_out=result.timed_out,
                    context_tokens_used=result.context_tokens_used,
                    context_window_max=result.context_window_max,
                    context_usage_ratio=result.context_usage_ratio,
                    audio_transcript=audio_transcript,
                    grounding_sources=result.grounding_sources,
                )
            return result

        full_env = os.environ.copy()
        if env:
            full_env.update(env)

        # Set up instance isolation (Improvement 1)
        isolated_home = None
        if self.codex_home is None:
            isolated_home = _create_isolated_home(self.instance_id)
            full_env["CODEX_HOME"] = str(isolated_home)
        else:
            full_env["CODEX_HOME"] = str(self.codex_home)

        # Prepare config override file (Improvement 4)
        temp_dir = None
        try:
            if self.config_overrides:
                temp_dir = Path(tempfile.mkdtemp(prefix="codex_config_"))
                _write_config_override(self.config_overrides, temp_dir)
                # Set env var to point to config directory
                full_env["CODEX_CONFIG_DIR"] = str(temp_dir)

            if self.agent_name == "zen":
                zen_base_url = getattr(self._settings, "zen_base_url", "") or os.environ.get("THGENT_ZEN_BASE_URL", "")
                base_url = (str(zen_base_url) or "https://api.opencode.ai").rstrip("/")
                api_key_env = (
                    getattr(self._settings, "zen_api_key", "")
                    or os.environ.get("THGENT_ZEN_API_KEY")
                    or os.environ.get("OPENCODE_API_KEY")
                    or os.environ.get("ZEN_API_KEY")
                    or ""
                ).strip()
                api_key = api_key_env
                if not api_key:
                    return RunResult(
                        exit_code=1,
                        stdout="",
                        stderr=(
                            "Zen API key missing. Set THGENT_ZEN_API_KEY (or OPENCODE_API_KEY / ZEN_API_KEY) "
                            "to use provider=zen."
                        ),
                        timed_out=False,
                    )
                full_env["OPENAI_BASE_URL"] = base_url
                full_env["OPENAI_API_KEY"] = api_key
            else:
                try:
                    base_url = ensure_proxy_running(self._settings)
                except (FileNotFoundError, RuntimeError) as e:
                    return RunResult(
                        exit_code=1,
                        stdout="",
                        stderr=str(e),
                        timed_out=False,
                    )
                full_env["OPENAI_BASE_URL"] = base_url.rstrip("/")
                full_env["OPENAI_API_KEY"] = "sk-dummy"

            # Set memory limit via ulimit (macOS/Linux) (Improvement 2)
            if self.memory_limit_mb > 0:
                # Note: ulimit is applied via shell; this is passed as env var for subprocess awareness
                full_env["CODEX_MEMORY_LIMIT_MB"] = str(self.memory_limit_mb)

            codex_cmd = _resolve_codex()
            cmd = [codex_cmd, "exec", "-", "--skip-git-repo-check"]
            if not _is_triggered_by_agent_process():
                cmd.append("--dangerously-bypass-approvals-and-sandbox")
            # codex no longer supports a top-level --search flag; leave search disabled by default
            # if enable_search:
            #     cmd.append("--search")
            if cwd:
                cmd.extend(["--cd", str(cwd)])
            if use_stream:
                cmd.append("--json")
            if model:
                cmd.extend(["--model", model])
            if mode == "write":
                cmd.extend(["--sandbox", "workspace-write"])
            elif mode == "full":
                cmd.extend(["--full-auto"])
            for image_path in image_paths or []:
                cmd.extend(["--image", image_path])

            # @trace WL-038 — capture result so $defer directives can be post-processed
            _inner_result: RunResult
            try:
                _inner_result = _run_with_retry(
                    cmd,
                    prompt,
                    cwd,
                    timeout,
                    full_env,
                    max_idle_seconds=self._settings.max_idle_seconds,
                    max_wall_time=self._settings.max_wall_time,
                    live_output=live_output,
                    on_stdout=on_stdout,
                    on_stderr=on_stderr,
                )
            except TransientAgentError as e:
                _inner_result = e.result
            except FileNotFoundError:
                _inner_result = RunResult(
                    exit_code=1,
                    stdout="",
                    stderr=("codex CLI not found. Install: npm i -g @openai/codex\nOr add codex to PATH."),
                    timed_out=False,
                )
            except subprocess.TimeoutExpired:
                _inner_result = RunResult(
                    exit_code=124,
                    stdout="",
                    stderr=f"Agent timed out after {timeout}s",
                    timed_out=True,
                )

            # WL-116: Add audio_transcript to result if audio was processed
            if audio_transcript:
                _inner_result = RunResult(
                    exit_code=_inner_result.exit_code,
                    stdout=_inner_result.stdout,
                    stderr=_inner_result.stderr,
                    timed_out=_inner_result.timed_out,
                    context_tokens_used=_inner_result.context_tokens_used,
                    context_window_max=_inner_result.context_window_max,
                    context_usage_ratio=_inner_result.context_usage_ratio,
                    audio_transcript=audio_transcript,
                    grounding_sources=_inner_result.grounding_sources,
                )

            if run_id is not None or session_id is not None:
                dispatch_post_agent_run_hook(
                    result=_inner_result,
                    run_id=run_id,
                    session_id=session_id,
                    cwd=cwd,
                    extra_context={
                        "agent": self.agent_name,
                        "model": model,
                        "mode": mode,
                        "timeout_seconds": timeout,
                        "use_stream": use_stream,
                        "enable_search": enable_search,
                    },
                )
            return self._process_output_deferrals(_inner_result, cwd=cwd)
        finally:
            # Clean up isolated home if not keeping for debugging (Improvement 1)
            if isolated_home and not self.keep_isolated_home:
                try:
                    shutil.rmtree(isolated_home)
                except OSError as e:
                    logger.warning(f"Failed to clean up isolated home {isolated_home}: {e}")

            # Clean up temp config directory (Improvement 4)
            if temp_dir:
                try:
                    shutil.rmtree(temp_dir)
                except OSError as e:
                    logger.warning(f"Failed to clean up temp config {temp_dir}: {e}")

    def _run_via_litellm_router(
        self,
        prompt: str,
        cwd: Path | None,
        mode: str,
        timeout: int,
        model: str,
        use_stream: bool,
        live_output: bool,
        on_stdout: Callable[[str], None] | None,
        on_stderr: Callable[[str], None] | None,
        env: dict[str, str] | None = None,
    ) -> RunResult:
        """Run via LiteLLM Router for Codex CLI compatibility."""
        try:
            from thegent.utils.routing_impl.litellm_router import get_enhanced_router

            router = get_enhanced_router()

            # Use model as-is; it should match a model alias in our catalog
            # which is what LiteLLM model_list uses for model_name.
            model_to_use = model

            result = router.route(prompt, model=model_to_use, stream=use_stream, timeout=timeout)

            if not result.success:
                return RunResult(
                    exit_code=1,
                    stdout="",
                    stderr=result.error or "Routing failed",
                    timed_out=False,
                )

            # Handle response
            if use_stream:
                # For Codex, we need to collect the stream into a single response
                # or handle it as Codex expects. Since we're emulating Codex,
                # we'll collect it for now unless we implement full SSE.
                stdout_collector = []
                for chunk in result.response or []:
                    content = ""
                    if hasattr(chunk, "choices") and chunk.choices:
                        delta = chunk.choices[0].delta
                        if hasattr(delta, "content") and delta.content:
                            content = delta.content
                    elif isinstance(chunk, dict):
                        # Handle dict response (from some LiteLLM adapters)
                        choices = chunk.get("choices", [])
                        if choices:
                            delta = choices[0].get("delta", {})
                            content = delta.get("content", "")

                    if content:
                        stdout_collector.append(content)
                        if on_stdout:
                            on_stdout(content)

                return RunResult(
                    exit_code=0,
                    stdout="".join(stdout_collector),
                    stderr="",
                    timed_out=False,
                )
            content = ""
            _resp_choices = getattr(result.response, "choices", None)
            if _resp_choices:
                choice = _resp_choices[0]
                msg = getattr(choice, "message", None) or getattr(choice, "delta", None)
                content = getattr(msg, "content", None) or ""
            elif isinstance(result.response, dict):
                choices = result.response.get("choices", [])
                if choices:
                    message = choices[0].get("message", {})
                    content = message.get("content", "")

            return RunResult(
                exit_code=0,
                stdout=content or "",
                stderr="",
                timed_out=False,
            )

        except Exception as e:
            logger.error("LiteLLM Router execution failed: %s", e, exc_info=True)
            return RunResult(
                exit_code=1,
                stdout="",
                stderr=f"LiteLLM Router execution failed: {e}",
                timed_out=False,
            )

    def run_with_metadata(
        self,
        prompt: str,
        cwd: Path | None,
        mode: str,
        timeout: int,
        *,
        metadata: TaskMetadata | None = None,
        use_stream: bool = True,
        live_output: bool = False,
        on_stdout: Callable[[str], None] | None = None,
        on_stderr: Callable[[str], None] | None = None,
        enable_search: bool = True,
        run_id: str | None = None,
        session_id: str | None = None,
    ) -> RunResult:
        """Run agent using resolved routing from TaskMetadata.

        This method consumes resolved_provider and resolved_model_alias
        from the routing classification.

        Args:
            prompt: User prompt
            cwd: Working directory
            mode: Execution mode (read/write/full)
            timeout: Timeout in seconds
            metadata: TaskMetadata with resolved routing

        Returns:
            RunResult from execution
        """
        # Determine provider and model from metadata
        provider: str = ((metadata.resolved_provider if metadata else None) or self.agent_name) or ""
        model: str = ((metadata.resolved_model_alias if metadata else None) or self._model) or ""

        # Determine execution path
        exec_path = get_execution_path(provider)

        if exec_path == ExecutionPath.NATIVE_CLI:
            return self._execute_native_cli(prompt, cwd, mode, timeout, model, run_id=run_id, session_id=session_id)
        if exec_path == ExecutionPath.LITELLM_API:
            return self._execute_litellm_api(
                prompt,
                cwd,
                mode,
                timeout,
                provider,
                model,
                run_id=run_id,
                session_id=session_id,
            )
        # CLIProxyAPIPlus path (default)
        return self.run(
            prompt,
            cwd,
            mode,
            timeout,
            agent_model=model,
            use_stream=use_stream,
            run_id=run_id,
            session_id=session_id,
        )

    def _execute_native_cli(
        self,
        prompt: str,
        cwd: Path | None,
        mode: str,
        timeout: int,
        model: str,
        run_id: str | None = None,
        session_id: str | None = None,
    ) -> RunResult:
        """Execute via native codex CLI (for codex provider)."""
        # Current implementation uses codex CLI already
        return self.run(prompt, cwd, mode, timeout, agent_model=model, run_id=run_id, session_id=session_id)

    def _execute_litellm_api(
        self,
        prompt: str,
        cwd: Path | None,
        mode: str,
        timeout: int,
        provider: str,
        model: str,
        run_id: str | None = None,
        session_id: str | None = None,
    ) -> RunResult:
        """Execute via LiteLLM direct API (for API key providers).

        Uses litellm.completion() to call providers directly without
        going through the CLIProxyAPIPlus proxy. Supports providers
        like minimax, glm, nim, kilo that have API keys.

        Implements provider-specific retry with circuit breaker for resilience.

        Args:
            prompt: User prompt to send to the model
            cwd: Working directory (not used for API calls, kept for signature compatibility)
            mode: Execution mode (not used for API calls, kept for signature compatibility)
            timeout: Timeout in seconds for the API call
            provider: Provider name (e.g., "minimax", "glm")
            model: Model name/alias (e.g., "minimax-m2.5")

        Returns:
            RunResult with the model response or error
        """
        try:
            from litellm import completion
        except ImportError as e:
            logger.error(f"litellm not installed: {e}")
            return RunResult(
                exit_code=1,
                stdout="",
                stderr="litellm package not installed. Install with: pip install litellm",
                timed_out=False,
            )

        # Build model string in LiteLLM format: "provider/model"
        model_string = f"{provider}/{model}"

        # Get API key environment variable name for this provider
        api_key_env = self._get_api_key_env(provider)
        api_key = os.environ.get(api_key_env)

        if not api_key:
            logger.error(f"API key not found for provider {provider} (env: {api_key_env})")
            return RunResult(
                exit_code=1,
                stdout="",
                stderr=f"API key not found. Set {api_key_env} environment variable.",
                timed_out=False,
            )

        # Get provider-specific retry config
        retry_config = _get_provider_retry_config(provider)

        # Get or create circuit breaker for this provider
        cb_registry = ProviderCircuitBreakerRegistry.get_instance()
        cb = cb_registry.get(provider)

        logger.info(f"Calling LiteLLM API: {model_string}")
        messages, compaction = self._prepare_litellm_messages(
            prompt=prompt,
            cwd=cwd,
            mode=mode,
            model=model,
        )
        normalized_usage_ratio = _normalize_context_usage_ratio(compaction.usage_ratio)
        estimated_tokens = round(normalized_usage_ratio * _LITELLM_CONTEXT_WINDOW_MAX)

        # Define the actual API call function for retry
        def _do_completion() -> tuple[str, bool]:
            """Execute litellm.completion and return (content, is_timeout)."""
            # Check circuit breaker first
            try:
                cb.call(lambda: None)  # This will raise if circuit is open
            except CircuitOpenError:
                logger.warning(f"Circuit breaker OPEN for provider {provider}, failing fast")
                raise

            try:
                response = completion(
                    model=model_string,
                    messages=messages,
                    api_key=api_key,
                    timeout=timeout,
                )

                # Extract response content from LiteLLM response.
                choices = getattr(response, "choices", None)
                choice = choices[0] if choices else None
                message_or_delta = (
                    (getattr(choice, "message", None) or getattr(choice, "delta", None)) if choice is not None else None
                )
                content = getattr(message_or_delta, "content", None)

                # Record success for circuit breaker
                record_deployment_success(provider)

                return content or "", False

            except Exception as e:
                error_msg = str(e)
                is_timeout = "timeout" in error_msg.lower() or "timed out" in error_msg.lower()

                # Record failure for circuit breaker
                record_deployment_failure(provider, e)

                # Check for rate limit - could have Retry-After header
                if is_timeout or "429" in error_msg or "rate limit" in error_msg.lower():
                    logger.warning(f"Rate limit or timeout for {provider}: {error_msg}")

                raise

        # Execute with retry using tenacity
        from tenacity import (
            retry,
            retry_if_exception_type,
            stop_after_attempt,
            wait_exponential,
        )

        @retry(
            stop=stop_after_attempt(retry_config["max_attempts"]),
            wait=wait_exponential(
                multiplier=retry_config["backoff_multiplier"],
                min=retry_config["min_wait"],
                max=retry_config["max_wait"],
            ),
            retry=retry_if_exception_type((Exception,)),
            before_sleep=lambda retry_state: logger.warning(
                "Retrying LiteLLM API call (attempt %d/%d) for provider %s: %s",
                retry_state.attempt_number,
                retry_config["max_attempts"],
                provider,
                retry_state.outcome.exception() if retry_state.outcome else "unknown",
            ),
            reraise=True,
        )
        def _execute_with_retry():
            return _do_completion()

        try:
            content, is_timeout = _execute_with_retry()
            logger.info(f"LiteLLM API call successful: {model_string}")
            return RunResult(
                exit_code=0,
                stdout=content,
                stderr="",
                timed_out=is_timeout,
                context_tokens_used=estimated_tokens,
                context_window_max=_LITELLM_CONTEXT_WINDOW_MAX,
                context_usage_ratio=normalized_usage_ratio,
            )

        except Exception as e:
            error_msg = str(e)
            logger.error(f"LiteLLM API call failed after retries: {error_msg}")

            # Check for timeout-related errors
            is_timeout = "timeout" in error_msg.lower() or "timed out" in error_msg.lower()

            # Check if circuit breaker is now open
            if cb.state == "open":
                logger.error(f"Circuit breaker now OPEN for provider {provider}")

            return RunResult(
                exit_code=1,
                stdout="",
                stderr=f"LiteLLM API error: {error_msg}",
                timed_out=is_timeout,
                context_tokens_used=estimated_tokens,
                context_window_max=_LITELLM_CONTEXT_WINDOW_MAX,
                context_usage_ratio=normalized_usage_ratio,
            )

    def _prepare_litellm_messages(
        self,
        *,
        prompt: str,
        cwd: Path | None,
        mode: str,
        model: str,
        context_window_max: int = _LITELLM_CONTEXT_WINDOW_MAX,
    ) -> tuple[list[dict[str, str]], ContextCompactionResult]:
        """Build Litellm messages and compact optional skill context when needed."""
        turns: list[dict[str, str]] = [
            {"role": "system", "content": "You are running inside the thegent codex proxy runner."},
        ]

        skill_suffix = self.get_skill_prompt_suffix().strip()
        if skill_suffix:
            turns.append({"role": "system", "content": skill_suffix})

        turns.append({"role": "system", "content": f"Execution agent={self.agent_name} model={model}"})
        turns.append({"role": "system", "content": f"Execution mode={mode} cwd={cwd or Path.cwd()}."})
        turns.append({"role": "user", "content": prompt})

        compactor = ContextCompactor()
        compaction = compactor.compact(turns, context_window_max)
        return compaction.turns, compaction

    @staticmethod
    def _get_api_key_env(provider: str) -> str:
        """Get environment variable name for provider API key.

        Args:
            provider: Provider name (e.g., "minimax", "glm")

        Returns:
            Environment variable name for the API key
        """
        mapping = {
            "minimax": "MINIMAX_API_KEY",
            "nim": "NVIDIA_API_KEY",
            "glm": "ZHIPU_API_KEY",
            "kilo": "KILO_API_KEY",
        }
        return mapping.get(provider, f"{provider.upper()}_API_KEY")
