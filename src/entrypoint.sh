#!/bin/bash
set -e

# Create user if it doesn't exist
if ! id "app" &>/dev/null; then
  PUID=${PUID:-1000}
  PGID=${PGID:-1000}
  echo "=== Creating user app ${PUID}:${PGID} ==="
  groupadd app -g ${PGID}
  useradd app -m -u ${PUID} -g app
  chown -R app:app .
fi

# Launch app as user
exec gosu app streamlit run src/MyAnimeStats.py
