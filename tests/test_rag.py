from pathlib import Path
from types import SimpleNamespace

import pytest

import rag


class FakeVectorStore:
    def __init__(self) -> None:
        self.ids: set[str] = set()
        self.added_documents = []

    def get(self, ids: list[str]) -> dict[str, list[str]]:
        return {"ids": [document_id for document_id in ids if document_id in self.ids]}

    def add_documents(self, documents, ids: list[str]) -> None:
        self.added_documents.extend(documents)
        self.ids.update(ids)


def test_index_pdf_adds_chunks_once(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    pdf_path = tmp_path / "source.pdf"
    pdf_path.write_bytes(b"test pdf")
    vectorstore = FakeVectorStore()

    class FakeMarkItDown:
        def convert(self, _path: str) -> SimpleNamespace:
            return SimpleNamespace(text_content="Information security protects information.")

    monkeypatch.setattr(rag, "MarkItDown", FakeMarkItDown)
    monkeypatch.setattr(rag, "get_vectorstore", lambda: vectorstore)

    assert rag.index_pdf(pdf_path, source_name="source.pdf") == 1
    assert rag.index_pdf(pdf_path, source_name="source.pdf") == 0
    assert vectorstore.added_documents[0].metadata["source"] == "source.pdf"


def test_index_pdf_rejects_non_pdf(tmp_path: Path) -> None:
    file_path = tmp_path / "notes.txt"
    file_path.write_text("not a PDF", encoding="utf-8")

    with pytest.raises(ValueError, match="Only PDF"):
        rag.index_pdf(file_path)


def test_answer_question_uses_retrieved_context(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    document = SimpleNamespace(page_content="Information security protects information.")

    class FakeVectorStore:
        def as_retriever(self, *, search_kwargs: dict[str, int]) -> SimpleNamespace:
            assert search_kwargs == {"k": 3}
            return SimpleNamespace(invoke=lambda _question: [document])

    class FakeChatGroq:
        def __init__(self, **kwargs: object) -> None:
            assert kwargs == {
                "model": "openai/gpt-oss-20b",
                "temperature": 0,
                "api_key": "test-key",
            }

        def invoke(self, prompt: str) -> SimpleNamespace:
            assert "Information security protects information." in prompt
            return SimpleNamespace(content="It protects information.")

    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    monkeypatch.setattr(rag, "get_vectorstore", FakeVectorStore)
    monkeypatch.setattr(rag, "ChatGroq", FakeChatGroq)

    assert rag.answer_question(" What does it protect? ") == "It protects information."


def test_answer_question_requires_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GROQ_API_KEY", raising=False)

    with pytest.raises(RuntimeError, match="Missing GROQ_API_KEY"):
        rag.answer_question("A question")


def test_answer_question_rejects_blank_question() -> None:
    with pytest.raises(ValueError, match="Enter a question"):
        rag.answer_question("  ")
