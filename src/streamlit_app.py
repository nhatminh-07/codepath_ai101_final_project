"""Streamlit UI for running RepoFinder end to end."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import List

import streamlit as st

try:
    from .repofinder import RepoFinderSystem, configure_logging
except ImportError:
    from repofinder import RepoFinderSystem, configure_logging


SUPPORTED_EXTENSIONS = ["md", "txt", "csv", "pdf"]


def _save_uploaded_files(uploaded_files, temp_dir: Path) -> List[str]:
    saved_paths: List[str] = []
    for uploaded in uploaded_files:
        destination = temp_dir / uploaded.name
        destination.write_bytes(uploaded.getvalue())
        saved_paths.append(str(destination))
    return saved_paths


def _collect_local_project_files() -> List[str]:
    candidates = [Path("README.md"), Path("model_card.md")]
    return [str(path) for path in candidates if path.exists()]


def render() -> None:
    configure_logging(logging.WARNING)

    st.set_page_config(
        page_title="RepoFinder UI",
        page_icon="R",
        layout="wide",
    )

    st.title("RepoFinder: Document Assistant")
    st.caption(
        "Upload local files, ask a planning or analysis question, and review grounded output with citations."
    )

    with st.sidebar:
        st.header("Run Settings")
        top_k = st.slider("Retriever top-k", min_value=1, max_value=10, value=3)
        include_local_defaults = st.checkbox(
            "Include README.md + model_card.md from this repo",
            value=True,
        )
        show_json = st.checkbox("Show full JSON output", value=False)

        st.markdown("### Demo Prompts")
        st.markdown("- Plan the highest-priority tasks for this project")
        st.markdown("- What should I do this week before the deadline?")
        st.markdown("- Explain marine biology taxonomy in coral ecosystems")

    query = st.text_area(
        "Query",
        value="Plan the highest-priority tasks for this project",
        height=120,
    )

    uploaded_files = st.file_uploader(
        "Upload one or more files (.md, .txt, .csv, .pdf)",
        type=SUPPORTED_EXTENSIONS,
        accept_multiple_files=True,
    )

    feedback = st.text_input(
        "Optional human feedback note",
        value="",
        placeholder="Useful, but add more schedule detail",
    )

    run_clicked = st.button("Run RepoFinder", type="primary")

    if not run_clicked:
        st.info("Select files and click Run RepoFinder.")
        return

    if not query.strip():
        st.error("Query is required.")
        return

    with TemporaryDirectory() as tmp:
        temp_dir = Path(tmp)
        input_paths: List[str] = []

        if include_local_defaults:
            input_paths.extend(_collect_local_project_files())

        if uploaded_files:
            input_paths.extend(_save_uploaded_files(uploaded_files, temp_dir))

        if not input_paths:
            st.error("Provide at least one file via upload or local defaults.")
            return

        system = RepoFinderSystem(top_k=top_k)

        try:
            output = system.run(query=query.strip(), file_paths=input_paths)
            if feedback.strip():
                system.submit_human_feedback(feedback)
        except Exception as exc:  # pragma: no cover
            st.exception(exc)
            return

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Answer")
        st.text(output["answer"])

        st.subheader("Plan")
        for step in output["plan"]:
            st.markdown(f"- {step}")

        st.subheader("Citations")
        if output["citations"]:
            for citation in output["citations"]:
                st.markdown(f"- {citation}")
        else:
            st.write("No citations returned.")

    with col2:
        st.subheader("Quality")
        st.metric("Confidence", f"{output['confidence']:.3f}")
        st.write("Evaluation")
        st.json(output["evaluation"])

        st.write("Retrieval scores")
        st.json(output["retrieval_scores"])

    if show_json:
        st.subheader("Full JSON")
        st.code(json.dumps(output, indent=2), language="json")


if __name__ == "__main__":
    render()
