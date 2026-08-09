"""
main.py

Runs the circuit reader on every .net file in the circuits/ folder.
For each circuit:
  1. Parse it and run structural checks (Python only)
  2. Send it to Gemini for analysis and a predicted value
  3. Run it through real LTspice simulation
  4. Compare Gemini's prediction to LTspice's real answer
"""

import glob

from netlist_parser import parse_netlist, build_circuit, circuit_summary_text
from circuit_analyzer import analyze_with_gemini
from ltspice_runner import run_ltspice, get_meas_lines, parse_measurements, parse_gemini_predictions, compare
import time

def run():
    circuit_files = sorted(glob.glob("circuits/*.net"))

    if not circuit_files:
        print("No .net files found in circuits/")
        return

    for path in circuit_files:
        print("=" * 60)
        print(f"Circuit file: {path}")
        print("=" * 60)

        components, measurements = parse_netlist(path)
        circuit = build_circuit(components, measurements)
        print(circuit_summary_text(circuit))
        print()

        print("--- Gemini analysis ---")
        gemini_text = None
        try:
            gemini_text = analyze_with_gemini(circuit_summary_text(circuit))
            print(gemini_text)
        except Exception as e:
            print(f"[Gemini call failed: {e}]")
        print()
        time.sleep(15)  # wait between circuits to avoid hitting Gemini's per-minute limit

        if circuit.measurements:
            print("--- LTspice comparison ---")
            try:
                log_path = run_ltspice(path)
                meas_lines = get_meas_lines(path)
                measured = parse_measurements(log_path, meas_lines)
                predicted = parse_gemini_predictions(gemini_text) if gemini_text else {}
                for line in compare(predicted, measured):
                    print(line)
            except Exception as e:
                print(f"[LTspice comparison failed: {e}]")
            print()


if __name__ == "__main__":
    run()