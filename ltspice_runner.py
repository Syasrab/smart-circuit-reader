"""
ltspice_runner.py

Runs a netlist through LTspice in batch mode (no popup window),
then reads the .log file it produces to pull out measured values.
Also compares those real values against Gemini's predictions.
"""

import subprocess
import os
import re

LTSPICE_PATH = r"C:\Users\sarah\AppData\Local\Programs\ADI\LTspice\LTspice.exe"


def run_ltspice(net_path):
    result = subprocess.run(
        [LTSPICE_PATH, "-b", net_path],
        capture_output=True,
        text=True,
        timeout=60,
    )

    log_path = os.path.splitext(net_path)[0] + ".log"

    if not os.path.exists(log_path):
        raise RuntimeError(f"No .log file was created. LTspice output: {result.stdout} {result.stderr}")

    return log_path


def get_meas_lines(net_path):
    """Reads the .meas lines directly from the netlist file, so we know
    which measurements are FIND type vs WHEN type."""
    lines = []
    with open(net_path, "r") as f:
        for line in f:
            if line.strip().upper().startswith(".MEAS"):
                lines.append(line.strip())
    return lines


def parse_measurements(log_path, meas_lines=None):
    """Reads the .log file and pulls out {name: value} for each .meas result.

    FIND-type lines look like:   'vout: V(OUT)=2.5 at 5'              -> we want 2.5 (right after '=')
    WHEN-type lines look like:   'f3db: mag(V(OUT))=0.7071 AT 159.16' -> we want 159.16 (right after 'AT')
    """
    meas_lines = meas_lines or []
    when_names = set()
    for m in meas_lines:
        parts = m.split()
        if "WHEN" in m.upper() and len(parts) > 2:
            when_names.add(parts[2].lower())

    measured = {}
    at_pattern = re.compile(r"^(\w+):.*?\bAT\s+(-?\d+\.?\d*(?:[eE][-+]?\d+)?)", re.IGNORECASE)
    eq_pattern = re.compile(r"^(\w+):\s*.*?=\s*(-?\d+\.?\d*(?:[eE][-+]?\d+)?)")

    with open(log_path, "r", errors="ignore") as f:
        for line in f:
            stripped = line.strip()
            name_match = re.match(r"^(\w+):", stripped)
            if not name_match:
                continue
            name = name_match.group(1).lower()

            if name in when_names:
                match = at_pattern.match(stripped)
            else:
                match = eq_pattern.match(stripped)

            if match:
                measured[name] = float(match.group(2))

    return measured


def parse_gemini_predictions(gemini_text):
    """Pulls {name: value} out of lines like 'PREDICTED vout = 2.5 V'."""
    predicted = {}
    pattern = re.compile(r"PREDICTED\s+(\w+)\s*=\s*(-?\d+\.?\d*(?:[eE][-+]?\d+)?)", re.IGNORECASE)
    for match in pattern.finditer(gemini_text):
        predicted[match.group(1).lower()] = float(match.group(2))
    return predicted


def compare(predicted, measured, tolerance_pct=5.0):
    """Compares Gemini's predictions to LTspice's real measured values."""
    lines = []
    all_names = set(predicted) | set(measured)
    if not all_names:
        return ["No measurements to compare."]

    for name in sorted(all_names):
        p = predicted.get(name)
        m = measured.get(name)
        if p is None:
            lines.append(f"  {name}: LTspice measured {m}, Gemini gave no prediction")
        elif m is None:
            lines.append(f"  {name}: Gemini predicted {p}, LTspice result not found")
        else:
            diff_pct = abs(p - m) / abs(m) * 100 if m != 0 else float("inf")
            status = "MATCH" if diff_pct <= tolerance_pct else "MISMATCH"
            lines.append(f"  {name}: Gemini predicted {p}, LTspice measured {m} ({diff_pct:.1f}% difference) -> {status}")

    return lines


if __name__ == "__main__":
    net_path = "circuits/noninverting_amp.net"
    log_path = run_ltspice(net_path)
    meas_lines = get_meas_lines(net_path)
    measured = parse_measurements(log_path, meas_lines)
    print("Measured values:", measured)