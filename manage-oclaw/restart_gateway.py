#!/usr/bin/env python3
import os, sys
os.execv('/home/desazure/.openclaw/workspace/ops/watchdog/restart_gateway.py', ['/home/desazure/.openclaw/workspace/ops/watchdog/restart_gateway.py'] + sys.argv[1:])
