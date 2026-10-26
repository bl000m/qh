"""Backend lifecycle for the native engine; no public routes or provider calls."""

import logging
import threading

from adapters.context.incremental import (
    IncrementalContextEngine,
    IncrementalProjector,
    ProjectionWorker,
)
from adapters.context.native import AuthorizedNativeContextService
from adapters.postgres.canonical import CanonicalRepository

LOG = logging.getLogger(__name__)


class NativeRuntime:
    def __init__(self, *, url, driver, policy, namespace, poll_seconds=0.5):
        self.url, self.driver, self.policy = url, driver, policy
        self.projector = IncrementalProjector(driver, namespace=namespace)
        self.poll_seconds = poll_seconds
        self.stop_event = threading.Event()
        self.thread = None
        self.last_error_type = None
        self.schema_version = None

    def repository(self, subject):
        return CanonicalRepository(
            url=self.url, subject_id=subject,
            connection_options="-c statement_timeout=5000 -c lock_timeout=5000",
        )

    def context_for(self, subject):
        return AuthorizedNativeContextService(
            policy=self.policy,
            engine=IncrementalContextEngine(self.repository(subject), self.projector),
        )

    def start(self):
        if self.thread is not None:
            raise RuntimeError("Native runtime already started")
        try:
            with self.repository("").connect() as c:
                self.schema_version = c.execute("SELECT version_num FROM alembic_version").fetchone()[
                    "version_num"
                ]
                if self.schema_version not in ("0004_projection_outbox", "0005_retire_legacy_category", "0006_owner_organization", "0009_guest_invitations", "0010_context_consolidation"):
                    raise RuntimeError("Native runtime requires migration 0004")
            self.driver.verify_connectivity()
            self.projector.initialize()
        except Exception:
            self.driver.close()
            raise
        self.stop_event.clear()
        self.thread = threading.Thread(target=self._run, name="qh-projection", daemon=True)
        self.thread.start()
        LOG.info("native_worker_started")

    def tick(self):
        # Trusted maintenance discovery reads queue/scope metadata only. Payload
        # access still goes through an owner-bound repository and SQL scope guard.
        with self.repository("").connect() as c:
            work = c.execute(
                """SELECT s.context_space_id, cs.owner_id FROM context_projection_state s
                JOIN context_spaces cs ON cs.id=s.context_space_id
                JOIN users u ON u.id=cs.owner_id
                JOIN projection_outbox o ON o.context_space_id=s.context_space_id
                  AND o.scope_version=s.applied_version+1
                WHERE s.desired_version>s.applied_version
                  AND cs.status='active' AND u.status='active'
                  AND ((o.state IN ('pending','failed') AND o.available_at<=clock_timestamp())
                    OR (o.state='processing' AND o.lease_until<clock_timestamp()))
                ORDER BY o.created_at LIMIT 64"""
            ).fetchall()
        for row in work:
            if self.stop_event.is_set():
                break
            worker = ProjectionWorker(
                self.repository(row["owner_id"]), self.projector,
                (row["context_space_id"],),
            )
            worker.run_once()
            if worker.last_error:
                self.last_error_type = type(worker.last_error).__name__
                LOG.warning("native_projection_failed error_type=%s", self.last_error_type)
        return len(work)

    def _run(self):
        while not self.stop_event.is_set():
            try:
                self.tick()
            except Exception as exc:
                self.last_error_type = type(exc).__name__
                LOG.warning("native_worker_poll_failed error_type=%s", self.last_error_type)
            self.stop_event.wait(self.poll_seconds)

    def stop(self):
        self.stop_event.set()
        if self.thread is not None:
            self.thread.join(timeout=30)
            if self.thread.is_alive():
                raise RuntimeError("Native worker shutdown timed out")
            self.thread = None
        self.driver.close()
        LOG.info("native_worker_stopped")
