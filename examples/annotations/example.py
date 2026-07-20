from dataclasses import dataclass
from typing import Tuple

from skyweaver import Parcel, flow, input, node, output

# ============================================================================
# Parcels
# ============================================================================


@dataclass
class RawText(Parcel):
    text: str


@dataclass
class NormalizedText(Parcel):
    text: str


@dataclass
class Tokens(Parcel):
    words: list[str]


@dataclass
class Statistics(Parcel):
    word_count: int
    character_count: int


@dataclass
class ContainsPython(Parcel):
    value: bool


@dataclass
class Analysis(Parcel):
    word_count: int
    character_count: int
    contains_python: bool


@dataclass
class Report(Parcel):
    text: str


# ============================================================================
# Flow 1
# ============================================================================


@flow
class TextAnalysisFlow:

    def __init__(self, prefix: str):
        self.prefix = prefix

    @input
    def build_report(
        self,
        text: str,
    ) -> RawText:

        print("[receive]")

        return RawText(
            text=self.prefix + text,
        )

    @node
    def tokenize(
        self,
        raw: RawText,
    ) -> Tokens:

        print("[tokenize]")

        return Tokens(
            words=raw.text.split(),
        )

    @node
    def normalize(
        self,
        raw: RawText,
    ) -> NormalizedText:

        return NormalizedText(
            text=raw.text.lower(),
        )

    @node
    def contains_python(
        self,
        normalized: NormalizedText,
    ) -> ContainsPython:

        return ContainsPython(
            value="python" in normalized.text,
        )

    @node
    def statistics(
        self,
        tokens: Tokens,
    ) -> Statistics:

        print("[statistics]")

        return Statistics(
            word_count=len(tokens.words),
            character_count=sum(len(word) for word in tokens.words),
        )

    @node
    def merge(
        self,
        stats: Statistics,
        contains: ContainsPython,
    ) -> Analysis:

        print("[merge]")

        return Analysis(
            word_count=stats.word_count,
            character_count=stats.character_count,
            contains_python=contains.value,
        )

    @output
    def show(
        self,
        analysis: Analysis,
    ) -> Tuple[int, int, bool]:

        print("[output]")

        return (analysis.word_count, analysis.character_count, analysis.contains_python)


# ============================================================================
# Flow 2
# ============================================================================


@flow
class ReportFlow:

    @node
    def receive(
        self,
        analysis: Analysis,
    ) -> Report:

        print("[receive report]")

        print("[build_report]")

        return Report(
            text=(
                f"Words: {analysis.word_count}\n"
                f"Characters: {analysis.character_count}\n"
                f"Contains 'Python': {analysis.contains_python}"
            )
        )

    @output
    def show(
        self,
        report: Report,
    ) -> str:

        print("[output report]")

        return report.text


# ============================================================================
# Main
# ============================================================================


if __name__ == "__main__":

    print("=" * 72)
    print("Creating flows")
    print("=" * 72)

    analysis = TextAnalysisFlow("[A] ")
    report = ReportFlow()

    print()

    print("=" * 72)
    print("Binding ReportFlow to TextAnalysisFlow")
    print("=" * 72)

    # Both flows will now share the same Logistics runtime.
    report.bind(analysis)

    print()

    print("=" * 72)
    print("Executing TextAnalysisFlow")
    print("=" * 72)

    result = analysis("Python type annotations make reactive graphs elegant.")

    print()

    print("=" * 72)
    print("Executing ReportFlow")
    print("=" * 72)

    report_text = report()

    print()

    print("=" * 72)
    print("Final Report")
    print("=" * 72)

    print(report_text)

    report_text = report()
    print(report_text)
