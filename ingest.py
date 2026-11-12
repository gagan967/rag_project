from pathlib import Path

from rag import index_pdf


def main() -> None:
    pdf_path = Path("data/document.pdf")
    chunk_count = index_pdf(pdf_path)
    print(f"Indexed {chunk_count} new chunks from {pdf_path}.")


if __name__ == "__main__":
    main()
