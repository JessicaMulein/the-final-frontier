from __future__ import annotations

import socket
import tempfile
from dataclasses import replace
from pathlib import Path

import pytest

import frontier_audiobook.narrate as narrate
from frontier_audiobook.config import load_audition_config
from frontier_audiobook.errors import InputError
from frontier_audiobook.nova import NovaRenderResult
from frontier_audiobook.util import atomic_write_json, read_json, sha256_bytes, workspace_relative
from frontier_audiobook.manuscript import markdown_to_spoken
from frontier_audiobook.verify import normalized_tokens


WORKSPACE = Path(__file__).resolve().parents[2]
AUDIOBOOK_ROOT = WORKSPACE / "audiobook-studio"
CONFIG_PATH = AUDIOBOOK_ROOT / "config" / "audition.toml"


@pytest.fixture(autouse=True)
def deny_python_network(monkeypatch):
    def blocked(*_args, **_kwargs):
        raise AssertionError("offline narration tests must not open a network connection")

    monkeypatch.setattr(socket, "create_connection", blocked)
    monkeypatch.setattr(socket.socket, "connect", blocked)
    monkeypatch.setenv("FRONTIER_AUDIOBOOK_DISABLE_AWS", "1")
    for name in (
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "AWS_SESSION_TOKEN",
        "AWS_PROFILE",
        "AWS_DEFAULT_PROFILE",
    ):
        monkeypatch.delenv(name, raising=False)


@pytest.fixture
def chapter_config():
    parent = AUDIOBOOK_ROOT / "build" / "pytest"
    parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=parent) as temporary:
        root = Path(temporary)
        manuscript_root = root / "manuscript"
        chapter_path = manuscript_root / "chapters" / "discovery" / "test-001-noise.md"
        chapter_path.parent.mkdir(parents=True)
        base = load_audition_config(CONFIG_PATH, WORKSPACE)
        config = replace(
            base,
            manuscript_root=manuscript_root,
            output_root=root / "build" / "auditions",
            package_root=root / "dist" / "auditions",
        )
        yield config, chapter_path


def _write_chapter(path: Path, body: str) -> None:
    path.write_text(
        "---\n"
        "movement: discovery\n"
        "chapter: 1\n"
        'title: "Test Chapter"\n'
        "pov_id: test\n"
        "timeline_id: test\n"
        "motif_events: none\n"
        "hook: test\n"
        "words: 999\n"
        "length_class: short\n"
        "status: draft\n"
        "---\n"
        f"{body}\n",
        encoding="utf-8",
    )


def _render_result(text: str) -> NovaRenderResult:
    return NovaRenderResult(
        audio_lpcm=b"\xe8\x03" * 2400,
        final_transcript=text,
        events=(),
        completion_stop_reason="END_TURN",
    )


def test_frontmatter_is_excluded_and_segmentation_preserves_word_order(chapter_config):
    config, chapter_path = chapter_config
    body = "First *spoken* paragraph has seven deliberate words.\n\nSecond paragraph stays entirely in order."
    _write_chapter(chapter_path, body)

    source, spoken = narrate.chapter_spoken_text(config, 1)
    segments = narrate.segment_spoken_text(spoken, max_words=5)

    assert source.body.startswith("First")
    assert spoken == body.replace("*spoken*", "spoken") + "\n"
    assert "movement:" not in spoken
    assert normalized_tokens(spoken) == tuple(
        token for segment in segments for token in normalized_tokens(segment.text)
    )


def test_carried_over_candidate_reclassifies_mismatch_without_render(chapter_config, monkeypatch):
    config, chapter_path = chapter_config
    body = "The complete paid clip should be reused exactly once."
    _write_chapter(chapter_path, body)
    outline = narrate.plan_narration(config, 1, "tiffany")
    planned = outline["segments"][0]
    segment = narrate.Segment(1, planned["paragraph_index"], planned["text"])
    root = narrate._narration_root(config, 1, "tiffany")
    audio_path = root / "segments" / "legacy.wav"
    transcript_path = root / "transcripts" / "legacy.txt"
    audio_path.parent.mkdir(parents=True)
    transcript_path.parent.mkdir(parents=True)
    audio = narrate._wav_bytes(b"\xe8\x03" * 2400, config)
    audio_path.write_bytes(audio)
    transcript_path.write_text(segment.text + "\n", encoding="utf-8")

    valid = {
        **planned,
        "text_sha256": narrate.sha256_text(segment.text),
        "status": "fidelity_mismatch",
        "audio_path": workspace_relative(WORKSPACE, audio_path),
        "audio_sha256": sha256_bytes(audio),
        "duration_seconds": 0.1,
        "exact_transcript_match": False,
        "coverage_ratio": 0.5,
    }
    broken = {**valid, "audio_path": workspace_relative(WORKSPACE, root / "missing.wav")}
    atomic_write_json(
        root / "manifest.json",
        {**outline, "segments": [broken], "carried_over_segments": [valid]},
    )

    def forbidden_render(*_args, **_kwargs):
        raise AssertionError("a reusable paid clip must not be rendered again")

    monkeypatch.setattr(narrate, "render_text", forbidden_render)
    outcome = narrate.narrate_chapter(
        config,
        1,
        "tiffany",
        paid_render_authorized=True,
        accept_verbatim_prefix=True,
    )

    assert outcome["billable_calls_made"] == 0
    assert outcome["segments_reused"] == 1
    persisted = read_json(root / "manifest.json")
    assert persisted["segments"][0]["status"] == "narrated"
    assert persisted["segments"][0]["transcript"] == segment.text
    assert persisted["segments"][0]["exact_transcript_match"] is True
    assert persisted["segments"][0]["coverage_ratio"] == 1.0


def test_content_addressed_paths_do_not_overwrite_shifted_segments(chapter_config):
    config, _ = chapter_config
    root = narrate._narration_root(config, 1, "tiffany")
    first = narrate._segment_paths(root, narrate.Segment(1, 0, "Earlier text."))
    changed = narrate._segment_paths(root, narrate.Segment(1, 0, "New inserted text."))

    assert first["audio"] != changed["audio"]
    assert len(first["audio"].stem.split("-", 1)[1]) == 64


def test_source_change_stops_before_next_paid_call(chapter_config, monkeypatch):
    config, chapter_path = chapter_config
    body = "One two three four five. Six seven eight nine ten. Eleven twelve."
    _write_chapter(chapter_path, body)
    invocations = 0

    def mutate_after_first_render(text, *_args, paid_render_authorized=False, **_kwargs):
        nonlocal invocations
        assert paid_render_authorized is True
        invocations += 1
        _write_chapter(chapter_path, body + " Changed afterward.")
        return _render_result(text)

    monkeypatch.setattr(narrate, "render_text", mutate_after_first_render)
    with pytest.raises(InputError, match="changed during narration"):
        narrate.narrate_chapter(
            config,
            1,
            "tiffany",
            max_words=5,
            paid_render_authorized=True,
        )

    assert invocations == 1
    assert not (narrate._narration_root(config, 1, "tiffany") / "chapter-001-tiffany.wav").exists()


def test_source_change_after_last_render_stops_before_stitch(chapter_config, monkeypatch):
    config, chapter_path = chapter_config
    body = "One short paid segment."
    _write_chapter(chapter_path, body)
    invocations = 0

    def mutate_during_only_render(text, *_args, paid_render_authorized=False, **_kwargs):
        nonlocal invocations
        assert paid_render_authorized is True
        invocations += 1
        _write_chapter(chapter_path, body + " Changed afterward.")
        return _render_result(text)

    monkeypatch.setattr(narrate, "render_text", mutate_during_only_render)
    with pytest.raises(InputError, match="final stitch"):
        narrate.narrate_chapter(config, 1, "tiffany", paid_render_authorized=True)

    assert invocations == 1
    assert not (narrate._narration_root(config, 1, "tiffany") / "chapter-001-tiffany.wav").exists()


def test_smooth_stitch_trims_variable_silence_fades_edges_and_uses_contextual_gaps(
    chapter_config,
):
    config, _ = chapter_config
    from array import array

    rate = config.nova.sample_rate_hz
    raw_samples = array(
        "h",
        [0] * int(0.10 * rate)
        + [2000] * int(0.10 * rate)
        + [0] * int(0.20 * rate),
    )
    smoothed = narrate._smooth_clip_lpcm(raw_samples.tobytes(), config)
    result = array("h")
    result.frombytes(smoothed)

    assert len(result) < len(raw_samples)
    assert len(result) / rate == pytest.approx(0.14, abs=0.02)
    assert result[0] == 0
    assert result[-1] == 0
    assert max(result) == 2000

    continuation = narrate.Segment(1, 0, "A clause ending here,")
    sentence = narrate.Segment(2, 0, "A sentence ending here.")
    same_paragraph = narrate.Segment(3, 0, "The next words.")
    next_paragraph = narrate.Segment(4, 1, "A new paragraph.")
    assert narrate._gap_between(continuation, same_paragraph) == narrate.CONTINUATION_GAP_SECONDS
    assert narrate._gap_between(sentence, same_paragraph) == narrate.SEGMENT_GAP_SECONDS
    assert narrate._gap_between(sentence, next_paragraph) == narrate.PARAGRAPH_GAP_SECONDS


def test_soft_word_target_never_splits_a_sentence_or_paragraph():
    long_sentence = "One two three four five six seven eight nine ten eleven twelve."
    short_sentence = "Brief ending."
    unpunctuated_paragraph = "Alpha beta gamma delta epsilon zeta eta theta"
    segments = narrate.segment_spoken_text(
        f"{long_sentence} {short_sentence}\n\n{unpunctuated_paragraph}",
        max_words=5,
    )

    assert [segment.text for segment in segments] == [
        long_sentence,
        short_sentence,
        unpunctuated_paragraph,
    ]
    assert segments[0].word_count == 12
    assert all(segment.word_count > 0 for segment in segments)
    assert narrate.SEGMENT_BOUNDARY_POLICY == "safe-narration-punctuation-v26"
    assert narrate.EDGE_FADE_SECONDS == 0.002


def test_mid_sentence_partial_turn_padding_is_removed_and_crossfaded(chapter_config):
    config, _ = chapter_config
    from array import array

    rate = config.nova.sample_rate_hz
    left = array(
        "h",
        [1000] * int(0.10 * rate) + [0] * int(0.10 * rate),
    )
    right = array(
        "h",
        [0] * int(0.25 * rate) + [2000] * int(0.10 * rate),
    )
    repaired = narrate._crossfade_partial_turns(
        ((left.tobytes(), True), (right.tobytes(), False)),
        config,
    )
    samples = array("h")
    samples.frombytes(repaired)

    expected = 0.10 + 0.10 - narrate.PARTIAL_TURN_CROSSFADE_SECONDS
    assert len(samples) / rate == pytest.approx(expected, abs=0.02)
    assert min(samples[int(0.08 * rate) : int(0.11 * rate)]) > 0
    assert samples[0] == 1000
    assert samples[-1] == 2000

    untouched = narrate._crossfade_partial_turns(
        ((left.tobytes(), False), (right.tobytes(), False)),
        config,
    )
    assert untouched == left.tobytes() + right.tobytes()
    assert narrate.PARTIAL_TURN_POLICY == "crossfade-mid-sentence-v1"


@pytest.mark.parametrize(
    ("body", "measurement"),
    [
        (" ".join(f"w{index}" for index in range(33)) + ".", "words=33"),
        (" ".join("abcdefghijklmnopqrst" for _ in range(10)) + ".", "characters=210"),
    ],
)
def test_safe_turn_preflight_rejects_before_paid_render(
    chapter_config,
    monkeypatch,
    body,
    measurement,
):
    config, chapter_path = chapter_config
    _write_chapter(chapter_path, body)
    invocations = 0

    def forbidden_render(*_args, **_kwargs):
        nonlocal invocations
        invocations += 1
        raise AssertionError("unsafe input must not reach render_text")

    monkeypatch.setattr(narrate, "render_text", forbidden_render)
    with pytest.raises(InputError, match=measurement):
        narrate.narrate_chapter(
            config,
            1,
            "tiffany",
            paid_render_authorized=True,
        )

    assert invocations == 0
    assert not narrate._narration_root(config, 1, "tiffany").exists()


def test_no_command_fragments_break_from_prior_narrative_and_trail_next_sentence():
    furniture = "This had none of that furniture."
    trailer = (
        "Nothing repeated for the sake of survival, and nothing in it that anticipated "
        "being received at all."
    )
    preamble = "A preamble, so the receiver can find the start."
    spoken = (
        f"Anything built to send information makes concessions to a receiver. {preamble}\n\n"
        f"{furniture} No preamble. No framing. No address. {trailer}"
    )
    segments = narrate.segment_spoken_text(spoken, max_words=12)
    texts = [segment.text for segment in segments]

    assert furniture in texts
    assert "No preamble. No framing. No address. " + trailer in texts
    assert "No preamble. No framing. No address." not in texts
    assert preamble in texts
    assert texts[texts.index(preamble) - 1] == (
        "Anything built to send information makes concessions to a receiver."
    )
    assert tuple(token for segment in segments for token in normalized_tokens(segment.text)) == (
        normalized_tokens(spoken)
    )
    assert all(len(segment.text) <= narrate.NOVA_SAFE_MAX_CHARACTERS for segment in segments)


def test_no_command_fragments_without_a_safe_trailer_stay_packed_together():
    segments = narrate.segment_spoken_text(
        "This had none of that furniture. No preamble. No framing. No address.",
        max_words=12,
    )

    assert [segment.text for segment in segments] == [
        "This had none of that furniture. No preamble. No framing. No address.",
    ]


def test_short_no_sentence_does_not_go_to_nova_alone():
    prior = "Between those public sounds it stayed under load."
    absence = "No message was present in it."
    trailer = (
        "I could not hear a caller, recover a question, or learn what had been decided."
    )
    segments = narrate.segment_spoken_text(
        f"{prior} {absence} {trailer}",
        max_words=12,
    )
    texts = [segment.text for segment in segments]

    assert prior in texts
    assert absence not in texts
    assert f"{absence} {trailer}" in texts
    assert not any(text.startswith("No message") and trailer not in text for text in texts)
    assert tuple(token for segment in segments for token in normalized_tokens(segment.text)) == (
        normalized_tokens(f"{prior} {absence} {trailer}")
    )


def test_unquoted_imperative_after_a_split_sentence_borrows_the_previous_fragment():
    source = (
        "It sat entirely on my side, after acquisition and before resolved output: "
        "the price of asking this early apparatus, with these settings and this much "
        "information, for an answer coherent enough to read. Ask for less and you buy "
        "speed by destroying the coherence that made the result legible at all."
    )
    segments = narrate.segment_spoken_text(source, max_words=12)
    texts = [segment.text for segment in segments]

    assert not any(text.startswith("Ask for less") for text in texts)
    assert any("Ask for less" in text for text in texts)
    assert tuple(token for segment in segments for token in normalized_tokens(segment.text)) == (
        normalized_tokens(source)
    )
    assert all(len(segment.text) <= narrate.NOVA_SAFE_MAX_CHARACTERS for segment in segments)


def test_unquoted_imperative_sentence_stays_attached_to_prior_sentence():
    prior = "The task was simple."
    command = "Confirm that the receiver still worked after the overnight calibration."
    segments = narrate.segment_spoken_text(f"{prior} {command}", max_words=5)
    texts = [segment.text for segment in segments]

    assert texts == [f"{prior} {command}"]
    assert not any(text.startswith("Confirm that") for text in texts)


def test_consecutive_short_quoted_sentences_pack_in_pairs():
    first = '"I\'m withholding an unsupported claim," I said.'
    second = '"Then support it."'
    third = '"That requires more observation."'
    fourth = '"Which is what the funding is for."'
    spoken = f"{first}\n\n{second}\n\n{third}\n\n{fourth}"
    segments = narrate.segment_spoken_text(spoken, max_words=12)
    texts = [segment.text for segment in segments]

    assert texts == [f"{first} {second}", f"{third} {fourth}"]
    assert second not in texts
    assert third not in texts
    assert all(len(segment.text) <= narrate.NOVA_SAFE_MAX_CHARACTERS for segment in segments)
    assert tuple(token for segment in segments for token in normalized_tokens(segment.text)) == (
        normalized_tokens(spoken)
    )


def test_short_quoted_sentence_does_not_glue_onto_prior_narrative():
    narrative = "I declined the briefing."
    quoted = '"Then support it."'
    spoken = f"{narrative}\n\n{quoted}"
    segments = narrate.segment_spoken_text(spoken, max_words=12)

    assert [segment.text for segment in segments] == [narrative, quoted]


def test_third_short_quoted_sentence_does_not_join_a_packed_pair():
    first = '"Then support it."'
    second = '"Then observe it."'
    third = '"Then wait."'
    spoken = f"{first}\n\n{second}\n\n{third}"
    segments = narrate.segment_spoken_text(spoken, max_words=12)
    texts = [segment.text for segment in segments]

    assert texts == [f"{first} {second}", third]


def test_quoted_question_keeps_its_attribution_and_pairs_with_the_reply():
    question = '"Near field?" he asked.'
    reply = '"Not in any geometry that closes."'
    spoken = f"{question}\n\n{reply}"
    segments = narrate.segment_spoken_text(spoken, max_words=12)
    texts = [segment.text for segment in segments]

    assert len(texts) == 1
    assert "he asked." not in texts
    assert reply not in texts
    assert "Near field" in texts[0]
    assert "he asked" in texts[0]
    assert "Not in any geometry that closes" in texts[0]
    assert tuple(token for segment in segments for token in normalized_tokens(segment.text)) == (
        normalized_tokens(spoken)
    )


def test_short_quoted_turn_may_borrow_a_longer_following_quote():
    question = '"Could it be task switching?"'
    answer = '"Attention is task switching when we want to count it."'
    spoken = f"{question}\n\n{answer}"
    segments = narrate.segment_spoken_text(spoken, max_words=12)
    texts = [segment.text for segment in segments]

    assert texts == [f"{question} {answer}"]
    assert question not in texts
    assert tuple(token for segment in segments for token in normalized_tokens(segment.text)) == (
        normalized_tokens(spoken)
    )


def test_unclosed_quoted_fragments_rejoin_inside_one_paragraph():
    spoken = (
        '"You don\'t have to want to. I need you beside him. Tell me when you\'re there."'
    )
    segments = narrate.segment_spoken_text(spoken, max_words=12)
    texts = [segment.text for segment in segments]

    assert any("You don't have to want to" in text for text in texts)
    assert any(
        "I need you beside him" in text and "Tell me when you're there" in text
        for text in texts
    )
    assert not any(text.lstrip().startswith("Tell me") for text in texts)
    assert all(narrate._sentence_end_count(text) <= narrate.MAX_PACKED_SENTENCE_ENDS for text in texts)
    assert tuple(token for segment in segments for token in normalized_tokens(segment.text)) == (
        normalized_tokens(spoken)
    )
    assert all(len(segment.text) <= narrate.NOVA_SAFE_MAX_CHARACTERS for segment in segments)


def test_sentence_split_keeps_the_closing_quote_after_a_period():
    spoken = (
        '"He\'s on the floor by the table," the girl said. Then, "He\'s breathing." '
        'Then, "I don\'t know if that\'s breathing."'
    )
    segments = narrate.segment_spoken_text(spoken, max_words=12)
    texts = [segment.text for segment in segments]

    assert any(text.endswith('"He\'s breathing."') or text.endswith("breathing.\"") for text in texts)
    assert not any(text.rstrip().endswith("breathing.") and '"' not in text[-12:] for text in texts)
    assert all('breathing.' in text for text in texts if "He's breathing" in text)
    assert tuple(token for segment in segments for token in normalized_tokens(segment.text)) == (
        normalized_tokens(spoken)
    )


def test_bare_no_trails_the_next_same_paragraph_sentence():
    question = "Could she reach the latch without leaving her father?"
    refusal = "No."
    trailer = "I told the crew."
    segments = narrate.segment_spoken_text(f"{question} {refusal} {trailer}", max_words=12)
    texts = [segment.text for segment in segments]

    assert question in texts
    assert refusal not in texts
    assert f"{refusal} {trailer}" in texts
    assert not any(text == "No." for text in texts)
    assert tuple(token for segment in segments for token in normalized_tokens(segment.text)) == (
        normalized_tokens(f"{question} {refusal} {trailer}")
    )


def test_isolated_one_word_caption_attaches_to_the_previous_short_sentence():
    spoken = (
        "I asked what she could see through the front window. Bus shelter. "
        "Green pharmacy sign. Houses opposite, no fields. Town."
    )
    segments = narrate.segment_spoken_text(spoken, max_words=12)
    texts = [segment.text for segment in segments]

    assert "Town." not in texts
    assert any(text.endswith("Town.") for text in texts)
    assert not any(text == "Town." for text in texts)
    assert tuple(token for segment in segments for token in normalized_tokens(segment.text)) == (
        normalized_tokens(spoken)
    )
    assert all(len(segment.text) <= narrate.NOVA_SAFE_MAX_CHARACTERS for segment in segments)


def test_leftover_short_quote_trails_the_next_short_sentence():
    quoted = '"That isn\'t an answer."'
    follower = "It was not."
    spoken = f"{quoted}\n\n{follower}"
    segments = narrate.segment_spoken_text(spoken, max_words=12)
    texts = [segment.text for segment in segments]

    assert texts == [f"{quoted} {follower}"]
    assert quoted not in texts
    assert tuple(token for segment in segments for token in normalized_tokens(segment.text)) == (
        normalized_tokens(spoken)
    )


def test_leftover_short_quote_trails_a_following_narrative_sentence():
    quoted = '"I can\'t tell."'
    follower = (
        "Was that breath, or was it the sound a throat makes when nobody is using it?"
    )
    spoken = f"{quoted}\n\n{follower}"
    segments = narrate.segment_spoken_text(spoken, max_words=12)
    texts = [segment.text for segment in segments]

    assert quoted not in texts
    assert any(quoted in text and follower in text for text in texts)
    assert tuple(token for segment in segments for token in normalized_tokens(segment.text)) == (
        normalized_tokens(spoken)
    )


def test_short_quote_tail_closes_the_previous_unclosed_turn():
    spoken = (
        '"Detection, initially. Consent architecture when the science permits it. '
        'Equitable access."'
    )
    segments = narrate.segment_spoken_text(spoken, max_words=12)
    texts = [segment.text for segment in segments]

    assert any(text.startswith('"Detection, initially.') for text in texts)
    assert any("Consent architecture when the science permits it." in text for text in texts)
    assert any("Equitable access" in text for text in texts)
    assert all(
        narrate._sentence_end_count(text) <= narrate.QUOTE_FRAGMENT_MAX_SENTENCE_ENDS
        for text in texts
    )
    assert tuple(token for segment in segments for token in normalized_tokens(segment.text)) == (
        normalized_tokens(spoken)
    )
    assert all(len(segment.text) <= narrate.NOVA_SAFE_MAX_CHARACTERS for segment in segments)


def test_quoted_imperative_dialogue_may_open_a_turn():
    source = (
        'She turned in the doorway and said, "Confirm that the lock held," '
        "and then she waited while the latch seated itself against the inner door."
    )
    segments = narrate.segment_spoken_text(source, max_words=12)
    texts = [segment.text for segment in segments]

    assert any(text.startswith('"Confirm that') or '"Confirm that' in text for text in texts)
    assert tuple(token for segment in segments for token in normalized_tokens(segment.text)) == (
        normalized_tokens(source)
    )


def test_colon_cut_does_not_emit_an_unquoted_imperative_as_its_own_turn():
    source = (
        "My instruction, when I finally read it rather than reading the people around it, "
        "was narrow: confirm that a particular answer on a funding disclosure remained accurate "
        "after Dr Mara Venn's recent modifications to the mathematical receiver at Northline Array."
    )
    segments = narrate.segment_spoken_text(source, max_words=12)

    assert not any(segment.text.startswith("Confirm that") for segment in segments)
    assert any("confirm that" in segment.text.casefold() for segment in segments)
    assert any(segment.text.startswith("Was narrow:") for segment in segments)
    assert tuple(token for segment in segments for token in normalized_tokens(segment.text)) == (
        normalized_tokens(source)
    )
    assert all(len(segment.text) <= narrate.NOVA_SAFE_MAX_CHARACTERS for segment in segments)


def test_short_leftover_trails_the_next_same_paragraph_sentence():
    host = (
        "Then I ran the same tests against the archived December sample, where the "
        "crossing bell supplied repeated acoustic edges."
    )
    leftover = "Each edge produced a small phase-coherent response."
    follower = (
        "When the bell stopped, the periodic response stopped and the sustained "
        "attention released more slowly."
    )
    segments = narrate.segment_spoken_text(
        f"{host} {leftover} {follower}",
        max_words=12,
    )
    texts = [segment.text for segment in segments]

    assert texts == [host, f"{leftover} {follower}"]
    assert leftover not in texts
    assert not any(host in text and leftover in text for text in texts)
    assert all(len(segment.text) <= narrate.NOVA_SAFE_MAX_CHARACTERS for segment in segments)


def test_over_target_leftover_does_not_pull_a_third_sentence():
    host = (
        "At the time there were three structures in the resolved field and nothing "
        "to call them."
    )
    first = "A sustained visual error."
    second = "A human voice carrying a location."
    third = (
        "Then the sharp redistribution of attention that followed when the voice "
        "was trusted over the display."
    )
    segments = narrate.segment_spoken_text(
        f"{host} {first} {second} {third}",
        max_words=12,
    )
    texts = [segment.text for segment in segments]

    assert texts == [host, first, second, third]
    assert not any(second in text and third in text for text in texts)
    assert all(len(segment.text) <= narrate.NOVA_SAFE_MAX_CHARACTERS for segment in segments)


def test_chapter_packing_does_not_join_two_complete_sentences_to_fill_the_budget():
    first = "The geometry differed from the route correction."
    second = "The timing family did not."
    segments = narrate.segment_spoken_text(f"{first} {second}", max_words=12)

    assert [segment.text for segment in segments] == [first, second]


def test_short_colon_attribution_is_split_from_the_written_content():
    source = (
        "I wrote: Hypothesis: a continuous live field coupled to human perceptual "
        "and attentional timing."
    )
    segments = narrate.segment_spoken_text(source, max_words=12)
    texts = [segment.text for segment in segments]

    assert texts[0] == "I wrote."
    assert texts[1].startswith("Hypothesis:")
    assert not any(text.startswith("I wrote:") for text in texts)
    assert tuple(token for segment in segments for token in normalized_tokens(segment.text)) == (
        normalized_tokens(source)
    )


def test_heading_colon_without_an_attribution_verb_stays_one_turn():
    source = (
        "Hypothesis: a continuous live field coupled to human perceptual and "
        "attentional timing."
    )
    segments = narrate.segment_spoken_text(source, max_words=12)

    assert [segment.text for segment in segments] == [source]


def test_longer_wrote_attribution_splits_from_the_drafted_sentence():
    source = (
        "I wrote a warning into the draft: The present hardware configuration is "
        "observational only."
    )
    segments = narrate.segment_spoken_text(source, max_words=12)
    texts = [segment.text for segment in segments]

    assert texts[0] == "I wrote a warning into the draft."
    assert texts[1].startswith("The present hardware")
    assert tuple(token for segment in segments for token in normalized_tokens(segment.text)) == (
        normalized_tokens(source)
    )


def test_ten_word_leftover_does_not_absorb_the_next_sentence():
    host = (
        "What I withheld was that the source now appeared to be a single live "
        "emergency dispatcher rather than a town, a tower, or an unknown class of machine."
    )
    leftover = "The institute still believed I was characterizing an anomalous band."
    follower = (
        "Julian's disclosure review still described the hardware truthfully: "
        "receive-only, no transmit stage."
    )
    segments = narrate.segment_spoken_text(
        f"{host} {leftover} {follower}",
        max_words=12,
    )
    texts = [segment.text for segment in segments]

    assert leftover in texts
    assert follower in texts
    assert not any(leftover in text and follower in text for text in texts)
    assert all(len(segment.text) <= narrate.NOVA_SAFE_MAX_CHARACTERS for segment in segments)


def test_one_word_form_labels_do_not_trail_an_over_target_host():
    host = (
        "Northline's observation log is a bound book with printed fields, because "
        "somebody decades ago decided that a scientist left to design her own page "
        "would leave things out."
    )
    labels = "Date. Instrument. Configuration. Sky. Operator."
    segments = narrate.segment_spoken_text(f"{host} {labels}", max_words=12)
    texts = [segment.text for segment in segments]

    assert texts[0] == host
    assert "Date." in texts[1]
    assert not any(text.endswith(" Date.") for text in texts)
    assert all(len(segment.text) <= narrate.NOVA_SAFE_MAX_CHARACTERS for segment in segments)


def test_quoted_commands_do_not_pack_three_sentences_in_one_turn():
    spoken = (
        '"Put the phone on speaker," I said. "Take it with you. Go back to your dad."'
    )
    segments = narrate.segment_spoken_text(spoken, max_words=12)
    texts = [segment.text for segment in segments]

    assert not any(text.count(".") >= 3 for text in texts)
    assert any("Put the phone on speaker" in text for text in texts)
    assert any("Go back to your dad" in text for text in texts)
    assert tuple(token for segment in segments for token in normalized_tokens(segment.text)) == (
        normalized_tokens(spoken)
    )
    assert all(len(segment.text) <= narrate.NOVA_SAFE_MAX_CHARACTERS for segment in segments)


def test_quoted_write_command_does_not_keep_a_following_sentence_in_the_same_turn():
    spoken = (
        '"Write down that it exists and that I know it does. And if my name goes '
        'anywhere near this, I hear it from you first."'
    )
    segments = narrate.segment_spoken_text(spoken, max_words=12)
    texts = [segment.text for segment in segments]

    assert any("Write down that it exists" in text for text in texts)
    assert any("I hear it from you first" in text for text in texts)
    assert not any(
        "Write down that it exists" in text and "I hear it from you first" in text
        for text in texts
    )
    assert tuple(token for segment in segments for token in normalized_tokens(segment.text)) == (
        normalized_tokens(spoken)
    )
    assert all(len(segment.text) <= narrate.NOVA_SAFE_MAX_CHARACTERS for segment in segments)


def test_comma_cut_does_not_end_a_turn_on_no_noun():
    source = (
        "The request went into the queue at 19:52, and in the morning I would know "
        "which of the four would sit in that room, and I would still have no procedure, "
        "no channel, and no name by which the fifth person could be asked anything at all."
    )
    segments = narrate.segment_spoken_text(source, max_words=12)
    texts = [segment.text for segment in segments]

    assert not any(text.endswith("no procedure.") for text in texts)
    assert any("no procedure" in text and "no channel" in text for text in texts)
    assert tuple(token for segment in segments for token in normalized_tokens(segment.text)) == (
        normalized_tokens(source)
    )
    assert all(len(segment.text) <= narrate.NOVA_SAFE_MAX_CHARACTERS for segment in segments)
    assert all(segment.word_count <= narrate.NOVA_SAFE_MAX_WORDS for segment in segments)


def test_oversized_sentence_uses_narration_only_comma_punctuation_without_changing_words():
    source = (
        "I kept the curves pinned above the bench in the order I had learned them, "
        "and when something anomalous surfaced the procedure was to walk down that list "
        "until one of our own machines confessed."
    )
    segments = narrate.segment_spoken_text(source)

    assert [segment.text for segment in segments] == [
        "I kept the curves pinned above the bench in the order I had learned them.",
        "And when something anomalous surfaced the procedure was to walk down that list "
        "until one of our own machines confessed.",
    ]
    assert all(segment.narration_only_punctuation for segment in segments)
    assert tuple(token for segment in segments for token in normalized_tokens(segment.text)) == normalized_tokens(source)
    assert all(len(segment.text) <= narrate.NOVA_SAFE_MAX_CHARACTERS for segment in segments)
    assert all(segment.word_count <= narrate.NOVA_SAFE_MAX_WORDS for segment in segments)


def test_oversized_sentence_uses_narration_only_semicolon_punctuation_without_changing_words():
    source = (
        "The distinction was exact enough to survive review, which is the only standard "
        "I am paid to meet: diagnostic output was not a transmit stage; an antenna capable "
        "of reciprocity was not an emitter without a path that drove it; a computational "
        "reconstruction was not a message sent to whatever had been measured."
    )
    segments = narrate.segment_spoken_text(source)

    assert all(segment.narration_only_punctuation for segment in segments)
    assert tuple(token for segment in segments for token in normalized_tokens(segment.text)) == normalized_tokens(source)
    assert all(len(segment.text) <= narrate.NOVA_SAFE_MAX_CHARACTERS for segment in segments)
    assert all(segment.word_count <= narrate.NOVA_SAFE_MAX_WORDS for segment in segments)
    assert any(";" not in segment.text for segment in segments)


def test_oversized_sentence_without_comma_uses_conjunction_fallback():
    source = (
        "I stood at the window at the end of the hall with my hands flat on the sill "
        "and looked at a car park and a line of poplars going over in the wind."
    )
    segments = narrate.segment_spoken_text(source)

    assert [segment.text for segment in segments] == [
        "I stood at the window at the end of the hall with my hands flat on the sill "
        "and looked at a car park.",
        "And a line of poplars going over in the wind.",
    ]
    assert all(segment.narration_only_punctuation for segment in segments)
    assert tuple(token for segment in segments for token in normalized_tokens(segment.text)) == normalized_tokens(source)


def test_sentence_initial_at_clock_is_spelled_and_mid_sentence_digits_stay():
    source = (
        "The call clock said 14:08:17. At 14:27 the ambulance status changed "
        "to transporting, with no destination on my screen. Then the crew "
        "confirmed patient contact at 14:14:52."
    )
    spoken = markdown_to_spoken(source, "chapter-012")

    assert "said 14:08:17." in spoken
    assert "contact at 14:14:52." in spoken
    assert "At fourteen twenty-seven the ambulance" in spoken
    assert "At 14:27" not in spoken
    assert normalized_tokens("fourteen twenty-seven") == ("fourteen", "twenty", "seven")
    segments = narrate.segment_spoken_text(spoken, max_words=12)
    assert not any(segment.text.startswith("At 14:") for segment in segments)
    assert any("fourteen twenty-seven" in segment.text for segment in segments)
    assert tuple(token for segment in segments for token in normalized_tokens(segment.text)) == (
        normalized_tokens(spoken)
    )


def test_hhmmss_clock_is_not_treated_as_an_at_time():
    spoken = markdown_to_spoken("At 14:08:17 the stamp advanced.", "chapter-012")

    assert spoken == "At 14:08:17 the stamp advanced."


def test_short_isolated_narrative_attaches_to_the_previous_over_budget_host():
    host = (
        "Mara had already walked the forms and found every one of them assuming a "
        "recruitment, a message, or a name."
    )
    short = "I did not need to repeat her work."
    follower = (
        "What I had that she did not was the definition itself, and the definition "
        "nowhere said that a name had to be pronounceable."
    )
    spoken = f"{host} {short} {follower}"
    segments = narrate.segment_spoken_text(spoken, max_words=12)
    texts = [segment.text for segment in segments]

    assert short not in texts
    assert any(host in text and short in text for text in texts)
    assert any(text == follower or follower in text for text in texts)
    assert not any(text.startswith(short) for text in texts)
    assert tuple(token for segment in segments for token in normalized_tokens(segment.text)) == (
        normalized_tokens(spoken)
    )
    assert all(narrate._sentence_end_count(text) <= narrate.MAX_PACKED_SENTENCE_ENDS for text in texts)
    assert all(len(text) <= narrate.NOVA_SAFE_MAX_CHARACTERS for text in texts)


def test_ordinary_short_narrative_does_not_attach_to_make_a_two_sentence_turn():
    host = (
        "A former public research director, outside counsel, and the adviser the "
        "institute had already proposed inviting."
    )
    short = "Their introductory note stated a public-interest purpose."
    spoken = f"{host} {short}"
    segments = narrate.segment_spoken_text(spoken, max_words=12)
    texts = [segment.text for segment in segments]

    assert texts == [host, short]
    assert all(narrate._sentence_end_count(text) <= 1 for text in texts)


def test_consecutive_short_questions_pack_into_pairs_not_triples():
    host = (
        "The outside adviser had received an earlier phrase from the invention notice, "
        "structured human-associated signals, and had returned three questions."
    )
    q1 = "Could a receiver distinguish simultaneous subjects?"
    q2 = "Could a channel persist across hardware?"
    q3 = "Could the method support enrolment without conventional identity data?"
    spoken = f"{host} {q1} {q2} {q3}"
    segments = narrate.segment_spoken_text(spoken, max_words=12)
    texts = [segment.text for segment in segments]
    pair = f"{q1} {q2}"

    assert q1 not in texts
    assert q2 not in texts
    assert pair in texts
    assert q3 in texts
    assert host in texts
    assert f"{q1} {q2} {q3}" not in texts
    assert all(text.count("?") <= narrate.MAX_PACKED_SHORT_QUESTIONS for text in texts)
    assert all(len(text) <= narrate.NOVA_SAFE_MAX_CHARACTERS for text in texts)
    assert tuple(token for segment in segments for token in normalized_tokens(segment.text)) == (
        normalized_tokens(spoken)
    )


def test_single_short_question_attaches_to_the_previous_host():
    host = "She checked the hallway once more before she moved."
    question = "Could she reach the latch without leaving her father?"
    spoken = f"{host} {question}"
    segments = narrate.segment_spoken_text(spoken, max_words=12)
    texts = [segment.text for segment in segments]

    assert question not in texts
    assert any(host in text and question in text for text in texts)
    assert all(narrate._sentence_end_count(text) <= narrate.MAX_PACKED_SENTENCE_ENDS for text in texts)
    assert tuple(token for segment in segments for token in normalized_tokens(segment.text)) == (
        normalized_tokens(spoken)
    )


def test_short_quote_does_not_absorb_a_three_period_quoted_reply():
    opener = '"A standard for what?"'
    reply = (
        '"Detection, initially. Consent architecture when the science permits it. '
        'Equitable access."'
    )
    spoken = f"{opener}\n\n{reply}"
    segments = narrate.segment_spoken_text(spoken, max_words=12)
    texts = [segment.text for segment in segments]

    assert opener in texts
    assert not any(opener in text and "Detection" in text for text in texts)
    assert any("Detection, initially" in text for text in texts)
    assert any("Equitable access." in text for text in texts)
    assert all(narrate._sentence_end_count(text) <= narrate.MAX_PACKED_SENTENCE_ENDS for text in texts)
    assert all(len(text) <= narrate.NOVA_SAFE_MAX_CHARACTERS for text in texts)
    assert tuple(token for segment in segments for token in normalized_tokens(segment.text)) == (
        normalized_tokens(spoken)
    )


def test_short_form_labels_do_not_pack_past_two_sentence_ends():
    spoken = "May constitute. Could engage. Subject to determination."
    segments = narrate.segment_spoken_text(spoken, max_words=12)
    texts = [segment.text for segment in segments]

    assert "May constitute. Could engage. Subject to determination." not in texts
    assert all(narrate._sentence_end_count(text) <= narrate.MAX_PACKED_SENTENCE_ENDS for text in texts)
    assert tuple(token for segment in segments for token in normalized_tokens(segment.text)) == (
        normalized_tokens(spoken)
    )
