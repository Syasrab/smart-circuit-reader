"""
netlist_parser.py

Reads a netlist file and turns it into structured data:
- a list of components (name, type, nodes, value)
- a node map showing which components touch which wire
- a list of warnings for common wiring mistakes
- a list of .meas lines (measurement requests), used later to check
  answers from Gemini and LTspice against each other
"""

from dataclasses import dataclass
from collections import defaultdict

TYPE_NAMES = {
    "R": "Resistor",
    "C": "Capacitor",
    "L": "Inductor",
    "V": "Voltage Source",
}

GROUND_NAMES = {"0", "GND", "GROUND"}


@dataclass
class Component:
    name: str
    ctype: str
    nodes: list
    value: str = ""

    @property
    def type_name(self):
        return TYPE_NAMES.get(self.ctype, f"Unknown ({self.ctype})")


@dataclass
class Circuit:
    components: list
    node_map: dict
    warnings: list
    measurements: list


def parse_netlist(path):
    components = []
    measurements = []

    with open(path, "r") as f:
        lines = f.readlines()

    for raw_line in lines:
        line = raw_line.strip()

        if not line or line.startswith("*"):
            continue

        # keep .meas lines, they tell us what value to check later
        if line.upper().startswith(".MEAS"):
            measurements.append(line)
            continue

        # skip other command lines like .op, .ac, .end
        if line.startswith("."):
            continue

        parts = line.split()
        name = parts[0]
        ctype = name[0].upper()
        nodes = parts[1:3]

        rest = parts[3:]
        if rest and rest[0].upper() in ("DC", "AC") and len(rest) > 1:
            value = f"{rest[0]} {rest[1]}"
        else:
            value = " ".join(rest)

        comp = Component(name=name, ctype=ctype, nodes=nodes, value=value)
        components.append(comp)

    return components, measurements


def build_circuit(components, measurements):
    node_map = defaultdict(list)
    for comp in components:
        for node in comp.nodes:
            node_map[node].append(comp.name)

    warnings = []

    # check 1: is there a ground reference?
    has_ground = any(node in GROUND_NAMES for node in node_map)
    if not has_ground:
        warnings.append("No ground reference node found (expected '0' or 'GND').")

    # check 2: any node touched by only one part = dead end
    for node, comps in node_map.items():
        if len(comps) < 2 and node not in GROUND_NAMES:
            warnings.append(f"Node '{node}' only touches one part ({comps[0]}). Looks like a dead end.")

    # check 3: duplicate names
    names = [c.name for c in components]
    dupes = {n for n in names if names.count(n) > 1}
    for d in dupes:
        warnings.append(f"Component name '{d}' is used more than once.")

    return Circuit(
        components=components,
        node_map=dict(node_map),
        warnings=warnings,
        measurements=measurements,
    )
def circuit_summary_text(circuit):
    lines = ["Components:"]
    for c in circuit.components:
        lines.append(f"  {c.name} [{c.type_name}] nodes={c.nodes} value={c.value}")

    lines.append("\nNodes:")
    for node, comps in circuit.node_map.items():
        lines.append(f"  {node}: touched by {comps}")

    if circuit.warnings:
        lines.append("\nWarnings:")
        for w in circuit.warnings:
            lines.append(f"  - {w}")

    if circuit.measurements:
        lines.append("\nMeasurements requested:")
        for m in circuit.measurements:
            lines.append(f"  - {m}")

    return "\n".join(lines)

if __name__ == "__main__":
    components, measurements = parse_netlist("circuits/rc_filter.net")
    circuit = build_circuit(components, measurements)

    print("Components:")
    for c in circuit.components:
        print(f"  {c.name} {c.type_name} {c.nodes} {c.value}")

    print("\nNodes:")
    for node, comps in circuit.node_map.items():
        print(f"  {node}: {comps}")

    print("\nWarnings:")
    for w in circuit.warnings:
        print(f"  - {w}")

    print("\nMeasurements:")
    for m in circuit.measurements:
        print(f"  {m}")