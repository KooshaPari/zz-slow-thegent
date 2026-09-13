from collections.abc import Sequence

def extract(
    query: str,
    choices: Sequence[str],
    *,
    scorer: object = ...,
    processor: object = ...,
    limit: int = ...,
    score_cutoff: float = ...,
) -> list[tuple[str, float, int]]: ...
def extractOne(
    query: str,
    choices: Sequence[str],
    *,
    scorer: object = ...,
    processor: object = ...,
    score_cutoff: float = ...,
) -> tuple[str, float, int] | None: ...
