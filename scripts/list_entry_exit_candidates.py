"""List candidate entry/exit edges for MVP-004's curated entry/exit list.

A one-off (re-runnable), read-only tool: prints car-capable edges that end at a
low-degree/dead-end junction — a proxy for "the MVP-002 coverage outline clipped through a
real road here" — sorted by speed (fastest/most-arterial-looking first), with their real
street name (from `netconvert --output.street-names`, see `simulator.network.build_network`)
so a human can pick the real ~10 entry/exit roads from the list. Writes nothing itself;
`apps/simulator/data/entry-exit-edges.json` is authored by hand from this output.

Usage:
    python scripts/list_entry_exit_candidates.py
"""

from __future__ import annotations

from pathlib import Path

import sumolib

REPO_ROOT = Path(__file__).resolve().parents[1]
NET_FILE = REPO_ROOT / "apps" / "simulator" / "data" / "network.net.xml"

# Junctions with this many or fewer incoming+outgoing edges are treated as low-degree —
# plausible dead-ends where the coverage outline cut through a real road.
MAX_JUNCTION_DEGREE = 2


def _is_low_degree(node) -> bool:
    return len(node.getIncoming()) + len(node.getOutgoing()) <= MAX_JUNCTION_DEGREE


def main() -> int:
    net = sumolib.net.readNet(str(NET_FILE))

    candidates = []
    for edge in net.getEdges():
        if not edge.allows("passenger"):
            continue
        if _is_low_degree(edge.getToNode()) or _is_low_degree(edge.getFromNode()):
            candidates.append(edge)

    candidates.sort(key=lambda e: e.getSpeed(), reverse=True)

    print(
        f"{len(candidates)} candidate entry/exit edges (car-capable, low-degree end):\n"
    )
    print(f"{'edge id':<20} {'speed (km/h)':>12} {'length (m)':>11}  street name")
    for edge in candidates:
        speed_kmh = round(edge.getSpeed() * 3.6)
        length_m = round(edge.getLength())
        name = edge.getName() or "(unnamed)"
        print(f"{edge.getID():<20} {speed_kmh:>12} {length_m:>11}  {name}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
