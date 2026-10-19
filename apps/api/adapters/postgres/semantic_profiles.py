"""Controlled generic profiles; no automatic registration from model output/startup."""

from copy import deepcopy

CONTENT_SCHEMA = {
    "type": "object",
    "required": ["text"],
    "properties": {
        "text": {"type": "string", "minLength": 1},
        "descriptors": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["value", "certainty"],
                "properties": {
                    "value": {"type": "string", "minLength": 1},
                    "certainty": {"type": "string", "enum": ["asserted", "tentative"]},
                },
                "additionalProperties": False,
            },
        },
        "properties": {"type": "object"},
    },
    "additionalProperties": True,
}


def generic_definitions():
    return [
        dict(
            type_id="qh.generic." + shape,
            version=1,
            structural_kind=shape,
            property_schema=deepcopy(CONTENT_SCHEMA),
            relation_rules={"mode": "any_registered"} if shape == "relation" else None,
        )
        for shape in ("item", "entity", "relation")
    ]


def register_generic_profiles(repository):
    """Trusted explicit provisioning; conflicting published definitions fail closed."""
    with repository.connect() as c:
        version = c.execute("SELECT version_num FROM alembic_version").fetchone()[
            "version_num"
        ]
        if version not in ("0004_projection_outbox", "0005_retire_legacy_category", "0006_owner_organization"):
            raise RuntimeError("Generic provisioning requires reviewed native semantic schema (0004/0005 or additive 0006)")
    repository.register_types(generic_definitions())
