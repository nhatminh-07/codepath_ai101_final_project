"""RepoFinder core pipeline.

This module implements a lightweight RAG + agentic workflow that mirrors the
system diagram in model_card.md.
"""

from __future__ import annotations

from dataclasses import dataclass
import logging
import math
from pathlib import Path
import re
from typing import Dict, List, Sequence, Tuple


LOGGER = logging.getLogger("repofinder")


def configure_logging(level: int = logging.INFO) -> None:
    """Configure structured logging once for local CLI use."""
    if LOGGER.handlers:
        return

    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    LOGGER.addHandler(handler)
    LOGGER.setLevel(level)


@dataclass
class DocumentChunk:
    chunk_id: str
    source: str
    text: str


@dataclass
class RetrievalHit:
    chunk: DocumentChunk
    score: float


@dataclass
class AgentResult:
    plan: List[str]
    answer: str
    citations: List[str]
    confidence: float


@dataclass
class EvaluationResult:
    passed: bool
    groundedness_ok: bool
    mode_ok: bool
    confidence_ok: bool
    notes: List[str]


class IngestionParser:
    """Validates files, extracts text, and chunks content for retrieval."""

    supported_suffixes = {".md", ".txt", ".csv", ".pdf"}

    def __init__(self, chunk_size: int = 500, overlap: int = 80):
        if chunk_size <= overlap:
            raise ValueError("chunk_size must be greater than overlap")
        self.chunk_size = chunk_size
        self.overlap = overlap

    def ingest(self, file_paths: Sequence[str]) -> List[DocumentChunk]:
        if not file_paths:
            raise ValueError("At least one input file is required")

        chunks: List[DocumentChunk] = []

        for path_str in file_paths:
            path = Path(path_str)
            self._validate_file(path)
            text = self._read_file_text(path)

            if not text.strip():
                LOGGER.warning("Skipping empty file: %s", path)
                continue

            parsed = self._chunk_text(str(path), text)
            LOGGER.info("Ingested %s -> %d chunks", path, len(parsed))
            chunks.extend(parsed)

        if not chunks:
            raise ValueError("No usable text was ingested from the provided files")

        return chunks

    def _read_file_text(self, path: Path) -> str:
        if path.suffix.lower() == ".pdf":
            return self._extract_pdf_text(path)
        return path.read_text(encoding="utf-8")

    def _extract_pdf_text(self, path: Path) -> str:
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise ImportError(
                "PDF support requires pypdf. Install dependencies with: pip install -r requirements.txt"
            ) from exc
        reader = PdfReader(str(path))
        pages = [(page.extract_text() or "") for page in reader.pages]
        return "\n".join(pages)

    def _validate_file(self, path: Path) -> None:
        if not path.exists():
            raise FileNotFoundError(f"Input file not found: {path}")
        if path.suffix.lower() not in self.supported_suffixes:
            raise ValueError(
                f"Unsupported file type {path.suffix}. Supported: {sorted(self.supported_suffixes)}"
            )
        if path.stat().st_size > 5_000_000:
            raise ValueError(f"File is too large (>5MB): {path}")

    def _chunk_text(self, source: str, text: str) -> List[DocumentChunk]:
        normalized = re.sub(r"\s+", " ", text).strip()
        if len(normalized) <= self.chunk_size:
            return [DocumentChunk(chunk_id=f"{source}#0", source=source, text=normalized)]

        chunks: List[DocumentChunk] = []
        step = self.chunk_size - self.overlap
        idx = 0
        for start in range(0, len(normalized), step):
            piece = normalized[start : start + self.chunk_size].strip()
            if piece:
                chunks.append(
                    DocumentChunk(chunk_id=f"{source}#{idx}", source=source, text=piece)
                )
                idx += 1
            if start + self.chunk_size >= len(normalized):
                break
        return chunks


class Retriever:
    """Simple TF-IDF retriever implemented with sparse dictionaries."""

    token_pattern = re.compile(r"[a-z0-9_]+")

    def __init__(self, chunks: Sequence[DocumentChunk]):
        if not chunks:
            raise ValueError("Retriever requires at least one chunk")
        self.chunks = list(chunks)
        self.idf: Dict[str, float] = {}
        self.chunk_vectors: List[Dict[str, float]] = []
        self._build_index()

    def _tokenize(self, text: str) -> List[str]:
        return self.token_pattern.findall(text.lower())

    def _tf(self, tokens: Sequence[str]) -> Dict[str, float]:
        counts: Dict[str, int] = {}
        for token in tokens:
            counts[token] = counts.get(token, 0) + 1
        total = max(len(tokens), 1)
        return {token: count / total for token, count in counts.items()}

    def _build_index(self) -> None:
        docs_tokens = [self._tokenize(chunk.text) for chunk in self.chunks]

        doc_freq: Dict[str, int] = {}
        for tokens in docs_tokens:
            for token in set(tokens):
                doc_freq[token] = doc_freq.get(token, 0) + 1

        n_docs = len(docs_tokens)
        self.idf = {
            token: math.log((n_docs + 1) / (df + 1)) + 1.0
            for token, df in doc_freq.items()
        }

        self.chunk_vectors = [self._tfidf_vector(tokens) for tokens in docs_tokens]

    def _tfidf_vector(self, tokens: Sequence[str]) -> Dict[str, float]:
        tf = self._tf(tokens)
        return {token: tf_val * self.idf.get(token, 0.0) for token, tf_val in tf.items()}

    @staticmethod
    def _cosine(a: Dict[str, float], b: Dict[str, float]) -> float:
        if not a or not b:
            return 0.0
        common = set(a.keys()) & set(b.keys())
        dot = sum(a[k] * b[k] for k in common)
        norm_a = math.sqrt(sum(v * v for v in a.values()))
        norm_b = math.sqrt(sum(v * v for v in b.values()))
        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0
        return dot / (norm_a * norm_b)

    def search(self, query: str, top_k: int = 3) -> List[RetrievalHit]:
        query_tokens = self._tokenize(query)
        query_vec = self._tfidf_vector(query_tokens)

        scored: List[RetrievalHit] = []
        for chunk, vec in zip(self.chunks, self.chunk_vectors):
            score = self._cosine(query_vec, vec)
            scored.append(RetrievalHit(chunk=chunk, score=score))

        scored.sort(key=lambda hit: hit.score, reverse=True)
        hits = scored[: max(top_k, 1)]
        LOGGER.info("Retrieved top %d chunks for query", len(hits))
        return hits


class AgentPlannerExecutor:
    """Selects a task mode and produces a grounded response with citations."""

    def run(self, query: str, hits: Sequence[RetrievalHit]) -> AgentResult:
        mode = self._detect_mode(query)
        top_hits = [hit for hit in hits if hit.score > 0.0]
        action_items = self._build_action_items(mode, top_hits)
        plan = [
            f"Detected mode: {mode}",
            "Use top retrieved evidence to ground the response",
            "Produce prioritized recommendations and cite sources",
            *[f"Action {idx + 1}: {item}" for idx, item in enumerate(action_items)],
        ]

        if not top_hits:
            answer = (
                "I could not find directly relevant evidence in the indexed files. "
                "Please provide more specific documents or query terms."
            )
            return AgentResult(plan=plan, answer=answer, citations=[], confidence=0.1)

        evidence_lines = []
        citations = []
        for hit in top_hits[:3]:
            snippet = hit.chunk.text[:180].strip()
            evidence_lines.append(f"- ({hit.score:.2f}) {snippet}")
            citations.append(hit.chunk.chunk_id)

        recommendation = self._build_recommendation(mode, query, top_hits)
        action_block = "\n".join(
            f"{idx + 1}. {item}" for idx, item in enumerate(action_items)
        )
        answer = (
            f"Mode: {mode}\n"
            f"Recommendation: {recommendation}\n"
            "Next Actions:\n"
            f"{action_block}\n"
            "Evidence:\n"
            + "\n".join(evidence_lines)
        )
        confidence = min(0.95, sum(hit.score for hit in top_hits[:3]) / 3 + 0.35)
        return AgentResult(plan=plan, answer=answer, citations=citations, confidence=confidence)

    def _detect_mode(self, query: str) -> str:
        q = query.lower()
        if any(k in q for k in ["deadline", "schedule", "week", "today", "plan"]):
            return "planning"
        if any(k in q for k in ["compare", "difference", "vs"]):
            return "comparison"
        if any(k in q for k in ["risk", "blocker", "issue"]):
            return "risk_review"
        return "summary"

    def _build_recommendation(
        self, mode: str, query: str, hits: Sequence[RetrievalHit]
    ) -> str:
        top_source = hits[0].chunk.source
        if mode == "planning":
            return (
                f"Prioritize the next actionable milestone from {Path(top_source).name}, "
                "then map tasks to a 1-week execution checklist with owners and due dates."
            )
        if mode == "comparison":
            return "Compare shared themes first, then highlight unique strengths and gaps per source."
        if mode == "risk_review":
            return "Rank risks by impact and urgency, then propose mitigations with explicit evidence links."
        return f"Provide a concise grounded summary for: {query}"

    def _build_action_items(self, mode: str, hits: Sequence[RetrievalHit]) -> List[str]:
        if not hits:
            return ["Provide more specific files or query terms to generate grounded actions."]

        candidate_sentences: List[str] = []
        for hit in hits[:3]:
            candidate_sentences.extend(re.split(r"[.!?]", hit.chunk.text))

        action_verbs = {
            "add",
            "build",
            "prioritize",
            "run",
            "record",
            "prepare",
            "test",
            "update",
            "include",
            "implement",
            "plan",
        }
        extracted: List[str] = []
        seen: set[str] = set()
        for sentence in candidate_sentences:
            cleaned = re.sub(r"\s+", " ", sentence).strip(" -\n\t")
            if not cleaned:
                continue
            lowered = cleaned.lower()
            if any(f" {verb} " in f" {lowered} " for verb in action_verbs):
                item = cleaned[0].upper() + cleaned[1:]
                if item not in seen:
                    extracted.append(item)
                    seen.add(item)
            if len(extracted) >= 3:
                break

        if extracted:
            return extracted

        if mode == "planning":
            return [
                "Define the top three deliverables for this week with clear owners.",
                "Convert each deliverable into a day-by-day checklist.",
                "Run a final validation pass and capture demo evidence.",
            ]
        if mode == "comparison":
            return [
                "List the shared points across top sources.",
                "Capture key differences with one sentence each.",
                "Recommend which option to prioritize and why.",
            ]
        if mode == "risk_review":
            return [
                "List the top risks by impact and urgency.",
                "Define one mitigation step per risk.",
                "Assign an owner and deadline for each mitigation.",
            ]

        return [
            "Summarize the top evidence in plain language.",
            "Extract two to three actionable decisions.",
            "Identify missing information needed for a stronger answer.",
        ]


class Evaluator:
    """Checks groundedness, mode consistency, and confidence thresholds."""

    def __init__(self, min_confidence: float = 0.4):
        self.min_confidence = min_confidence

    def evaluate(self, query: str, result: AgentResult) -> EvaluationResult:
        notes: List[str] = []
        groundedness_ok = bool(result.citations)
        if not groundedness_ok:
            notes.append("No citations present")

        mode_ok = "Mode:" in result.answer
        if not mode_ok:
            notes.append("Missing explicit mode in output")

        confidence_ok = result.confidence >= self.min_confidence
        if not confidence_ok:
            notes.append(
                f"Confidence below threshold ({result.confidence:.2f} < {self.min_confidence:.2f})"
            )

        passed = groundedness_ok and mode_ok and confidence_ok
        return EvaluationResult(
            passed=passed,
            groundedness_ok=groundedness_ok,
            mode_ok=mode_ok,
            confidence_ok=confidence_ok,
            notes=notes,
        )


class RepoFinderSystem:
    """Orchestrates ingestion -> retrieval -> agent -> evaluation -> fallback."""

    def __init__(self, chunk_size: int = 500, overlap: int = 80, top_k: int = 3):
        self.ingestion = IngestionParser(chunk_size=chunk_size, overlap=overlap)
        self.top_k = top_k
        self.evaluator = Evaluator()
        self.feedback_log: List[str] = []

    def run(self, query: str, file_paths: Sequence[str]) -> Dict[str, object]:
        LOGGER.info("Starting RepoFinder run")
        chunks = self.ingestion.ingest(file_paths)

        retriever = Retriever(chunks)
        hits = retriever.search(query, top_k=self.top_k)

        agent = AgentPlannerExecutor()
        result = agent.run(query, hits)
        evaluation = self.evaluator.evaluate(query, result)

        if not evaluation.passed:
            LOGGER.warning("Initial evaluation failed; attempting fallback repair")
            repaired_hits = retriever.search(query, top_k=max(self.top_k + 2, 5))
            repaired = agent.run(query, repaired_hits)
            repaired_eval = self.evaluator.evaluate(query, repaired)
            if repaired_eval.passed:
                result = repaired
                evaluation = repaired_eval
                hits = repaired_hits

        output = {
            "answer": result.answer,
            "plan": result.plan,
            "citations": result.citations,
            "confidence": round(result.confidence, 3),
            "evaluation": {
                "passed": evaluation.passed,
                "groundedness_ok": evaluation.groundedness_ok,
                "mode_ok": evaluation.mode_ok,
                "confidence_ok": evaluation.confidence_ok,
                "notes": evaluation.notes,
            },
            "retrieval_scores": [round(hit.score, 3) for hit in hits],
        }

        LOGGER.info("RepoFinder run complete; passed=%s", evaluation.passed)
        return output

    def submit_human_feedback(self, feedback: str) -> None:
        """Capture user verification feedback for iterative improvement."""
        cleaned = feedback.strip()
        if cleaned:
            self.feedback_log.append(cleaned)
            LOGGER.info("Stored human feedback item (%d total)", len(self.feedback_log))
