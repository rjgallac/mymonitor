# Local Setup

python -m venv .venv

source .venv/Scripts/activate
# OR
# source .venv/bin/activate

pip install -r requirements.txt

python agent.py

# Docker Setup

## Build the Image
Run the following command from the `agent` directory:

```bash
docker build -t mymonitor-agent .
```

## Run the Container (Standard Mode)
Use this mode to monitor a specific container or a lightweight isolated environment. You must point the agent to your Central Server's address.

```bash
docker run -e SERVER_URL="http://host.docker.internal:8000/report" mymonitor-agent
```

## Run the Container (Host-Aware Mode)
Use this mode if you want the agent to bypass container isolation and report on the **actual hardware statistics of the host machine**. 

**Warning:** This mode requires elevated privileges and breaks standard container isolation.

```bash
docker run -e SERVER_URL="http://host.docker.internal:8000/report" \
  --pid=host \
  --network=host \
  -v /proc:/host/proc:ro \
  -v /sys:/host/sys:ro \
  mymonitor-agent
```

*Note: If you are on Linux, you may also need to add `--add-host=host.docker.internal:host-gateway` if you aren't using `--network=host`.*
