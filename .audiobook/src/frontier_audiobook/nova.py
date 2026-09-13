"""Amazon Nova 2 Sonic bidirectional-stream adapter.

AWS SDK imports are deliberately lazy so planning and dry runs need no installed
SDK, credentials, network access, or billable model invocation.
"""

from __future__ import annotations

import asyncio
import base64
import json
import multiprocessing
import os
import time
import uuid
from dataclasses import dataclass
from typing import Any

from .config import NovaSettings
from .errors import InputError
from .util import json_loads_strict


@dataclass(frozen=True)
class NovaRenderResult:
    audio_lpcm: bytes
    final_transcript: str
    events: tuple[dict[str, Any], ...]
    completion_stop_reason: str


async def _send_event(stream: Any, event: dict[str, Any], input_chunk_type: Any, payload_type: Any) -> None:
    encoded = json.dumps({"event": event}, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    await stream.input_stream.send(input_chunk_type(value=payload_type(bytes_=encoded)))


def _content_id(content: dict[str, Any], event_name: str) -> str:
    value = content.get("contentId")
    if not isinstance(value, str) or not value:
        raise InputError(f"Nova {event_name} event has no contentId")
    return value


def _event_identity(content: dict[str, Any], event_name: str) -> tuple[str, str]:
    session_id = content.get("sessionId")
    if session_id is not None and (not isinstance(session_id, str) or not session_id):
        raise InputError(f"Nova {event_name} event has an invalid sessionId")
    values: list[str] = []
    for field in ("promptName", "completionId"):
        value = content.get(field)
        if not isinstance(value, str) or not value:
            raise InputError(f"Nova {event_name} event has no {field}")
        values.append(value)
    return values[0], values[1]


def _bind_prompt_name(
    content: dict[str, Any],
    event_name: str,
    expected_prompt_name: str | None,
    seen_prompt_name: str | None,
) -> str:
    """Bind an output event to the single paid request without assuming event order."""

    prompt_name, _ = _event_identity(content, event_name)
    if expected_prompt_name is not None and prompt_name != expected_prompt_name:
        raise InputError("Nova completion promptName does not match the persisted request")
    if seen_prompt_name is not None and prompt_name != seen_prompt_name:
        raise InputError(f"Nova {event_name} promptName does not match the rest of the stream")
    return prompt_name


def _validate_output_configuration(content: dict[str, Any], content_type: str) -> None:
    if content_type == "AUDIO":
        if "audioOutputConfiguration" not in content:
            return
        configuration = content["audioOutputConfiguration"]
        expected_fields = {
            "mediaType",
            "sampleRateHertz",
            "sampleSizeBits",
            "encoding",
            "channelCount",
        }
        if not isinstance(configuration, dict) or set(configuration) != expected_fields:
            raise InputError("Nova audio contentStart has a malformed output configuration")
        if (
            configuration.get("mediaType") != "audio/lpcm"
            or type(configuration.get("sampleRateHertz")) is not int
            or configuration["sampleRateHertz"] != 24000
            or type(configuration.get("sampleSizeBits")) is not int
            or configuration["sampleSizeBits"] != 16
            or configuration.get("encoding") != "base64"
            or type(configuration.get("channelCount")) is not int
            or configuration["channelCount"] != 1
        ):
            raise InputError("Nova audio output configuration is not 24 kHz, signed 16-bit, mono LPCM")
        return

    if content_type == "TEXT":
        if "textOutputConfiguration" not in content:
            return
        configuration = content["textOutputConfiguration"]
        if configuration != {"mediaType": "text/plain"}:
            raise InputError("Nova text contentStart has a malformed output configuration")
        return

    raise InputError(f"Nova contentStart has unsupported type {content_type!r}")


def _event_name_summary(events: list[Any], limit: int = 40) -> str:
    names: list[str] = []
    for event in events[:limit]:
        if isinstance(event, dict) and len(event) == 1:
            names.append(str(next(iter(event))))
        else:
            names.append("<malformed>")
    remaining = len(events) - limit
    suffix = f", ... (+{remaining} more)" if remaining > 0 else ""
    return f" (observed Nova output events: {', '.join(names) or 'none'}{suffix})"


def replay_output_events(
    events: Any,
    *,
    expected_prompt_name: str | None = None,
) -> NovaRenderResult:
    """Validate and replay persisted Nova OUTPUT events without SDK access."""

    event_list = list(events)
    stored_events: list[dict[str, Any]] = []
    seen_prompt_name: str | None = None
    contexts: dict[str, tuple[str, str, str]] = {}
    open_content: set[str] = set()
    final_parts: list[str] = []
    audio_parts: list[bytes] = []
    final_turn_completed = False
    audio_turn_completed = False
    completed = False
    stop_reason = ""

    for index, event in enumerate(event_list):
        if not isinstance(event, dict) or len(event) != 1:
            raise InputError(f"Nova output event {index + 1} must contain exactly one event type")
        stored_events.append(event)
        event_name, content = next(iter(event.items()))
        if not isinstance(content, dict):
            raise InputError(f"Nova {event_name} payload is malformed")
        completed = False

        if event_name not in {
            "completionStart",
            "usageEvent",
            "contentStart",
            "textOutput",
            "audioOutput",
            "contentEnd",
            "completionEnd",
        }:
            raise InputError(
                f"Nova output contains unsupported event type {event_name!r}"
                + _event_name_summary(event_list)
            )

        seen_prompt_name = _bind_prompt_name(
            content,
            event_name,
            expected_prompt_name,
            seen_prompt_name,
        )

        if event_name in {"completionStart", "usageEvent"}:
            continue

        if event_name == "contentStart":
            content_id = _content_id(content, event_name)
            if content_id in contexts:
                raise InputError(f"Nova reused output contentId {content_id!r}")
            role = content.get("role")
            content_type = content.get("type")
            if (
                not isinstance(content_type, str)
                or (content_type == "AUDIO" and role != "ASSISTANT")
                or (content_type == "TEXT" and role not in {"USER", "ASSISTANT"})
            ):
                raise InputError("Nova contentStart has an invalid role or type")
            _validate_output_configuration(content, content_type)
            stage = ""
            additional = content.get("additionalModelFields")
            if additional is not None:
                if not isinstance(additional, str):
                    raise InputError("Nova contentStart additionalModelFields is not JSON text")
                additional_value = json_loads_strict(additional, "Nova contentStart additionalModelFields")
                if not isinstance(additional_value, dict):
                    raise InputError("Nova contentStart additionalModelFields is not an object")
                stage_value = additional_value.get("generationStage", "")
                if not isinstance(stage_value, str):
                    raise InputError("Nova contentStart generationStage is not text")
                stage = stage_value
            contexts[content_id] = (role, stage, content_type)
            open_content.add(content_id)
            continue

        if event_name in {"textOutput", "audioOutput", "contentEnd"}:
            content_id = _content_id(content, event_name)
            context = contexts.get(content_id)
            if context is None or content_id not in open_content:
                raise InputError(f"Nova {event_name} references unopened contentId {content_id!r}")

            if event_name == "textOutput":
                if context[2] != "TEXT":
                    raise InputError(f"Nova textOutput references non-TEXT contentId {content_id!r}")
                value = content.get("content")
                if not isinstance(value, str):
                    raise InputError("Nova textOutput content is not text")
                if context == ("ASSISTANT", "FINAL", "TEXT"):
                    final_parts.append(value)
                continue

            if event_name == "audioOutput":
                if context[0] != "ASSISTANT" or context[2] != "AUDIO":
                    raise InputError(f"Nova audioOutput references unexpected contentId {content_id!r}")
                encoded_audio = content.get("content")
                if not isinstance(encoded_audio, str):
                    raise InputError("Nova audioOutput content is not base64 text")
                try:
                    audio_parts.append(base64.b64decode(encoded_audio, validate=True))
                except (ValueError, TypeError) as exc:
                    raise InputError("Nova returned invalid base64 audio") from exc
                continue

            content_type = content.get("type")
            if content_type != context[2]:
                raise InputError(f"Nova contentEnd type does not match contentId {content_id!r}")
            content_stop_reason = content.get("stopReason")
            allowed_reasons = (
                {"END_TURN", "PARTIAL_TURN"}
                if content_type == "AUDIO"
                else {"END_TURN", "PARTIAL_TURN", "INTERRUPTED"}
            )
            if content_stop_reason not in allowed_reasons:
                raise InputError(f"Nova contentEnd has an invalid stop reason for {content_id!r}")
            if context[2] == "AUDIO" and content_stop_reason == "END_TURN":
                audio_turn_completed = True
            if context == ("ASSISTANT", "FINAL", "TEXT"):
                if content_stop_reason == "INTERRUPTED":
                    raise InputError(f"Nova accepted output content was interrupted for {content_id!r}")
                if content_stop_reason == "END_TURN":
                    final_turn_completed = True
            open_content.remove(content_id)
            continue

        if open_content:
            raise InputError(f"Nova completionEnd arrived before contentEnd for {sorted(open_content)}")
        stop_reason_value = content.get("stopReason")
        if not isinstance(stop_reason_value, str):
            raise InputError("Nova completionEnd has no valid stopReason")
        stop_reason = stop_reason_value
        completed = True

    transcript = "".join(final_parts)
    audio = b"".join(audio_parts)
    if seen_prompt_name is None:
        raise InputError("Nova output contained no events" + _event_name_summary(event_list))
    if not completed:
        raise InputError(
            "Nova output does not end with completionEnd" + _event_name_summary(event_list)
        )
    if stop_reason != "END_TURN":
        raise InputError(f"Nova stream did not complete with END_TURN (stop reason {stop_reason!r})")
    if not final_turn_completed:
        raise InputError("Nova returned no complete ASSISTANT FINAL transcript turn")
    if not transcript.strip():
        raise InputError("Nova returned no ASSISTANT FINAL transcript")
    if not audio_turn_completed:
        raise InputError("Nova returned no complete ASSISTANT audio turn")
    if not audio or len(audio) % 2:
        raise InputError("Nova returned empty or malformed 16-bit LPCM audio")
    return NovaRenderResult(audio, transcript, tuple(stored_events), stop_reason)


async def _receive_events(
    stream: Any,
    model_types: dict[str, Any],
    expected_prompt_name: str | None = None,
    final_text_ended: asyncio.Future[None] | None = None,
    input_protocol_ended: asyncio.Event | None = None,
) -> NovaRenderResult:
    if (final_text_ended is None) != (input_protocol_ended is None):
        raise InputError("Nova receiver turn-boundary signals are incomplete")

    _, output_stream = await stream.await_output()
    if output_stream is None:
        raise InputError("Nova returned no output stream")

    events: list[dict[str, Any]] = []
    final_text_content_ids: set[str] = set()
    async for output in output_stream:
        if isinstance(output, model_types["chunk"]):
            payload = output.value.bytes_
            if not payload:
                continue
            try:
                decoded = payload.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise InputError(f"Nova returned malformed event JSON: {exc}") from exc
            document = json_loads_strict(decoded, "Nova output event")
            if not isinstance(document, dict) or set(document) != {"event"}:
                raise InputError("Nova output chunk must contain exactly one event object")
            event = document["event"]
            if not isinstance(event, dict):
                raise InputError("Nova output chunk does not contain an event object")
            events.append(event)

            if final_text_ended is not None and len(event) == 1:
                event_name, content = next(iter(event.items()))
                if isinstance(content, dict) and event_name == "contentStart":
                    if content.get("role") == "ASSISTANT" and content.get("type") == "TEXT":
                        additional = content.get("additionalModelFields")
                        if additional is not None:
                            if not isinstance(additional, str):
                                raise InputError(
                                    "Nova contentStart additionalModelFields is not JSON text"
                                )
                            additional_value = json_loads_strict(
                                additional,
                                "Nova contentStart additionalModelFields",
                            )
                            if not isinstance(additional_value, dict):
                                raise InputError(
                                    "Nova contentStart additionalModelFields is not an object"
                                )
                            if additional_value.get("generationStage") == "FINAL":
                                final_text_content_ids.add(_content_id(content, event_name))
                elif isinstance(content, dict) and event_name == "contentEnd":
                    content_id = content.get("contentId")
                    if content_id in final_text_content_ids:
                        if content.get("type") != "TEXT":
                            raise InputError("Nova ASSISTANT FINAL contentEnd is not TEXT")
                        content_stop_reason = content.get("stopReason")
                        if content_stop_reason not in {"END_TURN", "PARTIAL_TURN"}:
                            raise InputError(
                                "Nova ASSISTANT FINAL text has an invalid stop reason"
                            )
                        final_text_content_ids.remove(content_id)
                        if content_stop_reason == "END_TURN":
                            if not final_text_ended.done():
                                final_text_ended.set_result(None)
                            assert input_protocol_ended is not None
                            await input_protocol_ended.wait()

            if "completionEnd" in event and (
                final_text_ended is None or final_text_ended.done()
            ):
                break
        elif isinstance(output, model_types["errors"]):
            message = getattr(getattr(output, "value", None), "message", None)
            raise InputError(f"Nova stream error: {message or type(output).__name__}")
        elif isinstance(output, model_types["unknown"]):
            raise InputError(f"Unknown Nova stream event: {getattr(output, 'tag', type(output).__name__)}")
        else:
            raise InputError(f"Unexpected Nova stream event: {type(output).__name__}")

    return replay_output_events(events, expected_prompt_name=expected_prompt_name)


_CLEANUP_TIMEOUT_SECONDS = 1.0


def _consume_task_result(task: asyncio.Future[Any]) -> None:
    if task.cancelled():
        return
    try:
        task.exception()
    except BaseException:
        pass


async def _bounded_cleanup(label: str, awaitable: Any) -> str | None:
    task = asyncio.ensure_future(awaitable)
    done, _ = await asyncio.wait({task}, timeout=_CLEANUP_TIMEOUT_SECONDS)
    if not done:
        task.cancel()
        task.add_done_callback(_consume_task_result)
        return f"{label} exceeded {_CLEANUP_TIMEOUT_SECONDS:g}s"
    try:
        task.result()
    except BaseException as exc:
        return f"{label} failed with {type(exc).__name__}: {exc}"
    return None


async def _bounded_receiver_stop(receiver: asyncio.Task[Any]) -> str | None:
    if not receiver.done():
        receiver.cancel()
        done, _ = await asyncio.wait({receiver}, timeout=_CLEANUP_TIMEOUT_SECONDS)
        if not done:
            receiver.cancel()
            receiver.add_done_callback(_consume_task_result)
            return f"receiver cancellation exceeded {_CLEANUP_TIMEOUT_SECONDS:g}s"
    try:
        receiver.result()
    except asyncio.CancelledError:
        return None
    except BaseException as exc:
        return f"receiver finished with {type(exc).__name__}: {exc}"
    return None


_AUDIO_INPUT_SAMPLE_RATE_HZ = 16_000
_AUDIO_INPUT_SAMPLE_SIZE_BITS = 16
_AUDIO_INPUT_CHANNELS = 1
_AUDIO_INPUT_FRAME_DURATION_SECONDS = 0.032
_AUDIO_INPUT_FRAME_BYTES = int(
    _AUDIO_INPUT_SAMPLE_RATE_HZ
    * _AUDIO_INPUT_FRAME_DURATION_SECONDS
    * (_AUDIO_INPUT_SAMPLE_SIZE_BITS // 8)
    * _AUDIO_INPUT_CHANNELS
)
_SILENT_AUDIO_INPUT = base64.b64encode(bytes(_AUDIO_INPUT_FRAME_BYTES)).decode("ascii")


async def _invoke_session(
    text: str,
    voice_id: str,
    settings: NovaSettings,
    prompt_name: str,
    sdk: dict[str, Any],
    model_types: dict[str, Any],
) -> NovaRenderResult:
    config = await sdk["config"].resolve(
        region=settings.region,
        transport=sdk["transport"](),
    )
    client: Any = sdk["client"](config=config)
    stream: Any = None
    receiver: asyncio.Task[NovaRenderResult] | None = None
    result: NovaRenderResult | None = None
    stream_entered = False
    primary_error: BaseException | None = None
    cleanup_errors: list[str] = []

    try:
        stream = await client.invoke_model_with_bidirectional_stream(
            sdk["operation_input"](model_id=settings.model_id)
        )
        await stream.__aenter__()
        stream_entered = True

        system_name = str(uuid.uuid4())
        audio_name = str(uuid.uuid4())
        user_name = str(uuid.uuid4())

        async def send(event: dict[str, Any]) -> None:
            await _send_event(stream, event, sdk["input_chunk"], sdk["payload"])

        audio_input = {
            "audioInput": {
                "promptName": prompt_name,
                "contentName": audio_name,
                "content": _SILENT_AUDIO_INPUT,
            }
        }

        final_text_ended: asyncio.Future[None] = asyncio.get_running_loop().create_future()
        input_protocol_ended = asyncio.Event()
        receiver = asyncio.create_task(
            _receive_events(
                stream,
                model_types,
                prompt_name,
                final_text_ended,
                input_protocol_ended,
            )
        )
        await send(
            {
                "sessionStart": {
                    "inferenceConfiguration": {
                        "maxTokens": settings.max_tokens,
                        "topP": settings.top_p,
                        "temperature": settings.temperature,
                    }
                }
            }
        )
        await send(
            {
                "promptStart": {
                    "promptName": prompt_name,
                    "textOutputConfiguration": {"mediaType": "text/plain"},
                    "audioOutputConfiguration": {
                        "mediaType": "audio/lpcm",
                        "sampleRateHertz": settings.sample_rate_hz,
                        "sampleSizeBits": settings.sample_size_bits,
                        "channelCount": settings.channels,
                        "voiceId": voice_id,
                        "encoding": "base64",
                        "audioType": "SPEECH",
                    },
                }
            }
        )
        await send(
            {
                "contentStart": {
                    "promptName": prompt_name,
                    "contentName": system_name,
                    "type": "TEXT",
                    "interactive": False,
                    "role": "SYSTEM",
                    "textInputConfiguration": {"mediaType": "text/plain"},
                }
            }
        )
        await send(
            {
                "textInput": {
                    "promptName": prompt_name,
                    "contentName": system_name,
                    "content": settings.system_prompt,
                }
            }
        )
        await send({"contentEnd": {"promptName": prompt_name, "contentName": system_name}})
        await send(
            {
                "contentStart": {
                    "promptName": prompt_name,
                    "contentName": audio_name,
                    "type": "AUDIO",
                    "interactive": True,
                    "role": "USER",
                    "audioInputConfiguration": {
                        "mediaType": "audio/lpcm",
                        "sampleRateHertz": _AUDIO_INPUT_SAMPLE_RATE_HZ,
                        "sampleSizeBits": _AUDIO_INPUT_SAMPLE_SIZE_BITS,
                        "channelCount": _AUDIO_INPUT_CHANNELS,
                        "audioType": "SPEECH",
                        "encoding": "base64",
                    },
                }
            }
        )
        await send(audio_input)
        await send(
            {
                "contentStart": {
                    "promptName": prompt_name,
                    "contentName": user_name,
                    "type": "TEXT",
                    "interactive": True,
                    "role": "USER",
                    "textInputConfiguration": {"mediaType": "text/plain"},
                }
            }
        )
        await send(
            {
                "textInput": {
                    "promptName": prompt_name,
                    "contentName": user_name,
                    "content": text,
                }
            }
        )
        await send({"contentEnd": {"promptName": prompt_name, "contentName": user_name}})

        while not final_text_ended.done():
            done, _ = await asyncio.wait(
                {receiver, final_text_ended},
                timeout=_AUDIO_INPUT_FRAME_DURATION_SECONDS,
            )
            if receiver in done:
                receiver.result()
                raise InputError(
                    "Nova output completed before ASSISTANT FINAL text contentEnd"
                )
            if not final_text_ended.done():
                await send(audio_input)

        await send({"contentEnd": {"promptName": prompt_name, "contentName": audio_name}})
        await send({"promptEnd": {"promptName": prompt_name}})
        await send({"sessionEnd": {}})
        input_protocol_ended.set()
        result = await receiver
    except BaseException as exc:
        primary_error = exc
    finally:
        if receiver is not None:
            receiver_error = await _bounded_receiver_stop(receiver)
            if receiver_error:
                cleanup_errors.append(receiver_error)
        if stream is not None:
            close_error = await _bounded_cleanup("input stream close", stream.input_stream.close())
            if close_error:
                cleanup_errors.append(close_error)
        exit_args = (
            type(primary_error) if primary_error is not None else None,
            primary_error,
            primary_error.__traceback__ if primary_error is not None else None,
        )
        if stream_entered:
            stream_error = await _bounded_cleanup("stream __aexit__", stream.__aexit__(*exit_args))
            if stream_error:
                cleanup_errors.append(stream_error)

    if primary_error is not None:
        raise primary_error.with_traceback(primary_error.__traceback__)
    if cleanup_errors:
        raise InputError("Nova cleanup did not finish safely: " + "; ".join(cleanup_errors))
    if result is None:
        raise InputError("Nova session ended without a render result")
    return result


async def _render_async(
    text: str,
    voice_id: str,
    settings: NovaSettings,
    prompt_name: str,
) -> NovaRenderResult:
    if os.environ.get("FRONTIER_AUDIOBOOK_DISABLE_AWS") == "1":
        raise InputError("AWS invocation is disabled by FRONTIER_AUDIOBOOK_DISABLE_AWS")
    try:
        from smithy_http.aio.crt import AWSCRTHTTPClient, AWSCRTHTTPClientConfig
        from aws_sdk_bedrock_runtime.client import AsyncBedrockRuntimeClient
        from aws_sdk_bedrock_runtime.config import AsyncBedrockRuntimeConfig
        from aws_sdk_bedrock_runtime.models import (
            BidirectionalInputPayloadPart,
            InvokeModelWithBidirectionalStreamInputChunk,
            InvokeModelWithBidirectionalStreamOperationInput,
            InvokeModelWithBidirectionalStreamOutputChunk,
            InvokeModelWithBidirectionalStreamOutputInternalServerException,
            InvokeModelWithBidirectionalStreamOutputModelStreamErrorException,
            InvokeModelWithBidirectionalStreamOutputModelTimeoutException,
            InvokeModelWithBidirectionalStreamOutputServiceUnavailableException,
            InvokeModelWithBidirectionalStreamOutputThrottlingException,
            InvokeModelWithBidirectionalStreamOutputUnknown,
            InvokeModelWithBidirectionalStreamOutputValidationException,
        )
    except ImportError as exc:
        raise InputError(
            "The pinned Nova runtime is not installed. Run `uv sync --python 3.12 --no-editable` in .audiobook/."
        ) from exc

    sdk = {
        "transport": lambda: AWSCRTHTTPClient(
            client_config=AWSCRTHTTPClientConfig(force_http_2=True)
        ),
        "client": AsyncBedrockRuntimeClient,
        "config": AsyncBedrockRuntimeConfig,
        "payload": BidirectionalInputPayloadPart,
        "input_chunk": InvokeModelWithBidirectionalStreamInputChunk,
        "operation_input": InvokeModelWithBidirectionalStreamOperationInput,
    }
    model_types = {
        "chunk": InvokeModelWithBidirectionalStreamOutputChunk,
        "errors": (
            InvokeModelWithBidirectionalStreamOutputInternalServerException,
            InvokeModelWithBidirectionalStreamOutputModelStreamErrorException,
            InvokeModelWithBidirectionalStreamOutputModelTimeoutException,
            InvokeModelWithBidirectionalStreamOutputServiceUnavailableException,
            InvokeModelWithBidirectionalStreamOutputThrottlingException,
            InvokeModelWithBidirectionalStreamOutputValidationException,
        ),
        "unknown": InvokeModelWithBidirectionalStreamOutputUnknown,
    }
    try:
        return await asyncio.wait_for(
            _invoke_session(text, voice_id, settings, prompt_name, sdk, model_types),
            timeout=settings.stream_timeout_seconds,
        )
    except TimeoutError as exc:
        raise InputError(
            f"Nova session did not complete within {settings.stream_timeout_seconds} seconds"
        ) from exc


_PROCESS_CLEANUP_GRACE_SECONDS = 6.0
_PROCESS_TERMINATE_GRACE_SECONDS = 1.0


def _render_process_worker(
    connection: Any,
    text: str,
    voice_id: str,
    settings: NovaSettings,
    prompt_name: str,
) -> None:
    try:
        result = asyncio.run(_render_async(text, voice_id, settings, prompt_name))
        connection.send(("result", result))
    except InputError as exc:
        connection.send(("input_error", str(exc)))
    except BaseException as exc:
        connection.send(("error", type(exc).__name__, str(exc)))
    finally:
        connection.close()


def _terminate_process(process: Any) -> None:
    if not process.is_alive():
        process.join(timeout=0)
        return
    process.terminate()
    process.join(timeout=_PROCESS_TERMINATE_GRACE_SECONDS)
    if process.is_alive():
        process.kill()
        process.join(timeout=_PROCESS_TERMINATE_GRACE_SECONDS)


def _run_worker_process(
    worker: Any,
    worker_args: tuple[Any, ...],
    hard_timeout_seconds: float,
    timeout_message: str,
) -> Any:
    """Run cancellation-sensitive SDK work behind a killable process boundary."""

    context = multiprocessing.get_context("spawn")
    receiver, sender = context.Pipe(duplex=False)
    process = context.Process(target=worker, args=(sender, *worker_args), daemon=True)
    try:
        process.start()
        sender.close()
        deadline = time.monotonic() + hard_timeout_seconds
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                _terminate_process(process)
                raise InputError(timeout_message)
            if receiver.poll(min(0.1, remaining)):
                try:
                    payload = receiver.recv()
                except EOFError as exc:
                    raise InputError("Nova worker exited without a result") from exc
                process.join(timeout=_PROCESS_TERMINATE_GRACE_SECONDS)
                if process.is_alive():
                    _terminate_process(process)
                if not isinstance(payload, tuple) or not payload:
                    raise InputError("Nova worker returned a malformed result")
                if payload[0] == "result" and len(payload) == 2:
                    return payload[1]
                if payload[0] == "input_error" and len(payload) == 2:
                    raise InputError(str(payload[1]))
                if payload[0] == "error" and len(payload) == 3:
                    raise InputError(f"Nova invocation failed: {payload[1]}: {payload[2]}")
                raise InputError("Nova worker returned an unknown result type")
            if not process.is_alive():
                raise InputError(
                    f"Nova worker exited without a result (exit code {process.exitcode})"
                )
    finally:
        sender.close()
        receiver.close()
        if process.is_alive():
            _terminate_process(process)


def render_text(
    text: str,
    voice_id: str,
    settings: NovaSettings,
    *,
    prompt_name: str | None = None,
    paid_render_authorized: bool = False,
) -> NovaRenderResult:
    if not paid_render_authorized:
        raise InputError("Refusing billable Nova invocation without explicit paid-render authorization")
    if os.name != "posix" or os.uname().sysname not in {"Darwin", "Linux"}:
        raise InputError("Paid Nova rendering is supported only on macOS and Linux")
    if not text.strip():
        raise InputError("Refusing to invoke Nova with empty audition text")
    selected_prompt_name = prompt_name or str(uuid.uuid4())
    try:
        if str(uuid.UUID(selected_prompt_name)) != selected_prompt_name:
            raise ValueError
    except (ValueError, AttributeError) as exc:
        raise InputError("Nova prompt_name must be a canonical UUID") from exc

    hard_timeout = settings.stream_timeout_seconds + _PROCESS_CLEANUP_GRACE_SECONDS
    result = _run_worker_process(
        _render_process_worker,
        (text, voice_id, settings, selected_prompt_name),
        hard_timeout,
        f"Nova worker exceeded the {settings.stream_timeout_seconds}-second session timeout "
        "and bounded cleanup grace",
    )
    if not isinstance(result, NovaRenderResult):
        raise InputError("Nova worker returned an invalid render result")
    return result


@dataclass(frozen=True)
class _SequenceOutputFailure:
    error: BaseException


_SEQUENCE_OUTPUT_EOF = object()
_SEQUENCE_EVENT_TYPES = {
    "completionStart",
    "usageEvent",
    "contentStart",
    "textOutput",
    "audioOutput",
    "contentEnd",
    "completionEnd",
}
_SEQUENCE_OUTPUT_QUEUE_LIMIT = 512
_SEQUENCE_MAX_EVENT_BYTES = 1_048_576
_SEQUENCE_MAX_TURN_EVENTS = 4096
_SEQUENCE_MAX_TURN_BYTES = 16 * 1_048_576
_SEQUENCE_MAX_AUDIO_LATENESS_SECONDS = 0.5
_SEQUENCE_AUDIO_PREROLL_SECONDS = 0.1
_SEQUENCE_SEND_TIMEOUT_SECONDS = 2.0
_SEQUENCE_ESTABLISH_TIMEOUT_SECONDS = 10.0
_SEQUENCE_OUTPUT_READY_TIMEOUT_SECONDS = 10.0
_SEQUENCE_FIRST_OUTPUT_TIMEOUT_SECONDS = 30.0
_SEQUENCE_INTER_EVENT_TIMEOUT_SECONDS = 30.0
_SEQUENCE_MAX_SESSION_SECONDS = 120.0


class NovaSequenceIncomplete(InputError):
    """A sequence failed after one or more independently validated paid turns."""

    def __init__(
        self,
        message: str,
        completed_results: tuple[NovaRenderResult, ...],
    ) -> None:
        super().__init__(message)
        self.completed_results = completed_results


@dataclass(frozen=True)
class _SequenceWorkerOutcome:
    results: tuple[NovaRenderResult, ...]
    error: str | None = None


async def _queue_sequence_output_events(
    stream: Any,
    model_types: dict[str, Any],
    output_queue: asyncio.Queue[Any],
) -> None:
    """Read one persistent output stream and preserve its event ordering."""

    try:
        try:
            _, output_stream = await asyncio.wait_for(
                stream.await_output(),
                timeout=_SEQUENCE_OUTPUT_READY_TIMEOUT_SECONDS,
            )
        except TimeoutError as exc:
            raise InputError(
                "Nova output stream was not ready within "
                f"{_SEQUENCE_OUTPUT_READY_TIMEOUT_SECONDS:g} seconds"
            ) from exc
        if output_stream is None:
            raise InputError("Nova returned no output stream")

        async for output in output_stream:
            if isinstance(output, model_types["chunk"]):
                payload = output.value.bytes_
                if not payload:
                    continue
                if not isinstance(payload, bytes) or len(payload) > _SEQUENCE_MAX_EVENT_BYTES:
                    raise InputError("Nova returned an oversized or malformed event payload")
                try:
                    decoded = payload.decode("utf-8")
                except UnicodeDecodeError as exc:
                    raise InputError(f"Nova returned malformed event JSON: {exc}") from exc
                document = json_loads_strict(decoded, "Nova output event")
                if not isinstance(document, dict) or set(document) != {"event"}:
                    raise InputError("Nova output chunk must contain exactly one event object")
                event = document["event"]
                if not isinstance(event, dict):
                    raise InputError("Nova output chunk does not contain an event object")
                await output_queue.put(event)
            elif isinstance(output, model_types["errors"]):
                message = getattr(getattr(output, "value", None), "message", None)
                raise InputError(f"Nova stream error: {message or type(output).__name__}")
            elif isinstance(output, model_types["unknown"]):
                raise InputError(
                    f"Unknown Nova stream event: {getattr(output, 'tag', type(output).__name__)}"
                )
            else:
                raise InputError(f"Unexpected Nova stream event: {type(output).__name__}")
    except asyncio.CancelledError:
        raise
    except BaseException as exc:
        await output_queue.put(_SequenceOutputFailure(exc))
        raise
    else:
        await output_queue.put(_SEQUENCE_OUTPUT_EOF)


async def _pump_sequence_audio(
    send_audio: Any,
    stop: asyncio.Event,
    output_queue: asyncio.Queue[Any],
) -> None:
    """Maintain Nova's required real-time continuous audio stream with silence."""

    loop = asyncio.get_running_loop()
    deadline = loop.time() + _AUDIO_INPUT_FRAME_DURATION_SECONDS
    try:
        while not stop.is_set():
            remaining = deadline - loop.time()
            if remaining > 0:
                try:
                    await asyncio.wait_for(stop.wait(), timeout=remaining)
                    return
                except TimeoutError:
                    pass
            if stop.is_set():
                return
            await send_audio()
            lateness = loop.time() - deadline
            if lateness > _SEQUENCE_MAX_AUDIO_LATENESS_SECONDS:
                raise InputError(
                    f"Nova continuous audio cadence slipped by {lateness:.3f} seconds"
                )
            deadline += _AUDIO_INPUT_FRAME_DURATION_SECONDS
    except asyncio.CancelledError:
        raise
    except BaseException as exc:
        await output_queue.put(_SequenceOutputFailure(exc))
        raise


def _validate_sequence_turn_identities(
    events: tuple[dict[str, Any], ...],
    expected_prompt_name: str,
    identity_state: dict[str, Any],
) -> None:
    """Prevent output identifiers from leaking across serialized text turns."""

    local_session_id: str | None = None
    local_completion_ids: set[str] = set()
    local_content_ids: set[str] = set()
    content_identities: dict[str, tuple[str | None, str, str]] = {}

    for event in events:
        event_name, content = next(iter(event.items()))
        prompt_name, completion_id = _event_identity(content, event_name)
        if prompt_name != expected_prompt_name:
            raise InputError("Nova completion promptName does not match the persisted sequence request")
        local_completion_ids.add(completion_id)

        session_id = content.get("sessionId")
        if session_id is not None:
            if local_session_id is not None and session_id != local_session_id:
                raise InputError("Nova changed sessionId within a sequence turn")
            local_session_id = session_id

        if event_name == "contentStart":
            content_id = _content_id(content, event_name)
            local_content_ids.add(content_id)
            content_identities[content_id] = (session_id, prompt_name, completion_id)
        elif event_name in {"textOutput", "audioOutput", "contentEnd"}:
            content_id = _content_id(content, event_name)
            start_identity = content_identities.get(content_id)
            if start_identity is None:
                raise InputError(f"Nova {event_name} has no matching contentStart")
            start_session_id, start_prompt_name, start_completion_id = start_identity
            if prompt_name != start_prompt_name or completion_id != start_completion_id:
                raise InputError(f"Nova {event_name} identity does not match contentStart")
            if (
                start_session_id is not None
                and session_id is not None
                and session_id != start_session_id
            ):
                raise InputError(f"Nova {event_name} sessionId does not match contentStart")

    if len(local_completion_ids) != 1:
        raise InputError("Nova sequence turn did not contain exactly one completionId")
    previous_session_id = identity_state["session_id"]
    if (
        previous_session_id is not None
        and local_session_id is not None
        and local_session_id != previous_session_id
    ):
        raise InputError("Nova changed sessionId between sequence turns")
    if identity_state["completion_ids"] & local_completion_ids:
        raise InputError("Nova reused a completionId across sequence turns")
    if identity_state["content_ids"] & local_content_ids:
        raise InputError("Nova reused an output contentId across sequence turns")

    if previous_session_id is None and local_session_id is not None:
        identity_state["session_id"] = local_session_id
    identity_state["completion_ids"].update(local_completion_ids)
    identity_state["content_ids"].update(local_content_ids)


async def _receive_sequence_turn(
    output_queue: asyncio.Queue[Any],
    expected_prompt_name: str,
    identity_state: dict[str, Any],
    turn_index: int,
    output_reader: asyncio.Task[Any],
    audio_pump: asyncio.Task[Any],
) -> NovaRenderResult:
    """Freeze one completion lifecycle before another input turn is sent."""

    events: list[dict[str, Any]] = []
    completion_id: str | None = None
    completion_started = False
    event_bytes = 0

    while True:
        timeout_seconds = (
            _SEQUENCE_FIRST_OUTPUT_TIMEOUT_SECONDS
            if not events
            else _SEQUENCE_INTER_EVENT_TIMEOUT_SECONDS
        )
        try:
            item = await asyncio.wait_for(
                output_queue.get(),
                timeout=timeout_seconds,
            )
        except TimeoutError as exc:
            _require_sequence_task_running(output_reader, "output reader")
            _require_sequence_task_running(audio_pump, "audio pump")
            phase = "first output event" if not events else "next output event"
            last_event = next(iter(events[-1])) if events else "none"
            raise InputError(
                f"Nova sequence turn {turn_index} received no {phase} for "
                f"{timeout_seconds:g} seconds "
                f"(last event: {last_event}; output reader: running; "
                "audio pump: running)"
            ) from exc
        if isinstance(item, _SequenceOutputFailure):
            raise item.error.with_traceback(item.error.__traceback__)
        if item is _SEQUENCE_OUTPUT_EOF:
            raise InputError("Nova output stream ended before the sequence turn completed")
        if not isinstance(item, dict) or len(item) != 1:
            raise InputError("Nova sequence output event must contain exactly one event type")

        event_name, content = next(iter(item.items()))
        if event_name not in _SEQUENCE_EVENT_TYPES:
            raise InputError(f"Nova output contains unsupported event type {event_name!r}")
        if not isinstance(content, dict):
            raise InputError(f"Nova {event_name} payload is malformed")
        prompt_name, event_completion_id = _event_identity(content, event_name)
        if prompt_name != expected_prompt_name:
            raise InputError("Nova completion promptName does not match the persisted sequence request")
        if completion_id is None:
            completion_id = event_completion_id
        elif event_completion_id != completion_id:
            raise InputError("Nova emitted more than one completionId for one sequence turn")

        event_bytes += len(
            json.dumps(
                {"event": item},
                ensure_ascii=False,
                separators=(",", ":"),
            ).encode("utf-8")
        )
        if len(events) >= _SEQUENCE_MAX_TURN_EVENTS or event_bytes > _SEQUENCE_MAX_TURN_BYTES:
            raise InputError("Nova sequence turn exceeded the guarded output event budget")
        events.append(item)

        if event_name == "completionStart":
            if completion_started:
                raise InputError("Nova emitted duplicate completionStart for one sequence turn")
            completion_started = True
            continue
        if event_name in {"contentStart", "textOutput", "audioOutput", "contentEnd"}:
            if not completion_started:
                raise InputError(f"Nova {event_name} arrived before completionStart")
            continue
        if event_name != "completionEnd":
            continue
        if not completion_started:
            raise InputError("Nova completionEnd arrived before completionStart")

        result = replay_output_events(events, expected_prompt_name=expected_prompt_name)
        _validate_sequence_turn_identities(result.events, expected_prompt_name, identity_state)
        return result


def _require_sequence_task_running(task: asyncio.Task[Any], label: str) -> None:
    if not task.done():
        return
    try:
        task.result()
    except asyncio.CancelledError as exc:
        raise InputError(f"Nova {label} was cancelled before sequence shutdown") from exc
    except BaseException as exc:
        raise exc.with_traceback(exc.__traceback__)
    raise InputError(f"Nova {label} ended before sequence shutdown")


def _assert_no_queued_sequence_output(output_queue: asyncio.Queue[Any]) -> None:
    if output_queue.empty():
        return
    item = output_queue.get_nowait()
    if isinstance(item, _SequenceOutputFailure):
        raise item.error.with_traceback(item.error.__traceback__)
    if item is _SEQUENCE_OUTPUT_EOF:
        raise InputError("Nova output stream ended before sequence shutdown")
    raise InputError("Nova emitted output after the terminal completionEnd boundary")


def _mid_sentence_partial_turn_count(events: tuple[dict[str, Any], ...]) -> int:
    """Count audio PARTIAL_TURN boundaries not proven to follow sentence punctuation."""

    contexts: dict[str, tuple[str, str, int]] = {}
    text_parts: dict[str, list[str]] = {}
    partial_audio_starts: list[int] = []
    for index, event in enumerate(events):
        if "contentStart" in event:
            content = event["contentStart"]
            content_id = _content_id(content, "contentStart")
            additional = content.get("additionalModelFields")
            stage = ""
            if isinstance(additional, str):
                decoded = json_loads_strict(
                    additional,
                    "Nova contentStart additionalModelFields",
                )
                if isinstance(decoded, dict) and isinstance(decoded.get("generationStage"), str):
                    stage = decoded["generationStage"]
            contexts[content_id] = (str(content.get("type", "")), stage, index)
            text_parts[content_id] = []
        elif "textOutput" in event:
            content = event["textOutput"]
            text_parts[_content_id(content, "textOutput")].append(str(content.get("content", "")))
        elif "contentEnd" in event:
            content = event["contentEnd"]
            if content.get("type") == "AUDIO" and content.get("stopReason") == "PARTIAL_TURN":
                partial_audio_starts.append(contexts[_content_id(content, "contentEnd")][2])

    unsafe = 0
    trailing_closers = '\"\u201d\u2019\' )]'
    for audio_start in partial_audio_starts:
        preceding = [
            (start, "".join(text_parts[content_id]))
            for content_id, (content_type, stage, start) in contexts.items()
            if content_type == "TEXT" and stage == "SPECULATIVE" and start < audio_start
        ]
        speculative = max(preceding, default=(-1, ""))[1].rstrip()
        while speculative and speculative[-1] in trailing_closers:
            speculative = speculative[:-1].rstrip()
        if not speculative or speculative[-1] not in ".!?":
            unsafe += 1
    return unsafe


async def _invoke_sequence(
    texts: tuple[str, ...],
    voice_id: str,
    settings: NovaSettings,
    prompt_name: str,
    sdk: dict[str, Any],
    model_types: dict[str, Any],
) -> tuple[NovaRenderResult, ...]:
    """Render ordered cross-modal turns in one prompt with continuous audio input."""

    stream: Any = None
    output_reader: asyncio.Task[None] | None = None
    audio_pump: asyncio.Task[None] | None = None
    stream_entered = False
    primary_error: BaseException | None = None
    cleanup_errors: list[str] = []
    results: tuple[NovaRenderResult, ...] | None = None
    rendered: list[NovaRenderResult] = []

    try:
        try:
            config = await asyncio.wait_for(
                sdk["config"].resolve(
                    region=settings.region,
                    transport=sdk["transport"](),
                ),
                timeout=_SEQUENCE_ESTABLISH_TIMEOUT_SECONDS,
            )
        except TimeoutError as exc:
            raise InputError(
                "Nova sequence configuration resolution exceeded "
                f"{_SEQUENCE_ESTABLISH_TIMEOUT_SECONDS:g} seconds"
            ) from exc
        client: Any = sdk["client"](config=config)
        try:
            stream = await asyncio.wait_for(
                client.invoke_model_with_bidirectional_stream(
                    sdk["operation_input"](model_id=settings.model_id)
                ),
                timeout=_SEQUENCE_ESTABLISH_TIMEOUT_SECONDS,
            )
        except TimeoutError as exc:
            raise InputError(
                "Nova sequence stream invocation exceeded "
                f"{_SEQUENCE_ESTABLISH_TIMEOUT_SECONDS:g} seconds"
            ) from exc
        try:
            await asyncio.wait_for(
                stream.__aenter__(),
                timeout=_SEQUENCE_ESTABLISH_TIMEOUT_SECONDS,
            )
        except TimeoutError as exc:
            raise InputError(
                "Nova sequence stream entry exceeded "
                f"{_SEQUENCE_ESTABLISH_TIMEOUT_SECONDS:g} seconds"
            ) from exc
        stream_entered = True

        send_lock = asyncio.Lock()
        output_queue: asyncio.Queue[Any] = asyncio.Queue(
            maxsize=_SEQUENCE_OUTPUT_QUEUE_LIMIT
        )
        audio_stop = asyncio.Event()
        system_name = str(uuid.uuid4())
        audio_name = str(uuid.uuid4())

        async def send_many(events: tuple[dict[str, Any], ...]) -> None:
            async with send_lock:
                for event in events:
                    event_name = next(iter(event), "unknown")
                    try:
                        await asyncio.wait_for(
                            _send_event(
                                stream,
                                event,
                                sdk["input_chunk"],
                                sdk["payload"],
                            ),
                            timeout=_SEQUENCE_SEND_TIMEOUT_SECONDS,
                        )
                    except TimeoutError as exc:
                        raise InputError(
                            f"Nova {event_name} input send exceeded "
                            f"{_SEQUENCE_SEND_TIMEOUT_SECONDS:g} seconds"
                        ) from exc

        audio_input = {
            "audioInput": {
                "promptName": prompt_name,
                "contentName": audio_name,
                "content": _SILENT_AUDIO_INPUT,
            }
        }

        async def send_audio() -> None:
            await send_many((audio_input,))

        await send_many(
            (
                {
                    "sessionStart": {
                        "inferenceConfiguration": {
                            "maxTokens": settings.max_tokens,
                            "topP": settings.top_p,
                            "temperature": settings.temperature,
                        }
                    }
                },
                {
                    "promptStart": {
                        "promptName": prompt_name,
                        "textOutputConfiguration": {"mediaType": "text/plain"},
                        "audioOutputConfiguration": {
                            "mediaType": "audio/lpcm",
                            "sampleRateHertz": settings.sample_rate_hz,
                            "sampleSizeBits": settings.sample_size_bits,
                            "channelCount": settings.channels,
                            "voiceId": voice_id,
                            "encoding": "base64",
                            "audioType": "SPEECH",
                        },
                    }
                },
                {
                    "contentStart": {
                        "promptName": prompt_name,
                        "contentName": system_name,
                        "type": "TEXT",
                        "interactive": False,
                        "role": "SYSTEM",
                        "textInputConfiguration": {"mediaType": "text/plain"},
                    }
                },
                {
                    "textInput": {
                        "promptName": prompt_name,
                        "contentName": system_name,
                        "content": settings.system_prompt,
                    }
                },
                {"contentEnd": {"promptName": prompt_name, "contentName": system_name}},
            )
        )
        # Match AWS's cross-modal sample: complete setup before awaiting output,
        # then establish continuous audio before sending interactive text.
        output_reader = asyncio.create_task(
            _queue_sequence_output_events(stream, model_types, output_queue)
        )
        await send_many(
            (
                {
                    "contentStart": {
                        "promptName": prompt_name,
                        "contentName": audio_name,
                        "type": "AUDIO",
                        "interactive": True,
                        "role": "USER",
                        "audioInputConfiguration": {
                            "mediaType": "audio/lpcm",
                            "sampleRateHertz": _AUDIO_INPUT_SAMPLE_RATE_HZ,
                            "sampleSizeBits": _AUDIO_INPUT_SAMPLE_SIZE_BITS,
                            "channelCount": _AUDIO_INPUT_CHANNELS,
                            "audioType": "SPEECH",
                            "encoding": "base64",
                        },
                    }
                },
                audio_input,
            )
        )
        audio_pump = asyncio.create_task(
            _pump_sequence_audio(send_audio, audio_stop, output_queue)
        )
        await asyncio.sleep(_SEQUENCE_AUDIO_PREROLL_SECONDS)
        _require_sequence_task_running(output_reader, "output reader")
        _require_sequence_task_running(audio_pump, "audio pump")

        from .verify import normalized_tokens

        identity_state: dict[str, Any] = {
            "session_id": None,
            "completion_ids": set(),
            "content_ids": set(),
        }
        for turn_index, text in enumerate(texts, start=1):
            user_name = str(uuid.uuid4())
            await send_many(
                (
                    {
                        "contentStart": {
                            "promptName": prompt_name,
                            "contentName": user_name,
                            "type": "TEXT",
                            "interactive": True,
                            "role": "USER",
                            "textInputConfiguration": {"mediaType": "text/plain"},
                        }
                    },
                    {
                        "textInput": {
                            "promptName": prompt_name,
                            "contentName": user_name,
                            "content": text,
                        }
                    },
                    {"contentEnd": {"promptName": prompt_name, "contentName": user_name}},
                )
            )
            result = await _receive_sequence_turn(
                output_queue,
                prompt_name,
                identity_state,
                turn_index,
                output_reader,
                audio_pump,
            )
            rendered.append(result)
            if normalized_tokens(result.final_transcript) != normalized_tokens(text):
                raise InputError(
                    f"Nova sequence turn {turn_index} did not preserve the exact word sequence"
                )
            unsafe_partial_turns = _mid_sentence_partial_turn_count(result.events)
            if unsafe_partial_turns:
                raise InputError(
                    f"Nova sequence turn {turn_index} crossed "
                    f"{unsafe_partial_turns} mid-sentence PARTIAL_TURN boundary"
                )
            _assert_no_queued_sequence_output(output_queue)
            _require_sequence_task_running(output_reader, "output reader")
            _require_sequence_task_running(audio_pump, "audio pump")

        audio_stop.set()
        await audio_pump
        await send_many(
            (
                {"contentEnd": {"promptName": prompt_name, "contentName": audio_name}},
                {"promptEnd": {"promptName": prompt_name}},
                {"sessionEnd": {}},
            )
        )
        await asyncio.sleep(0)
        if output_reader.done():
            output_reader.result()
            if output_queue.empty() or output_queue.get_nowait() is not _SEQUENCE_OUTPUT_EOF:
                raise InputError("Nova output reader ended without a clean shutdown boundary")
            if not output_queue.empty():
                raise InputError("Nova emitted output after sequence shutdown")
        results = tuple(rendered)
    except BaseException as exc:
        primary_error = exc
    finally:
        if audio_pump is not None:
            audio_pump_error = await _bounded_receiver_stop(audio_pump)
            if audio_pump_error:
                cleanup_errors.append(audio_pump_error.replace("receiver", "audio pump", 1))
        if output_reader is not None:
            receiver_error = await _bounded_receiver_stop(output_reader)
            if receiver_error:
                cleanup_errors.append(receiver_error)
        if stream is not None:
            close_error = await _bounded_cleanup("input stream close", stream.input_stream.close())
            if close_error:
                cleanup_errors.append(close_error)
        exit_args = (
            type(primary_error) if primary_error is not None else None,
            primary_error,
            primary_error.__traceback__ if primary_error is not None else None,
        )
        if stream_entered:
            stream_error = await _bounded_cleanup("stream __aexit__", stream.__aexit__(*exit_args))
            if stream_error:
                cleanup_errors.append(stream_error)

    completed_results = tuple(rendered)
    if primary_error is not None:
        if completed_results:
            detail = str(primary_error) or type(primary_error).__name__
            raise NovaSequenceIncomplete(
                f"Nova sequence failed after {len(completed_results)} completed turn(s): {detail}",
                completed_results,
            ) from primary_error
        raise primary_error.with_traceback(primary_error.__traceback__)
    if cleanup_errors:
        detail = "Nova cleanup did not finish safely: " + "; ".join(cleanup_errors)
        if completed_results:
            raise NovaSequenceIncomplete(detail, completed_results)
        raise InputError(detail)
    if results is None or len(results) != len(texts):
        if completed_results:
            raise NovaSequenceIncomplete(
                "Nova sequence ended without all render results",
                completed_results,
            )
        raise InputError("Nova sequence ended without all render results")
    return results


async def _render_sequence_async(
    texts: tuple[str, ...],
    voice_id: str,
    settings: NovaSettings,
    prompt_name: str,
) -> tuple[NovaRenderResult, ...]:
    if os.environ.get("FRONTIER_AUDIOBOOK_DISABLE_AWS") == "1":
        raise InputError("AWS invocation is disabled by FRONTIER_AUDIOBOOK_DISABLE_AWS")
    try:
        from smithy_http.aio.crt import AWSCRTHTTPClient, AWSCRTHTTPClientConfig
        from aws_sdk_bedrock_runtime.client import AsyncBedrockRuntimeClient
        from aws_sdk_bedrock_runtime.config import AsyncBedrockRuntimeConfig
        from aws_sdk_bedrock_runtime.models import (
            BidirectionalInputPayloadPart,
            InvokeModelWithBidirectionalStreamInputChunk,
            InvokeModelWithBidirectionalStreamOperationInput,
            InvokeModelWithBidirectionalStreamOutputChunk,
            InvokeModelWithBidirectionalStreamOutputInternalServerException,
            InvokeModelWithBidirectionalStreamOutputModelStreamErrorException,
            InvokeModelWithBidirectionalStreamOutputModelTimeoutException,
            InvokeModelWithBidirectionalStreamOutputServiceUnavailableException,
            InvokeModelWithBidirectionalStreamOutputThrottlingException,
            InvokeModelWithBidirectionalStreamOutputUnknown,
            InvokeModelWithBidirectionalStreamOutputValidationException,
        )
    except ImportError as exc:
        raise InputError(
            "The pinned Nova runtime is not installed. Run `uv sync --python 3.12 --no-editable` in .audiobook/."
        ) from exc

    sdk = {
        "transport": lambda: AWSCRTHTTPClient(
            client_config=AWSCRTHTTPClientConfig(force_http_2=True)
        ),
        "client": AsyncBedrockRuntimeClient,
        "config": AsyncBedrockRuntimeConfig,
        "payload": BidirectionalInputPayloadPart,
        "input_chunk": InvokeModelWithBidirectionalStreamInputChunk,
        "operation_input": InvokeModelWithBidirectionalStreamOperationInput,
    }
    model_types = {
        "chunk": InvokeModelWithBidirectionalStreamOutputChunk,
        "errors": (
            InvokeModelWithBidirectionalStreamOutputInternalServerException,
            InvokeModelWithBidirectionalStreamOutputModelStreamErrorException,
            InvokeModelWithBidirectionalStreamOutputModelTimeoutException,
            InvokeModelWithBidirectionalStreamOutputServiceUnavailableException,
            InvokeModelWithBidirectionalStreamOutputThrottlingException,
            InvokeModelWithBidirectionalStreamOutputValidationException,
        ),
        "unknown": InvokeModelWithBidirectionalStreamOutputUnknown,
    }
    sequence_timeout = min(
        settings.stream_timeout_seconds,
        _SEQUENCE_MAX_SESSION_SECONDS,
    )
    try:
        return await asyncio.wait_for(
            _invoke_sequence(texts, voice_id, settings, prompt_name, sdk, model_types),
            timeout=sequence_timeout,
        )
    except TimeoutError as exc:
        raise InputError(
            f"Nova sequence did not complete within the {sequence_timeout:g}-second "
            "persistent-session safety limit"
        ) from exc


def _render_sequence_process_worker(
    connection: Any,
    texts: tuple[str, ...],
    voice_id: str,
    settings: NovaSettings,
    prompt_name: str,
) -> None:
    try:
        results = asyncio.run(_render_sequence_async(texts, voice_id, settings, prompt_name))
        connection.send(("result", _SequenceWorkerOutcome(results)))
    except NovaSequenceIncomplete as exc:
        connection.send(
            (
                "result",
                _SequenceWorkerOutcome(exc.completed_results, str(exc)),
            )
        )
    except InputError as exc:
        connection.send(("input_error", str(exc)))
    except BaseException as exc:
        connection.send(("error", type(exc).__name__, str(exc)))
    finally:
        connection.close()


def render_text_sequence(
    texts: Any,
    voice_id: str,
    settings: NovaSettings,
    *,
    prompt_name: str | None = None,
    paid_render_authorized: bool = False,
) -> tuple[NovaRenderResult, ...]:
    """Render multiple ordered text turns in one billable Nova conversation."""

    if not paid_render_authorized:
        raise InputError("Refusing billable Nova sequence without explicit paid-render authorization")
    if os.name != "posix" or os.uname().sysname not in {"Darwin", "Linux"}:
        raise InputError("Paid Nova rendering is supported only on macOS and Linux")
    if isinstance(texts, (str, bytes)):
        raise InputError("Nova sequence texts must be an ordered collection, not one string")
    try:
        selected_texts = tuple(texts)
    except TypeError as exc:
        raise InputError("Nova sequence texts must be an ordered collection") from exc
    if not selected_texts:
        raise InputError("Refusing to invoke Nova with an empty text sequence")
    for index, text in enumerate(selected_texts, start=1):
        if not isinstance(text, str) or not text.strip():
            raise InputError(f"Nova sequence turn {index} must be nonblank text")

    selected_prompt_name = prompt_name or str(uuid.uuid4())
    try:
        if str(uuid.UUID(selected_prompt_name)) != selected_prompt_name:
            raise ValueError
    except (ValueError, AttributeError) as exc:
        raise InputError("Nova prompt_name must be a canonical UUID") from exc

    sequence_timeout = min(
        settings.stream_timeout_seconds,
        _SEQUENCE_MAX_SESSION_SECONDS,
    )
    hard_timeout = sequence_timeout + _PROCESS_CLEANUP_GRACE_SECONDS
    outcome = _run_worker_process(
        _render_sequence_process_worker,
        (selected_texts, voice_id, settings, selected_prompt_name),
        hard_timeout,
        f"Nova worker exceeded the {sequence_timeout:g}-second persistent-session "
        "safety limit and bounded cleanup grace",
    )
    if not isinstance(outcome, _SequenceWorkerOutcome):
        raise InputError("Nova worker returned an invalid sequence outcome")
    results = outcome.results
    if (
        not isinstance(results, tuple)
        or len(results) > len(selected_texts)
        or any(not isinstance(item, NovaRenderResult) for item in results)
    ):
        raise InputError("Nova worker returned invalid sequence results")
    if outcome.error is not None:
        if not results:
            raise InputError(outcome.error)
        raise NovaSequenceIncomplete(outcome.error, results)
    if len(results) != len(selected_texts):
        raise InputError("Nova worker returned an incomplete sequence without an error")
    return results
