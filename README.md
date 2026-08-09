# Smart Circuit Reader

A small research project testing whether a large language model (Gemini) can correctly **read an existing circuit**, not just generate a new one.

## Why this project exists

Most LLM research in circuit design focuses on generating new circuits from a text description. Far fewer projects test whether an LLM can first read an existing circuit correctly, work out what it does, and predict its behavior. If a model cannot read a circuit right, it cannot fix, verify, or improve it either.

This project builds a small, working, and fully automated pipeline to test exactly that, using real circuits and a real SPICE simulator as ground truth, not just the model grading its own answers.

## How it works

Every circuit goes through three independent layers of checking:

**1. Structural check (pure Python, no AI)**
`netlist_parser.py` reads a `.net` file, lists every component and which wires (nodes) it touches, and checks for basic wiring mistakes: missing ground reference, dead-end (floating) nodes, duplicate component names.

**2. AI analysis (Gemini)**
`circuit_analyzer.py` sends the parsed circuit to Google Gemini and asks it to identify the circuit type, explain what it does in plain language with the correct formula, agree or disagree with the structural warnings, and predict a specific numeric value for the circuit (a voltage, a cutoff frequency, etc).

**3. Ground truth check (real LTspice simulation)**
`ltspice_runner.py` runs the same circuit through LTspice in batch mode on the local machine, extracts the real simulated value, and compares it against Gemini's prediction with a percent difference and a match/mismatch verdict.

`main.py` runs all three layers on every circuit automatically.

## Project structure
smart_circuit_reader/
├── circuits/ sample .net circuit files
├── netlist_parser.py reads a netlist, checks wiring, no AI
├── circuit_analyzer.py sends circuit to Gemini, caches responses
├── ltspice_runner.py runs real LTspice simulation, extracts results
├── main.py runs the full pipeline on every circuit
├── gemini_cache.json auto-generated, stores Gemini answers to save API quota
└── requirements.txt
## Sample circuits

**Passive circuits**

| File | What it is | Expected value |
|---|---|---|
| `voltage_divider.net` | Simple two-resistor divider | 2.5 V |
| `rc_filter.net` | RC low-pass filter | 159.15 Hz cutoff |
| `rc_highpass.net` | RC high-pass filter, same values, reversed topology | 159.15 Hz cutoff (tests if the model confuses high-pass with low-pass) |
| `two_stage_filter.net` | Two cascaded low-pass stages with a buffer between them | ~102 Hz cutoff, not 159.15 Hz (tests if the model just repeats the single-stage formula) |
| `wheatstone_bridge.net` | Balanced resistor bridge | 0 V (tests if the model assumes "more parts means a more complex answer") |

**Op-amp circuits** (modeled with an ideal high-gain dependent source, no external model files needed)

| File | What it is | Expected value |
|---|---|---|
| `noninverting_amp.net` | Non-inverting amplifier | Gain = 1 + R2/R1 = 10 |
| `inverting_amp.net` | Inverting amplifier | Gain = -R2/R1 = -9 (tests if the model catches the sign flip) |
| `voltage_follower.net` | Unity gain buffer | Output exactly equals input |

**Broken circuits** (used to test error detection)

| File | The problem | Category |
|---|---|---|
| `broken_circuit.net` | Missing ground reference, one floating node | Wiring error, caught by the Python structural check |
| `short_circuit.net` | A 0-ohm resistor placed directly across the voltage source | Value error, NOT caught by the structural check, since the wiring itself is technically valid |

## Results so far

All real LTspice simulations matched hand-calculated expected values. Where Gemini's prediction was available, it also matched LTspice within 0.1 percent:

| Circuit | Predicted | LTspice measured | Result |
|---|---|---|---|
| Voltage divider | 2.5 V | 2.5 V | Match |
| RC low-pass | 159.15 Hz | 159.16 Hz | Match |
| RC high-pass | 159.15 Hz | 159.23 Hz | Match |
| Two-stage filter | ~102 Hz | 102.31 Hz | Match |
| Non-inverting amp | 10 V | 9.9999 V | Match |
| Inverting amp | -9 V | -8.9999 V | Match |
| Voltage follower | 3 V | 2.9999 V | Match |
| Wheatstone bridge | 0 V | 0.0 V | Match |

**Notable result:** on the non-inverting amp circuit, the Python structural checker raised a false warning about a "floating" node, because it does not fully understand multi-terminal components. Gemini correctly identified that the checker was wrong and explained exactly why. This is direct evidence that an LLM can, in some cases, read a circuit more accurately than a simple rule-based checker.

On the short-circuit test, Gemini correctly identified the 0-ohm resistor as a fatal error that would cause a real SPICE simulation to fail, an error type the structural checker cannot detect at all, since it only checks wiring, not component values.

## Setup

Install the one Python dependency:
pip install google-generativeai


Set your Gemini API key as an environment variable named `GEMINI_API_KEY`.

Make sure LTspice is installed, and update the `LTSPICE_PATH` variable at the top of `ltspice_runner.py` to match your install location.

## Running it

python main.py


This runs every `.net` file in `circuits/` through all three layers and prints a full report.

## Gemini response caching

Gemini's free tier has strict daily and per-minute request limits. To avoid wasting quota by asking the same question twice, every Gemini response is saved to `gemini_cache.json`, keyed by a fingerprint of the circuit's exact content. If a circuit has not changed, `main.py` reuses the saved answer instead of calling the API again. Delete `gemini_cache.json` to force fresh answers.

**Note on rate limits:** free-tier Gemini models can allow as few as 20 requests per day. `main.py` pauses briefly between circuits to avoid the per-minute limit. If you hit the daily limit, cached results still work, new ones will need to wait for the quota to reset.

## Known limitations

- The structural parser does not fully understand multi-terminal components (like the op-amp model `E1`), which can produce false "floating node" warnings. Left as-is currently, since it produced a genuinely useful result (see above).
- Only Gemini is currently tested. Comparing multiple LLMs on the same circuits is a planned next step.
- The op-amp circuits use an ideal model (a high-gain dependent source), not a real op-amp part number, which keeps the demo simulation-file free but is a simplification.

## Research context and next steps

This project sits in the "LLM reads an existing circuit" category of ongoing research (related to AMSbench, GENIE-ASI, AnalogCoder-Pro), which is a smaller but still active area compared to circuit generation. The specific angle here, testing purely on text netlists (not schematic images), and automatically verifying numeric predictions against a real simulator rather than just checking topology labels, does not appear to be directly covered by current published work.

Planned next steps:
- Compare multiple LLMs (Gemini, GPT, Claude) on the same circuit set, tracking accuracy percentage per model
- Expand the circuit set further, including harder multi-stage and mixed-signal cases
- Report results as a small quantitative benchmark suitable for a short paper

