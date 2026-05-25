#!/usr/bin/env python3
"""Model the PTP Best Master Clock Algorithm ranking."""

from __future__ import annotations

import argparse
from dataclasses import dataclass


@dataclass(frozen=True)
class ClockCandidate:
    name: str
    priority1: int
    clock_class: int
    clock_accuracy: int
    offset_scaled_log_variance: int
    priority2: int
    clock_identity: str

    def bmca_key(self) -> tuple[int, int, int, int, int, str]:
        return (
            self.priority1,
            self.clock_class,
            self.clock_accuracy,
            self.offset_scaled_log_variance,
            self.priority2,
            normalize_identity(self.clock_identity),
        )


def normalize_identity(identity: str) -> str:
    return "".join(character for character in identity if character.isalnum()).lower()


def parse_int(value: str) -> int:
    return int(value, 0)


def parse_candidate(value: str) -> ClockCandidate:
    fields = {}
    for item in value.split(","):
        if "=" not in item:
            raise argparse.ArgumentTypeError(f"candidate field {item!r} must use key=value")
        key, field_value = item.split("=", 1)
        fields[key.strip()] = field_value.strip()

    required = {
        "name",
        "priority1",
        "clockClass",
        "clockAccuracy",
        "offsetScaledLogVariance",
        "priority2",
        "clockIdentity",
    }
    missing = sorted(required - fields.keys())
    if missing:
        raise argparse.ArgumentTypeError(f"candidate is missing fields: {', '.join(missing)}")

    return ClockCandidate(
        name=fields["name"],
        priority1=parse_int(fields["priority1"]),
        clock_class=parse_int(fields["clockClass"]),
        clock_accuracy=parse_int(fields["clockAccuracy"]),
        offset_scaled_log_variance=parse_int(fields["offsetScaledLogVariance"]),
        priority2=parse_int(fields["priority2"]),
        clock_identity=fields["clockIdentity"],
    )


def default_candidates() -> list[ClockCandidate]:
    return [
        ClockCandidate(
            name="current-vm",
            priority1=128,
            clock_class=248,
            clock_accuracy=0xFE,
            offset_scaled_log_variance=0xFFFF,
            priority2=128,
            clock_identity="001c42.fffe.ee3f40",
        ),
        ClockCandidate(
            name="better-grandmaster",
            priority1=100,
            clock_class=248,
            clock_accuracy=0xFE,
            offset_scaled_log_variance=0xFFFF,
            priority2=128,
            clock_identity="001c42.fffe.aaaaaa",
        ),
        ClockCandidate(
            name="same-priority-better-class",
            priority1=128,
            clock_class=127,
            clock_accuracy=0xFE,
            offset_scaled_log_variance=0xFFFF,
            priority2=128,
            clock_identity="001c42.fffe.bbbbbb",
        ),
    ]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare PTP clock candidates using a BMCA-style key")
    parser.add_argument(
        "--candidate",
        action="append",
        type=parse_candidate,
        help=(
            "candidate fields as comma-separated key=value pairs. "
            "Example: name=gm1,priority1=128,clockClass=248,"
            "clockAccuracy=0xfe,offsetScaledLogVariance=0xffff,"
            "priority2=128,clockIdentity=001c42.fffe.ee3f40"
        ),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    candidates = args.candidate or default_candidates()
    ranked = sorted(candidates, key=lambda candidate: candidate.bmca_key())

    print("PTP BMCA ranking model")
    print("Lower values win at the first field that differs.")
    print()
    print(
        "rank name                       priority1 clockClass clockAccuracy "
        "offsetScaledLogVariance priority2 clockIdentity"
    )

    for rank, candidate in enumerate(ranked, start=1):
        print(
            f"{rank:04d} "
            f"{candidate.name:26s} "
            f"{candidate.priority1:9d} "
            f"{candidate.clock_class:10d} "
            f"0x{candidate.clock_accuracy:02x}          "
            f"0x{candidate.offset_scaled_log_variance:04x}                  "
            f"{candidate.priority2:9d} "
            f"{normalize_identity(candidate.clock_identity)}"
        )

    winner = ranked[0]
    print()
    print(f"selected_grandmaster: {winner.name}")
    print(f"selected_identity:    {normalize_identity(winner.clock_identity)}")


if __name__ == "__main__":
    main()
