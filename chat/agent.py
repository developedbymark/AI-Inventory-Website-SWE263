import json
import os

from google import genai

from .tools import TOOL_DECLARATIONS, TOOL_FUNCTIONS

MODEL = "gemini-3.8-flash"

SYSTEM_PROMPT = """You are an inventory and pricing assistant for a small warehouse.

You help the user check and update stock, and look up prices and costs, by calling the tools available to you.

Rules:
- Always use a tool to answer questions about stock. Never guess or rely on memory.
- For any price, cost, total or VAT question, use the pricing tools. Never do the arithmetic yourself; use calculate_cost and report its figures.
- If the user asks for a cost with VAT, pass the VAT percentage to calculate_cost.
- If a tool returns an error, explain the problem to the user in plain language.
- Before deleting an item entirely, make sure that is what the user meant.
- Keep your answers short and factual.
- Do not answer any question unrelated to inventory or pricing.
"""

MAX_STEPS = 5

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])


def run_agent(user_message, previous_interaction_id=None, verbose=False):
    """Send a message to the agent and run tools until it produces an answer."""

    interaction = client.interactions.create(
        model=MODEL,
        input=user_message,
        tools=TOOL_DECLARATIONS,
        system_instruction=SYSTEM_PROMPT,
        previous_interaction_id=previous_interaction_id,
    )

    for _ in range(MAX_STEPS):
        calls = [s for s in interaction.steps if s.type == "function_call"]

        if not calls:
            return interaction.output_text, interaction.id

        results = []
        for call in calls:
            function = TOOL_FUNCTIONS[call.name]
            output = function(**call.arguments)

            if verbose:
                print(f"  -> {call.name}({call.arguments}) = {output}")

            results.append({
                "type": "function_result",
                "name": call.name,
                "call_id": call.id,
                "result": [{"type": "text", "text": json.dumps(output)}],
            })

        interaction = client.interactions.create(
            model=MODEL,
            input=results,
            tools=TOOL_DECLARATIONS,
            system_instruction=SYSTEM_PROMPT,
            previous_interaction_id=interaction.id,
        )

    return "I got stuck working on that. Please try rephrasing.", interaction.id