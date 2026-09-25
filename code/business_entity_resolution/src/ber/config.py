"""Run configuration passed to every pipeline stage (docs/DEVELOPMENT.md).

A stage receives one ``RunConfig`` and reads everything from it: the split, its output tag, the tags of its inputs,
optional fold restriction, seed and free-form parameters (``--set key=value``) that the stage owner documents.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from .paths import check_name

# Artifact kinds a stage can read with ``--in <kind>=<tag>`` (docs/CONTRACTS.md C0).
ARTIFACT_KINDS = ("norm", "candidates", "features", "models", "scores", "matches")
SEED = 2026
SPLITS = ("train", "test")


@dataclass
class RunConfig:
    split: str
    tag: str | None = None
    inputs: dict[str, str] = field(default_factory=dict)
    params: dict[str, str] = field(default_factory=dict)
    folds: tuple[int, ...] | None = None
    seed: int = SEED
    n_jobs: int = -1
    device: str = "auto"
    command: str = ""

    def __post_init__(self) -> None:
        if self.split not in SPLITS:
            raise ValueError(f"split must be one of {SPLITS}, got {self.split!r}")
        if self.tag is not None:
            check_name(self.tag)
        for kind, tag in self.inputs.items():
            if kind not in ARTIFACT_KINDS:
                raise ValueError(f"unknown input kind {kind!r}; expected one of {ARTIFACT_KINDS}")
            check_name(tag)
        if self.device not in ("auto", "cuda", "cpu"):
            raise ValueError("device must be auto, cuda or cpu")

    def require_tag(self) -> str:
        if self.tag is None:
            raise ValueError("this stage writes an artifact: pass --tag <member>-<stage>-v<N>")
        return self.tag

    def input_tag(self, kind: str) -> str:
        """Tag to read for an input kind: ``--in kind=tag`` if given, else this run's own tag."""
        if kind not in ARTIFACT_KINDS:
            raise KeyError(f"unknown artifact kind {kind!r}; expected one of {ARTIFACT_KINDS}")
        return self.inputs.get(kind) or self.require_tag()

    def param(self, key: str, default: Any = None, cast: Callable[[str], Any] = str) -> Any:
        """A ``--set key=value`` parameter converted with ``cast`` (e.g. ``cfg.param("k", 40, int)``)."""
        if key not in self.params:
            return default
        return cast(self.params[key])
