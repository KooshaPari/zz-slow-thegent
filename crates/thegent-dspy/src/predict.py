from typing import Any

from .module import DSPyModule


class Predict(DSPyModule):
    """Predict module that wraps a thegent agent call."""

    def __init__(self, agent_role: str = "predictor", prompt_template: str = "{input}") -> None:
        super().__init__(name="Predict")
        self.agent_role = agent_role
        self.prompt_template = prompt_template

    def forward(self, input_data: str, context: dict[str, Any] | None = None) -> str:
        """Invoke a thegent agent to predict output for the given input.

        Args:
            input_data: The raw input string.
            context: Optional metadata/context dict.
        Returns:
            A string prediction. In a real deployment this would route through
            thegent's AgentRegistry.
        """
        prompt = self.prompt_template.format(input=input_data)
        return f"[thegent:{self.agent_role}] {prompt}"
