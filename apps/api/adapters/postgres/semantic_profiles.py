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


def semantic_definitions():
    """Explicit v2 definitions; never mutate registered historical version1."""
    definitions = generic_definitions()
    for definition in definitions:
        definition['version'] = 2
        descriptor = definition['property_schema']['properties']['descriptors']['items']
        descriptor['required'] = ['dimension', 'value', 'certainty', 'evidence_refs', 'review_state']
        descriptor['properties'].update(
            dimension={'type': 'string', 'enum': ['thematic', 'semantic_role']},
            evidence_refs={'type': 'array', 'items': {'type': 'integer'}},
            review_state={'type': 'string', 'enum': ['proposed', 'accepted', 'rejected']},
            name_candidate={'type': 'string', 'minLength': 1})
    return definitions


def register_semantic_profiles(repository):
    """Explicit trusted provisioning, isolated tests only until VPS gate approved."""
    with repository.connect() as c:
        version = c.execute('SELECT version_num FROM alembic_version').fetchone()['version_num']
        if version not in ('0004_projection_outbox', '0005_retire_legacy_category', '0006_owner_organization'):
            raise RuntimeError('Reviewed native schema required for semantic profile provisioning')
    repository.register_types(semantic_definitions())


def uum_definitions():
    """Approved UUM profiles, additive immutable version; explicit registration only."""
    from app.core.uum import PRIMARY_DIMENSIONS
    definitions = semantic_definitions()
    for definition in definitions:
        definition['version'] = 3
        definition['property_schema']['properties']['primary_dimension'] = {
            'type': 'object', 'required': ['value', 'certainty', 'evidence_refs', 'review_state'],
            'additionalProperties': False, 'properties': {
                'value': {'type': 'string', 'enum': list(PRIMARY_DIMENSIONS)},
                'certainty': {'type': 'string', 'enum': ['asserted', 'tentative']},
                'evidence_refs': {'type': 'array', 'items': {'type': 'integer'}},
                'review_state': {'type': 'string', 'enum': ['proposed', 'accepted', 'rejected']}}}
    return definitions


def register_uum_profiles(repository):
    """Trusted explicit provisioning; no VPS registration before cutover approval."""
    with repository.connect() as c:
        version = c.execute('SELECT version_num FROM alembic_version').fetchone()['version_num']
        if version not in ('0004_projection_outbox', '0005_retire_legacy_category', '0006_owner_organization', '0009_guest_invitations', '0010_context_consolidation'):
            raise RuntimeError('Reviewed native schema required')
    repository.register_types(uum_definitions())
