import json
from pathlib import Path
import tempfile
import unittest
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from scripts.amend_qh51_poc_budget import amend,ENVELOPE

class Amendment(unittest.TestCase):
    def test_history_backup_identity_and_expiry_retained_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory);auth=p/'authorization.json';ledger=p/'ledger.json'
            receipt=dict(purpose='QH-45 interactive chat',owner_authorized=True,model='mistral-small-2603',development_account=dict(environment='development',subject_id='owner'),eur_per_usd_upper_bound='2',expires_at='unchanged',development_budget=dict(max_calls=100,max_usd='2.50',max_eur='5.00',eur_per_usd_upper_bound='2'))
            state=dict(blocked=False,max_calls=100,max_usd='2.50',calls=[dict(status='completed',observed_usd='.00041220')]);auth.write_text(json.dumps(receipt));ledger.write_text(json.dumps(state))
            self.assertTrue(amend(auth,ledger,p/'backup'));self.assertFalse(amend(auth,ledger,p/'backup'))
            updated=json.loads(ledger.read_text());self.assertEqual(updated['calls'],state['calls']);self.assertEqual(updated['max_usd'],'5.00');self.assertIsNone(updated['max_calls'])
            current=json.loads(auth.read_text());self.assertEqual(current['development_budget'],ENVELOPE);current.pop('development_budget');receipt.pop('development_budget');self.assertEqual(current,receipt)
            self.assertEqual(json.loads((p/'backup/ledger.before.private.json').read_text()),state)

    def test_blocked_or_pending_never_changes_ledger(self):
        for blocked,status in [(True,'failed'),(False,'pending')]:
            with tempfile.TemporaryDirectory() as directory:
                p=Path(directory);auth=p/'authorization.json';ledger=p/'ledger.json'
                auth.write_text(json.dumps(dict(purpose='QH-45 interactive chat',owner_authorized=True,model='mistral-small-2603',development_account=dict(environment='development'),eur_per_usd_upper_bound='2')))
                ledger.write_text(json.dumps(dict(blocked=blocked,calls=[dict(status=status)])));before=ledger.read_bytes()
                with self.assertRaises(AssertionError):amend(auth,ledger,p/'backup')
                self.assertEqual(ledger.read_bytes(),before)
