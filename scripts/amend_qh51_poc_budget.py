"""Owner-authorized 23-Oct POC envelope amendment; never runs at startup/CI.

Existing calls, identity, expiry and blocked/pending protections remain unchanged.
Run only with backend stopped; frontend stays running. Backups stay private.
"""
import argparse
from datetime import datetime,timezone
from decimal import Decimal
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess

ENVELOPE=dict(max_calls=None,max_usd='5.00',max_eur='10.00',eur_per_usd_upper_bound='2')


def amend(auth,ledger,backup):
    auth,ledger,backup=Path(auth),Path(ledger),Path(backup)
    backup.mkdir(mode=0o700,parents=True,exist_ok=True)
    assert backup.stat().st_mode & 0o077 == 0
    with ledger.open('r+') as stream:
        fcntl.flock(stream,fcntl.LOCK_EX)
        original=stream.read();state=json.loads(original);raw=auth.read_bytes();receipt=json.loads(raw)
        assert receipt['purpose']=='QH-45 interactive chat' and receipt['owner_authorized'] is True
        assert receipt['development_account']['environment']=='development' and receipt['model']=='mistral-small-2603'
        assert receipt['eur_per_usd_upper_bound']=='2' and not state['blocked']
        assert all(c['status'] in ('completed','failed') for c in state['calls']), 'Unsettled attempts require review'
        charges=[Decimal(c['observed_usd'] if 'observed_usd' in c else c['reserved_usd']) for c in state['calls']]
        assert all(v.is_finite() and v>=0 for v in charges) and sum(charges)<=Decimal('5.00')
        if receipt.get('development_budget')==ENVELOPE and state['max_calls'] is None and state['max_usd']=='5.00':
            return False
        assert receipt['development_budget']==dict(max_calls=100,max_usd='2.50',max_eur='5.00',eur_per_usd_upper_bound='2')
        for name,data in [('authorization.before.private.json',raw),('ledger.before.private.json',original.encode())]:
            fd=os.open(backup/name,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
            with os.fdopen(fd,'wb') as out:out.write(data);out.flush();os.fsync(out.fileno())
        state.setdefault('budget_amendments',[]).append(dict(time_utc=datetime.now(timezone.utc).isoformat(),
            authorization='Owner mandate 2026-10-23: EUR10 aggregate, no call/session micro ceilings',
            previous_ledger_sha256=hashlib.sha256(original.encode()).hexdigest(),previous_authorization_sha256=hashlib.sha256(raw).hexdigest(),
            previous_max_calls=state['max_calls'],previous_max_usd=state['max_usd'],calls_retained=len(state['calls']),**ENVELOPE))
        state.update(max_calls=None,max_usd='5.00');receipt['development_budget']=ENVELOPE
        # The application is stopped. On interruption, mixed metadata fails closed.
        stream.seek(0);json.dump(state,stream,indent=2);stream.truncate();stream.flush();os.fsync(stream.fileno())
        temp=auth.with_suffix('.amendment.tmp');fd=os.open(temp,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        with os.fdopen(fd,'w') as out:json.dump(receipt,out,indent=2);out.flush();os.fsync(out.fileno())
        temp.replace(auth)
        assert json.loads(ledger.read_text())['calls']==json.loads(original)['calls']
        return True


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--runtime',type=Path,required=True);parser.add_argument('--backup',type=Path,required=True);args=parser.parse_args()
    for name in ('qh-backend-1',):
        state=json.loads(subprocess.check_output(['docker','inspect',name],text=True))[0]['State']
        if state['Running']:raise SystemExit('Stop backend with guarded make dev-stop DEV_SERVICE=backend before amendment')
    changed=amend(args.runtime/'authorization.json',args.runtime/'ledger.json',args.backup)
    print(json.dumps(dict(amended=changed,max_eur='10.00',max_usd='5.00',max_calls=None,historical_calls_preserved=True)))


if __name__=='__main__':main()
