"""Run every per-topic analysis: regenerates all figures + analysis/findings/*.json.

Each topic owns its own RNG (seeded to reproduce the original eda.py /
partner_eda.py draws), so the run order does not affect computed values.
"""
from __future__ import annotations

import cohort_overview
import demographics
import country_permanova
import predict_disease
import microbiome_pcoa
import differential_abundance
import cross_omics
import naive_baseline

TOPICS = [
    cohort_overview,
    demographics,
    country_permanova,
    predict_disease,
    microbiome_pcoa,
    differential_abundance,
    cross_omics,
    naive_baseline,
]


def main():
    for mod in TOPICS:
        print(f"\n========== {mod.__name__} ==========")
        mod.main()
    print("\nAll topics complete.")


if __name__ == "__main__":
    main()
