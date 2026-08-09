# Smart Circuit Reader

A small project testing whether an LLM (Gemini) can correctly **read** an
existing circuit, instead of only generating new ones.

## Why this project

Most LLM circuit work focuses on generating a circuit from a spec. Fewer
projects test whether the LLM can first read an existing circuit
correctly. If it cannot read a circuit right, it cannot fix or verify
it either. This project is a small, working version of that idea.

## How it works

1. `netlist_parser.py` reads a simple SPICE-style netlist file (`.net`)
   and builds a list of components and a map of which nodes connect to
   which parts. Plain Python, no AI involved here.
2. It also runs structural checks: is there a ground reference, are
   any nodes floating (connected to only one part), are there
   duplicate component names.
3. `circuit_analyzer.py` sends the parsed summary to Google Gemini and
   asks it to identify the circuit type, explain what it does, agree
   or disagree with the structural warnings, and predict a numeric
   value for the circuit.

## Sample circuits included

- `voltage_divider.net`: correct, simple resistive divider
- `rc_filter.net`: correct, first order RC low pass filter
- `broken_circuit.net`: intentionally broken, missing ground and a
  floating node, used to show the checker catching real problems

## Running it

Install the dependency: