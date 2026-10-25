"""Only the disposable browser harness enables these explicit sharing bindings."""
import os
from adapters.sharing import SharingSettings
from app.bootstrap import create_runtime_app


def create_app():
    if (os.environ.get('QH_SHARING_BROWSER_TEST')!='1' or os.environ.get('QH11_BROWSER_TEST')!='1'
            or not os.environ.get('QH_NATIVE_GRAPH_NAMESPACE','').startswith('qh12-browser-')
            or os.environ.get('POSTGRES_HOST')!='postgres'
            or os.environ.get('POSTGRES_DB')!='qh'):
        raise RuntimeError('Explicit disposable sharing browser harness required')
    return create_runtime_app(guest_settings=SharingSettings(origin='https://localhost:5173',
        verifier_key=bytes.fromhex(os.environ['QH_SHARING_VERIFIER_KEY'])))
