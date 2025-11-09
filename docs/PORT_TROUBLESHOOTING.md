# Port 8001 "Address Already in Use" - Troubleshooting

## Why This Happens

The "Address already in use" error typically occurs because:

1. **Uvicorn Reload Mode**: When `reload=True`, uvicorn spawns a parent process (watcher) and a child process (server). Killing only the parent leaves the child holding the port.

2. **Zombie Processes**: Sometimes processes don't fully terminate and remain in a zombie state.

3. **Port in TIME_WAIT**: After a process dies, the port can be in TIME_WAIT state for ~60 seconds.

## Solutions

### Quick Fix (Recommended)

```bash
# Kill all server processes
./scripts/kill_all_servers.sh

# Wait a moment, then start
sleep 2
./scripts/start_server.sh
```

### Manual Fix

```bash
# 1. Find all processes
pgrep -f "uvicorn|main.py"

# 2. Kill them all (including children)
pkill -9 -f "uvicorn|main.py"

# 3. Check port is free
lsof -i:8001

# 4. If still in use, wait 10 seconds for TIME_WAIT to clear
sleep 10

# 5. Start server
uv run python main.py
```

### Disable Reload Mode

To avoid this issue entirely, disable reload mode:

```bash
# Start without reload
RELOAD=false uv run python main.py

# Or edit main.py and set reload=False
```

### Use a Different Port

If port 8001 is persistently stuck:

```bash
# Edit .env file
API_PORT=8002

# Or override when starting
uv run uvicorn api.main:app --host 0.0.0.0 --port 8002
```

## Prevention

The updated `start_server.sh` script now:
- Kills parent and child processes
- Waits longer between kills
- Checks port is free before starting
- Provides clear error messages

## Check What's Using the Port

```bash
# See what process is using port 8001
lsof -i:8001

# See process tree (parent/child relationships)
pstree -p $(lsof -ti:8001)
```

## Still Not Working?

1. **Check for other services**: Maybe another app is using port 8001
   ```bash
   lsof -i:8001
   ```

2. **Wait for TIME_WAIT**: Ports can be reserved for ~60 seconds after process dies
   ```bash
   sleep 60
   ```

3. **Restart terminal/shell**: Sometimes shell keeps references to processes

4. **Use a different port**: Change to 8002, 8003, etc. in `config.py`

