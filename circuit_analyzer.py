"""
circuit_analyzer.py

Sends the circuit summary to Gemini and asks it to:
1. Identify the circuit type
2. Explain what it does
3. Check if it agrees with our warnings
4. Predict a number for each measurement, so we can compare later
"""

import os
import google.generativeai as genai

PROMPT_TEMPLATE = """You are reviewing a circuit netlist for correctness, the way a hardware engineer would before running SPICE.

Here is the parsed circuit:

{summary}

Answer in exactly this format:

1. Circuit type: (one line)
2. What it does: (2-3 sentences, plain language, include the key formula if relevant)
3. Correctness check: (do you agree with the warnings above, if any. Point out anything missed)
4. Predicted values: for EACH line under "Measurements requested", calculate it by hand and output a line like:
PREDICTED <name> = <number> <unit>

If there are no measurements listed, skip step 4.
"""


def analyze_with_gemini(circuit_summary):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not found in environment variables.")

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-3.6-flash")

    prompt = PROMPT_TEMPLATE.format(summary=circuit_summary)
    response = model.generate_content(prompt)
    return response.text


if __name__ == "__main__":
    from netlist_parser import parse_netlist, build_circuit, circuit_summary_text

    components, measurements = parse_netlist("circuits/voltage_divider.net")
    circuit = build_circuit(components, measurements)
    summary = circuit_summary_text(circuit)

    result = analyze_with_gemini(summary)
    print(result)