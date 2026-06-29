"""Unit tests for the Jira REST backend — no network (httpx MockTransport).

Covers: ADF wrapping, the label/comment/transition request bodies, tenant + project-boundary
enforcement (structural isolation), search pagination, and error mapping.
Run:  cd engine && pytest   |   python tests/test_jira_rest_client.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import httpx
import pytest

from qa_agent.config import TenantConfig
from qa_agent.jira import adf
from qa_agent.jira.config import JiraConfig
from qa_agent.jira.rest_client import JiraError, JiraRestClient
from qa_agent.tenant import CrossTenantError, TenantContext

TCFG = TenantConfig(
    tenant_id="lbvoiceser",
    jira_base_url="https://x.atlassian.net",
    allowed_project_keys=("LBVOICESER",),
)
JCFG = JiraConfig(
    base_url="https://x.atlassian.net",
    email="qa@laerdal.com",
    api_token="tok",
    project_key="LBVOICESER",
    timeout_ms=30000,
)
TENANT = TenantContext("lbvoiceser")


def make_client(handler):
    transport = httpx.MockTransport(handler)
    return JiraRestClient(TCFG, JCFG, client=httpx.Client(transport=transport))


# ---------------------------------------------------------------- ADF
def test_adf_blank_lines_and_empty():
    doc = adf.from_plain_text("line1\nline2\n\npara2")
    assert doc["type"] == "doc" and doc["version"] == 1
    first = doc["content"][0]
    assert [n["type"] for n in first["content"]] == ["text", "hardBreak", "text"]
    assert doc["content"][1]["content"][0]["text"] == "para2"
    # blank input still yields a valid, non-empty doc
    assert adf.from_plain_text("")["content"][0]["content"][0]["text"] == " "


# ---------------------------------------------------------------- request bodies
def test_set_labels_builds_update_ops():
    seen: dict = {}

    def handler(req):
        seen.update(method=req.method, path=req.url.path, body=json.loads(req.content))
        return httpx.Response(204)

    make_client(handler).set_labels(
        TENANT, "LBVOICESER-1335", add=["qa-context-requested"], remove=["old"]
    )
    assert seen["method"] == "PUT"
    assert seen["path"] == "/rest/api/3/issue/LBVOICESER-1335"
    assert seen["body"] == {
        "update": {"labels": [{"add": "qa-context-requested"}, {"remove": "old"}]}
    }


def test_add_comment_wraps_in_adf():
    seen: dict = {}

    def handler(req):
        seen["body"] = json.loads(req.content)
        return httpx.Response(201, json={"id": "1"})

    make_client(handler).add_comment(TENANT, "LBVOICESER-1335", "hello\nworld")
    assert seen["body"]["body"]["type"] == "doc"


def test_create_issue_returns_key():
    def handler(req):
        body = json.loads(req.content)
        assert body["fields"]["project"]["key"] == "LBVOICESER"
        assert body["fields"]["issuetype"]["name"] == "Test"
        return httpx.Response(201, json={"key": "LBVOICESER-1340"})

    assert make_client(handler).create_issue(
        TENANT, "LBVOICESER", "Test", "[Automated] foo"
    ) == "LBVOICESER-1340"


def test_transition_body():
    seen: dict = {}

    def handler(req):
        seen.update(path=req.url.path, body=json.loads(req.content))
        return httpx.Response(204)

    make_client(handler).transition(TENANT, "LBVOICESER-1", "31")
    assert seen["path"] == "/rest/api/3/issue/LBVOICESER-1/transitions"
    assert seen["body"] == {"transition": {"id": "31"}}


# ---------------------------------------------------------------- isolation
def test_cross_tenant_rejected():
    client = make_client(lambda req: httpx.Response(200, json={}))
    with pytest.raises(CrossTenantError):
        client.get_issue(TenantContext("otherteam"), "LBVOICESER-1", ["summary"])


def test_project_boundary_rejected():
    client = make_client(lambda req: httpx.Response(200, json={}))
    with pytest.raises(CrossTenantError):
        client.add_comment(TENANT, "OTHER-1", "hi")


# ---------------------------------------------------------------- search + errors
def test_search_paginates():
    pages = [
        httpx.Response(200, json={"issues": [{"key": "LBVOICESER-1"}], "nextPageToken": "t2"}),
        httpx.Response(200, json={"issues": [{"key": "LBVOICESER-2"}]}),
    ]
    calls = {"n": 0}

    def handler(req):
        resp = pages[calls["n"]]
        calls["n"] += 1
        return resp

    issues = make_client(handler).search_jql(TENANT, "project = LBVOICESER", ["summary"])
    assert [i["key"] for i in issues] == ["LBVOICESER-1", "LBVOICESER-2"]
    assert calls["n"] == 2


def test_http_error_raises_jiraerror():
    client = make_client(lambda req: httpx.Response(401, text="Unauthorized"))
    with pytest.raises(JiraError) as excinfo:
        client.myself(TENANT)
    assert excinfo.value.status == 401


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
