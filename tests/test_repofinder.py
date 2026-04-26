from pathlib import Path

import pytest

from src.repofinder import IngestionParser, RepoFinderSystem


def test_ingestion_rejects_unsupported_extension(tmp_path: Path):
    bad_file = tmp_path / "notes.pdf"
    bad_file.write_text("fake", encoding="utf-8")

    parser = IngestionParser()
    with pytest.raises(ValueError, match="Unsupported file type"):
        parser.ingest([str(bad_file)])


def test_end_to_end_returns_grounded_output(tmp_path: Path):
    schedule = tmp_path / "schedule.md"
    notes = tmp_path / "notes.txt"

    schedule.write_text(
        "Week 4: Build RAG pipeline. Deadline Friday. Prioritize evaluation and citations.",
        encoding="utf-8",
    )
    notes.write_text(
        "Use chunking and top-k retrieval. Add groundedness checks and regression tests.",
        encoding="utf-8",
    )

    system = RepoFinderSystem(top_k=3)
    output = system.run(
        query="Plan what I should do this week before the deadline",
        file_paths=[str(schedule), str(notes)],
    )

    assert "Mode: planning" in output["answer"]
    assert output["evaluation"]["passed"] is True
    assert len(output["citations"]) >= 1


def test_low_relevance_query_is_handled_safely(tmp_path: Path):
    doc = tmp_path / "repo.md"
    doc.write_text("This repository contains study notes about AI workflows.", encoding="utf-8")

    system = RepoFinderSystem(top_k=2)
    output = system.run(
        query="Explain marine biology taxonomy in coral ecosystems",
        file_paths=[str(doc)],
    )

    assert isinstance(output["evaluation"]["passed"], bool)
    assert "answer" in output
