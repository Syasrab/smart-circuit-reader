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
import json
import hashlib

CACHE_FILE = "gemini_cache.json"
def _load_cache():
    if not os.path.exists(CACHE_FILE):
        return {}
    with open(CACHE_FILE, "r") as f:
        return json.load(f)


def _save_cache(cache):
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2)


def _cache_key(circuit_summary):
    # Turns the circuit text into a short fixed-length fingerprint.
    # If the circuit text changes even slightly, this fingerprint changes too,
    # so we correctly know to ask Gemini again.
    return hashlib.sha256(circuit_summary.encode()).hexdigest()

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
    cache = _load_cache()
    key = _cache_key(circuit_summary)

    if key in cache:
        print("[using cached Gemini answer, no API call made]")
        return cache[key]

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not found in environment variables.")

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-3.6-flash")

    prompt = PROMPT_TEMPLATE.format(summary=circuit_summary)
    response = model.generate_content(prompt)

    cache[key] = response.text
    _save_cache(cache)

    return response.text