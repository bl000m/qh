"""Explicit schema provisioning, separate from startup and source interpretation."""

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps/api"))

from adapters.postgres.canonical import CanonicalRepository  # noqa: E402
from adapters.postgres.config import database_url  # noqa: E402
from adapters.postgres.semantic_profiles import register_generic_profiles, register_uum_profiles  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--register-generic-profiles", action="store_true")
    mode.add_argument("--register-uum-profiles", action="store_true")
    args = parser.parse_args()
    repository = CanonicalRepository(url=database_url(), subject_id="")
    if args.register_uum_profiles:
        # Cutover only: never reinterpret or upgrade existing application content.
        with repository.connect() as connection:
            connection.execute("SET LOCAL lock_timeout='5s'")
            connection.execute('LOCK TABLE context_spaces,owner_organization,sources,source_revisions,'
                'understanding_items,understanding_item_revisions,item_revision_types,item_revision_provenance,'
                'relation_revision_details,context_projection_state,projection_outbox IN SHARE MODE')
            if connection.execute('SELECT version_num FROM alembic_version').fetchone()['version_num'] != '0006_owner_organization':
                raise RuntimeError('UUM cutover requires the reviewed 0006 baseline')
            for table in ('context_spaces', 'owner_organization', 'sources', 'source_revisions',
                          'understanding_items', 'understanding_item_revisions', 'item_revision_types',
                          'item_revision_provenance', 'relation_revision_details',
                          'context_projection_state', 'projection_outbox'):
                if connection.execute('SELECT EXISTS(SELECT 1 FROM '+table+') AS present').fetchone()['present']:
                    raise RuntimeError('UUM cutover requires an empty application dataset')
            register_uum_profiles(repository)
        print('PASS: explicit UUM profile3 provisioning on empty 0006; no data conversion')
        return
    register_generic_profiles(repository)
    print(
        "PASS: qh.generic.item/1, entity/1, relation/1 registered or identical replay"
    )


if __name__ == "__main__":
    main()
