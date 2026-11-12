import argparse

from rag import answer_question


def main() -> None:
    parser = argparse.ArgumentParser(description="Ask a question about indexed PDFs.")
    parser.add_argument(
        "question",
        nargs="?",
        default="What is information security?",
        help="Question to answer using the indexed PDF documents.",
    )
    args = parser.parse_args()
    print("Starting retrieval...")
    print("\nAnswer:")
    print(answer_question(args.question))


if __name__ == "__main__":
    main()
