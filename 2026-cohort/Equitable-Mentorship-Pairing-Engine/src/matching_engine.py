"""
Equitable Mentorship Pairing Engine — matching prototype
Team Catalyst Strategists / MMC BUILD, SDG 5

Matches mentees to mentors using skill overlap, seniority gap, and mentor
capacity. Gender is tracked for equity reporting only — never used as a
matching input, per the team's data-privacy recommendation.

Usage:
    python matching_engine.py sample_mentees.csv sample_mentors.csv
"""

import csv
import sys
from dataclasses import dataclass, field

# Tunable weights — sum to 1.0
W_SKILLS = 0.5
W_SENIORITY = 0.3
W_CAPACITY = 0.2


@dataclass
class Person:
    id: str
    name: str
    skills: set
    seniority: int
    gender: str = "unspecified"
    capacity: int = 1
    remaining_capacity: int = field(init=False)

    def __post_init__(self):
        self.remaining_capacity = self.capacity


def load_people(path):
    people = []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            people.append(Person(
                id=row["id"],
                name=row["name"],
                skills=set(s.strip().lower() for s in row["skills"].split(",")),
                seniority=int(row["seniority_level"]),
                gender=row.get("gender", "unspecified") or "unspecified",
                capacity=int(row.get("capacity", 1)),
            ))
    return people


def skill_score(mentee, mentor):
    if not mentee.skills or not mentor.skills:
        return 0.0
    overlap = mentee.skills & mentor.skills
    union = mentee.skills | mentor.skills
    return len(overlap) / len(union)  # Jaccard similarity


def seniority_score(mentee, mentor):
    gap = mentor.seniority - mentee.seniority
    if gap <= 0:
        return 0.0  # mentor must be more senior
    return min(gap / 3, 1.0)  # gap of 3+ levels scores max


def capacity_score(mentor):
    if mentor.capacity == 0:
        return 0.0
    return mentor.remaining_capacity / mentor.capacity


def match_score(mentee, mentor):
    return (
        W_SKILLS * skill_score(mentee, mentor)
        + W_SENIORITY * seniority_score(mentee, mentor)
        + W_CAPACITY * capacity_score(mentor)
    )


def run_matching(mentees, mentors):
    results = []
    for mentee in mentees:
        scored = sorted(
            ((match_score(mentee, m), m) for m in mentors if m.remaining_capacity > 0),
            key=lambda x: x[0],
            reverse=True,
        )
        if not scored:
            results.append((mentee, None, 0.0))
            continue
        best_score, best_mentor = scored[0]
        best_mentor.remaining_capacity -= 1
        results.append((mentee, best_mentor, best_score))
    return results


def print_equity_summary(results):
    from collections import Counter
    pairs = Counter(
        (m.gender, mentor.gender if mentor else "unmatched")
        for m, mentor, _ in results
    )
    print("\n--- Equity summary (gender tracked, not used for matching) ---")
    for (mentee_g, mentor_g), count in pairs.items():
        print(f"  mentee={mentee_g:<12} mentor={mentor_g:<12} count={count}")


def main():
    if len(sys.argv) != 3:
        print("Usage: python matching_engine.py mentees.csv mentors.csv")
        sys.exit(1)

    mentees = load_people(sys.argv[1])
    mentors = load_people(sys.argv[2])
    results = run_matching(mentees, mentors)

    print("--- Matches ---")
    for mentee, mentor, score in results:
        mentor_label = mentor.name if mentor else "NO MATCH (capacity exhausted)"
        print(f"{mentee.name:<15} -> {mentor_label:<15} (score={score:.2f})")

    print_equity_summary(results)


if __name__ == "__main__":
    main()
