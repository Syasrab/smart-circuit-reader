"""
main.py

Runs the circuit reader on every .net file in the circuits/ folder.
"""
from circuit_analyzer import analyze_with_gemini
import glob
from netlist_parser import parse_netlist, build_circuit, circuit_summary_text


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
        try:
            result = analyze_with_gemini(circuit_summary_text(circuit))
            print(result)
        except Exception as e:
            print(f"[Gemini call failed: {e}]")
        print()

if __name__ == "__main__":
    run()