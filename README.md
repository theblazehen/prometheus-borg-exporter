# Prometheus Borg Exporter

A very simple Borg exporter for Prometheus. This exporter is mostly useful for
getting the days since the last backup was made and the sizes of the backups in
total.

# Dependencies

* python
* prometheus_client

# Usage

Run the exporter

  python prometheus-borg-exporter.py

The default port is 9099, visit metrics [http://localhost:9099/ http://localhost:9099/].

# Configuration

The backup directory's can be configured in borg.yml with the backups
directories in the 'dirs' list. The metrics use the basename of the directory
as the "backup host".

# Example Promethues AlertManager rule

```yaml
  - name: backup
  interval: 60s
  rules:
  - alert: backup
    expr: borg_last_modified > 5
    for: 20m
    labels:
      severity: warning
    annotations:
      description: 'host {{ $labels.instance }} has outdated backups'
      summary: '{{ $labels.instance }} backups are {{ $value }} days old'
```

# Not implemented

There is no support for decrypting the backups.
