import random
from datetime import datetime
from threading import Lock

from app.extensions import db, socketio
from app.models.official import Official


_ACTIVE_STATUSES = {"active", "activo"}


def _is_status_active(status_value):
    if status_value is None:
        return False
    return str(status_value).strip().lower() in _ACTIVE_STATUSES


class OfficialTrackingService:
    def __init__(self):
        self._tracked_ids = set()
        self._lock = Lock()
        self._task_running = False

    def start_tracking(self, raw_ids, app):
        ids, invalid = self._normalize_ids(raw_ids)
        missing = []
        inactive = []
        missing_coords = []
        started = []

        for official_id in ids:
            official = Official.query.get(official_id)
            if official is None:
                missing.append(official_id)
                continue
            if not official.gps_active or not _is_status_active(official.status):
                inactive.append(official_id)
                continue
            if official.last_latitude is None or official.last_longitude is None:
                missing_coords.append(official_id)
                continue
            started.append(official_id)

        if started:
            with self._lock:
                self._tracked_ids.update(started)
                if not self._task_running:
                    self._task_running = True
                    socketio.start_background_task(self._tracking_loop, app)

        return {
            "started_ids": started,
            "ignored": {
                "missing": missing,
                "inactive": inactive,
                "missing_coords": missing_coords,
                "invalid": invalid,
            },
        }

    def stop_tracking(self, raw_ids):
        if not raw_ids:
            with self._lock:
                stopped = list(self._tracked_ids)
                self._tracked_ids.clear()
            return {
                "stopped_ids": stopped,
                "not_tracking": [],
                "invalid": [],
                "stopped_all": True,
            }

        ids, invalid = self._normalize_ids(raw_ids)
        stopped = []
        not_tracking = []

        with self._lock:
            for official_id in ids:
                if official_id in self._tracked_ids:
                    self._tracked_ids.remove(official_id)
                    stopped.append(official_id)
                else:
                    not_tracking.append(official_id)

        return {
            "stopped_ids": stopped,
            "not_tracking": not_tracking,
            "invalid": invalid,
            "stopped_all": False,
        }

    def _tracking_loop(self, app):
        with app.app_context():
            while True:
                with self._lock:
                    if not self._tracked_ids:
                        self._task_running = False
                        break
                    tracked_ids = list(self._tracked_ids)

                try:
                    officials = Official.query.filter(Official.id_official.in_(tracked_ids)).all()
                    updates = []
                    remove_ids = []

                    for official in officials:
                        if not official.gps_active or not _is_status_active(official.status):
                            remove_ids.append(official.id_official)
                            continue
                        if official.last_latitude is None or official.last_longitude is None:
                            continue

                        official.last_latitude += random.uniform(-0.0001, 0.0001)
                        official.last_longitude += random.uniform(-0.0001, 0.0001)
                        official.last_gps_update = datetime.utcnow()
                        updates.append(
                            {
                                "id_official": official.id_official,
                                "latitude": official.last_latitude,
                                "longitude": official.last_longitude,
                                "last_gps_update": official.last_gps_update.isoformat(),
                            }
                        )

                    if updates:
                        db.session.commit()
                        socketio.emit("official_tracking", {"officials": updates})

                    if remove_ids:
                        with self._lock:
                            for official_id in remove_ids:
                                self._tracked_ids.discard(official_id)
                except Exception:
                    db.session.rollback()
                    app.logger.exception("Official tracking loop failed")

                socketio.sleep(2)

    @staticmethod
    def _normalize_ids(raw_ids):
        ids = []
        invalid = []
        for value in raw_ids or []:
            try:
                ids.append(int(value))
            except (TypeError, ValueError):
                invalid.append(value)
        return ids, invalid
