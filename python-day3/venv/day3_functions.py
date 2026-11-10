import re
import string


def count_words(text: str) -> int:
    """Count words separated by whitespace."""
    return len(text.split())


def count_sentences(text: str) -> int:
    """Estimate the number of sentences."""
    if not text.strip():
        return 0

    parts = re.split(r"[.!?]+", text)
    return len([part for part in parts if part.strip()])


def average_word_length(text: str) -> float:
    """Calculate the average word length."""
    words = [
        word.strip(string.punctuation)
        for word in text.split()
    ]
    words = [word for word in words if word]

    if not words:
        return 0.0

    return sum(len(word) for word in words) / len(words)


def analyze_text(text: str) -> dict[str, int | float]:
    """Return basic text statistics."""
    return {
        "word_count": count_words(text),
        "sentence_count": count_sentences(text),
        "average_word_length": round(average_word_length(text), 2),
    }


def main() -> None:
    text = input("Enter text: ")

    result = analyze_text(text)

    print("\nTEXT ANALYSIS")
    print("-" * 30)
    print(f"Words: {result['word_count']}")
    print(f"Sentences: {result['sentence_count']}")
    print(f"Average word length: {result['average_word_length']}")


if __name__ == "__main__":
    main()
  