#!/usr/bin/python

import argparse
import json
import subprocess
import glob

from datetime import datetime
from wsgiref.simple_server import make_server
from os.path import basename

from yaml import safe_load
from prometheus_client import make_wsgi_app, Metric, REGISTRY


CONF = "/etc/prometheus/borg.yml"
PORT = 9099


class BorgCollector:
    def __init__(self, data):
        dirstoscan = []
        for dir in data["dirs"]:
            dirstoscan.extend(glob.glob(dir))

        self.dirs = dirstoscan

    def collect(self):
        cache_keys = {
            "total_csize": "Compressed size",
            "total_size": "Original size",
            "unique_csize": "Deduplicated size",
        }
        repo_keys = {"last_modified": "Last backup date"}

        for d in self.dirs:
            host = basename(d)
            data = json.loads(
                subprocess.check_output(
                    ["/usr/bin/borg", "info", d, "--json"], input=b"y"
                )
            )
            stats = data["cache"]["stats"]
            for key, desc in cache_keys.items():
                mkey = f"borg_{key}"
                metric = Metric(mkey, desc, "gauge")
                metric.add_sample(mkey, value=stats[key], labels={"host": host})
                yield metric

            repo = data["repository"]
            for key, desc in repo_keys.items():
                mkey = f"borg_{key}"
                metric = Metric(mkey, desc, "gauge")
                diff = datetime.now() - datetime.strptime(
                    repo[key], "%Y-%m-%dT%H:%M:%S.%f"
                )
                value = 0 if diff.days < 0 else diff.days
                metric.add_sample(mkey, value=value, labels={"host": host})
                yield metric


def main():
    parser = argparse.ArgumentParser(description="Borg exporter for Prometheus")
    parser.add_argument(
        "-p",
        "--port",
        help=f"exporter exposed port (default {PORT})",
        type=int,
        default=PORT,
    )
    parser.add_argument(
        "-c",
        "--conf",
        help=f"configuration file (default {CONF})",
        type=argparse.FileType("r"),
        default=CONF,
    )
    args = parser.parse_args()

    data = safe_load(args.conf)

    REGISTRY.register(BorgCollector(data))

    app = make_wsgi_app()
    httpd = make_server("", args.port, app)
    httpd.serve_forever()


if __name__ == "__main__":
    main()
