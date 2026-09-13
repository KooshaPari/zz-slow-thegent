import random
from collections.abc import Callable


class Teleprompter:
    """Optimize prompts via hill-climbing paraphrasing."""

    def __init__(self, iterations: int = 3) -> None:
        self.iterations = iterations

    def _paraphrase(self, prompt: str) -> str:
        """Simple paraphrase: shuffle words or add prefixes."""
        words = prompt.split()
        if len(words) > 3:
            random.shuffle(words[1:-1])
        variants = [
            f"Please answer the following: {prompt}",
            f"In detail, {prompt.lower()}",
            f"Consider this carefully: {prompt}",
        ]
        return random.choice(variants)

    def optimize(self, prompts: list[str], metric: Callable[[str], float]) -> list[str]:
        """Optimize a list of prompts via hill-climbing.

        Args:
            prompts: List of prompt strings.
            metric: Callable that takes a prompt and returns a score.
        Returns:
            List of optimized prompts.
        """
        optimized = []
        for prompt in prompts:
            best = prompt
            best_score = metric(best)
            for _ in range(self.iterations):
                candidate = self._paraphrase(best)
                score = metric(candidate)
                if score > best_score:
                    best = candidate
                    best_score = score
            optimized.append(best)
        return optimized
