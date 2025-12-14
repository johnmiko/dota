import json
from datetime import datetime
from json import JSONDecodeError
from logging import getLogger

logger = getLogger(__name__)


class RunTracker:
    def __init__(self, filename):
        self.filename = filename
        self.last_ran_dict = self.load_last_ran_dict()

    def update_file(self):
        def encode(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError

        with open(self.filename, "w") as f:
            json.dump(self.last_ran_dict, f, default=encode)

    def load_last_ran_dict(self):
        def decode(obj):
            for k, v in obj.items():
                if isinstance(v, str):
                    try:
                        obj[k] = datetime.fromisoformat(v)
                    except ValueError:
                        pass
            return obj

        try:
            with open(self.filename, 'r') as f:
                return decode(json.load(f))
        # FileNotFoundError will occur on first run
        # JSONDecodeError will occur if file is empty (can happen if there was an error, file was created but not populated)
        except (FileNotFoundError, JSONDecodeError) as e:
            logger.error(e)
            self.last_ran_dict = {"last_ran": datetime.now()}
            self.update_file()
            return self.last_ran_dict

    def should_run(self, key, run_every_x_hours):
        # should run based on dict
        try:
            last_ran_date = self.last_ran_dict[key]
        except KeyError:
            self.last_ran_dict[key] = datetime.now()
            self.update_file()
            logger.info(f'key not found, running {key}')
            return True
        utc_now = datetime.now()
        delta = utc_now - last_ran_date
        delta_seconds = delta.days * 3600 * 24 + delta.seconds
        delta_hours = round(delta_seconds / 3600, 1)
        will_run = delta_hours > run_every_x_hours
        if will_run:
            status = 'running'
        else:
            status = 'skipping'
        logger.info(f'last ran {delta_hours} hours ago, {status} {key}')
        return will_run
