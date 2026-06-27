"""Verified Jira ground truth for the LBVOICESER QA loop.

These are the exact status/label/issue-type/link strings and ids confirmed against live Jira
(see docs/ + the qa-loop ground-truth). Keep them here so nodes never hard-code magic strings.
Values that are project-specific default to the pilot (LBVOICESER) but are overridable via config.
"""
from __future__ import annotations

# --- statuses ---------------------------------------------------------------
STATUS_READY_FOR_TESTING = "Ready for testing"   # id 10015 — the loop trigger
STATUS_DONE = "Done"                              # id 10005 — Test card on all-pass
STATUS_OPEN = "Open"                              # id 1 — Test card on any failure
STATUS_IN_PROGRESS = "In Progress"                # set on the Test card when a run starts

# --- labels -----------------------------------------------------------------
LABEL_AUTO_GENERATED = "qa-auto-generated"        # terminal: always excluded from the fetch
LABEL_CONTEXT_REQUESTED = "qa-context-requested"  # awaiting author; kept in fetch, re-evaluated

# --- the sentinel that marks the bot's context-request comment --------------
# Must appear on its own line at the end of an insufficient-path comment. The re-eval gate keys
# off the `created` timestamp of the latest comment containing this string.
CONTEXT_REQUEST_SENTINEL = "[qa-auto:context-request]"

# --- issue types / links (Xray) ---------------------------------------------
ISSUE_TYPE_TEST = "Test"                          # id 10004 — Xray Test card
LINK_TYPE_TESTS = "Tests"                         # id 10007 — inward=Test card, outward=parent

# --- fetch ------------------------------------------------------------------
# Issue types the loop considers ready-for-testing candidates.
CANDIDATE_ISSUE_TYPES = ("Story", "Task")

# Fields the fetch needs (the enhanced search API returns only id/key unless asked).
FETCH_FIELDS = ("summary", "description", "status", "issuetype", "labels", "assignee",
                "comment", "updated")


def phase1_jql(project_key: str) -> str:
    """Timestamp-aware Phase-1 query: ready-for-testing Stories/Tasks, excluding only the
    terminal ``qa-auto-generated`` label so ``qa-context-requested`` tickets re-enter for re-eval.
    """
    types = ", ".join(CANDIDATE_ISSUE_TYPES)
    return (
        f'project = {project_key} AND status = "{STATUS_READY_FOR_TESTING}" '
        f'AND issuetype IN ({types}) '
        f'AND (labels IS EMPTY OR labels NOT IN ("{LABEL_AUTO_GENERATED}")) '
        f'ORDER BY updated DESC'
    )
