"""Targeted two-account availability and ownership checks; no provider HTTP."""
import asyncio
from dataclasses import replace
import json

import pytest

from adapters.llm.session_config import PrivateSessionFactory
from app.api.chat_sessions import CapabilityOutput
from app.core.models import ContextSpaceNotFound
from app.policy.owner import OwnerPolicyService
from tests.test_development_ai import setup, answer
from tests.test_poc_memory import poc
from tests.test_chat_service import request


def test_ineligible_poc_account_has_valid_disabled_capabilities_without_spending(tmp_path, monkeypatch):
    ai, alice, _, _, calls, ledger, _, _ = setup(tmp_path, monkeypatch, answer)
    poc(ai, ledger)
    ai.chat.policy = OwnerPolicyService(owner_for=owned)
    async def run():
        bob = replace(alice, subject_id='bob', principal_id='b'*64)
        before = ledger.read_bytes()
        caps = CapabilityOutput.model_validate(await ai.capabilities(bob, request(subject_id='bob', context_id='bob-space')))
        assert not caps.automatic and not caps.enabled and caps.model is None
        assert caps.remaining_usd == '0' and caps.max_calls == 3
        assert ledger.read_bytes() == before and not calls
    asyncio.run(run())


async def owned(scope):
    return {'space': 'alice', 'bob-space': 'bob', 'other-space': 'other'}.get(scope)


def test_two_verified_accounts_share_factory_budget_but_never_private_spaces(tmp_path, monkeypatch):
    ai, alice, _, _, calls, ledger, _, _ = setup(tmp_path, monkeypatch, answer)
    poc(ai, ledger)
    path = ai.factory.authorization_path
    receipt = json.loads(path.read_text())
    receipt['additional_development_accounts'] = [dict(environment='development', subject_id='bob', principal_id='b'*64)]
    path.write_text(json.dumps(receipt))
    old = ai.factory
    ai.factory = PrivateSessionFactory(authorization_path=path, ledger_path=ledger, transport=old.transport, pricing=old.pricing)
    ai.chat.policy = OwnerPolicyService(owner_for=owned)
    bob = replace(alice, subject_id='bob', principal_id='b'*64)
    async def run():
        before = ledger.read_bytes()
        first = CapabilityOutput.model_validate(await ai.capabilities(alice, request()))
        second = CapabilityOutput.model_validate(await ai.capabilities(bob, request(subject_id='bob', context_id='bob-space')))
        assert first.enabled and second.enabled and first.automatic and second.automatic
        assert first.model == second.model == 'mistral-small-2603'
        assert first.remaining_usd == second.remaining_usd
        assert first.max_calls is second.max_calls is None
        for identity, query in [(bob, request(subject_id='bob')), (alice, request(context_id='bob-space'))]:
            with pytest.raises(ContextSpaceNotFound):
                await ai.capabilities(identity, query)
            with pytest.raises(ContextSpaceNotFound):
                await ai.respond(identity, query)
        wrong = replace(bob, principal_id='c'*64)
        caps = CapabilityOutput.model_validate(await ai.capabilities(wrong, request(subject_id='bob', context_id='bob-space')))
        assert not caps.enabled
        with pytest.raises(ContextSpaceNotFound):
            await ai.respond(wrong, request(subject_id='bob', context_id='bob-space'))
        assert not calls and ledger.read_bytes() == before
    asyncio.run(run())
