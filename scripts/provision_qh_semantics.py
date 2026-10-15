"""Explicit schema provisioning, separate from startup and source interpretation."""

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps/api"))

from adapters.postgres.canonical import CanonicalRepository  # noqa: E402
from adapters.postgres.config import database_url  # noqa: E402
from adapters.postgres.semantic_profiles import register_generic_profiles  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--register-generic-profiles", action="store_true", required=True
    )
    parser.parse_args()
    register_generic_profiles(CanonicalRepository(url=database_url(), subject_id=""))
    print(
        "PASS: qh.generic.item/1, entity/1, relation/1 registered or identical replay"
    )


if __name__ == "__main__":
    main()
