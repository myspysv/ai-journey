def count_words(text: str) -> int:
    return len(text.split())

def count_sentences(text: str) -> int:
    num_symbols = text.count(".") + text.count("?") + text.count("!")
    if num_symbols == 0:
        if text == "":
            return 0
        return 1
    return num_symbols

def average_word_length(text: str) -> float:
    words = text.split()
    if not words:
        return 0.0
    lengths = [len(word.strip(".,!?")) for word in words]
    return round((sum(lengths) / len(words)), 2)

def analyze_text(text: str) -> dict[str, int | float]:
    words = count_words(text)
    sentences = count_sentences(text)
    avg_word_length = average_word_length(text)
    return {
        "words": words,
        "sentences": sentences,
        "avg_word_length": avg_word_length
    }

print(analyze_text("The morning sun slowly rises over the quiet town. " \
"Birds sing brightly in the tall green trees. " \
"Sarah walks down the street with a warm cup of coffee in her hand. " \
"She smiles at her neighbor and waves hello. " \
"A gentle breeze blows through the park as the city begins to wake up. " \
"Today feels like the start of a wonderful adventure."))