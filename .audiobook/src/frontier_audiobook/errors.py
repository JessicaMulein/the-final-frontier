"""Expected failures with stable command-line exit semantics."""

from __future__ import annotations


class AudiobookError(Exception):
    """Base class for user-actionable pipeline failures."""

    exit_code = 2


class InputError(AudiobookError):
    """A required input is absent, malformed, stale, or incomplete."""


class FidelityMismatch(AudiobookError):
    """A complete transcript differs from the expected spoken text."""

    exit_code = 1
