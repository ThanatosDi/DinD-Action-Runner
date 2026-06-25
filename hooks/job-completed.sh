#!/bin/sh
# ACTIONS_RUNNER_HOOK_JOB_COMPLETED
# Runner 在 job 完成後、容器銷毀前執行此腳本
# 清理 RUNNER_WORKDIR 下的工作目錄

if [ -n "$RUNNER_WORKDIR" ] && [ -d "$RUNNER_WORKDIR" ]; then
    echo "[job-completed hook] Cleaning up: $RUNNER_WORKDIR"
    rm -rf "$RUNNER_WORKDIR"
fi
