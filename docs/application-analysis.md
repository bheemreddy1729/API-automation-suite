# Application & Workflow Analysis

> Source of truth for the Jira-driven QA automation loop. Reconciles the lead's
> deck (`docs/QA_Automation_Overview.pptx`), the demo doc
> (`docs/QA-Automation-Demo.md`), and **live Jira recon** of project `LBVOICESER`
> performed 2026-06-26. Where sources disagree, the **live Jira data wins** and is
> marked ✅.

---

## 1. Application under test — Laerdal TTS / Voice Service

A multi-tenant **Text-to-Speech / Voice Service**. Jira project **LBVOICESER**
("LBLR Voice Services", id `10105`).

| Aspect | Detail |
|---|---|
| Base URI (stage) | `https://stage-tts-api.laerdalblr.in` |
| Auth | Token-based. `POST /account/v1/token` returns a Bearer JWT for a tenant. |
| Core endpoint | `POST /tts/v1/tts` — synthesize speech; body `{voice, speechText}` → audio bytes (`application/octet-stream`). |
| Other endpoint (deck) | `GET /tts/v1/voice-configurations` — voices available to the calling tenant. |
| Multi-tenancy | Each token is scoped to a tenant id (e.g. `201`) with role / langCode / userId. Responses are tenant-scoped. |
| Gateway | KrakenD in front of downstream synthesis service (a 422 "dependent service is down" comes from here when the backend is unavailable). |

Existing automation: [`TtsPostApiTest`](../src/test/java/com/laerdal/api/tests/TtsPostApiTest.java)
covers the `POST /tts/v1/tts` cases, annotated `@XrayTest(key="LBVOICESER-1307")`.

---

## 2. The QA automation loop

**Streamlined entry points (preferred):** three simple commands drive it interactively:

| Command | Does |
|---|---|
| **`/qa-start`** | Fetch "Ready for testing" tickets → requirement gathering (context-check) → insufficient gets a Jira comment+label; sufficient gets a test plan written to `qa/plans/<KEY>-plan.md` and **opened in an editor tab** for review |
| **`/qa-approve`** | Read the plan back (applies your file edits / review notes / chat edits) → generate the Java test class → open it in a tab to verify/edit |
| **`/qa-run`** | Execute (`mvn test`) → open the Allure report → create + link the Xray Test card (`Tests`→parent) → post results to the card + update the parent |

`/ready-for-testing` remains the shared playbook (full phase detail) and can run the
whole flow end-to-end. Both gates (plan, script) support **approve / edit / reject**;
edits work via the opened file **or** chat.

The underlying phases (1,2,exec,update automatic; plan + script human-gated):

```
① Fetch        JQL: LBVOICESER Stories in "Ready for testing", excluding the done
               label qa-auto-generated (qa-context-requested is KEPT for re-eval)
② Context check  per ticket → SUFFICIENT | INSUFFICIENT
               re-eval gate: a qa-context-requested ticket is re-checked only when
               updated > its [qa-auto:context-request] comment.created.
               sufficient → drop label + proceed; still short → stay silent
③ Gate 1       AI drafts test-case table from ACs → QA approves/rejects plan
④ Gate 2       AI writes Java JUnit5/REST-Assured class → QA approves/rejects
   ⚠ INSUFFICIENT → post structured Jira comment, label qa-context-requested, skip
⑤ Run          ONE combined `mvn test` over all approved classes → Allure
⑥ Update Jira  label qa-auto-generated · transition ticket · on failure @-tag reporter
               + summary report to QA engineer
```

---

## 3. Reconciled decisions (the contradictions, resolved)

| # | Topic | Old demo doc | Lead's deck | Live Jira | **Decision** |
|---|---|---|---|---|---|
| 1 | Trigger status | "Ready for QA" | "Ready for testing" | **"Ready for testing"** (id 10015) exists; "Ready for QA" does not ✅ | **"Ready for testing"** |
| 2 | Trigger | `/ready-for-testing` | `start` (narration) | n/a | Slash command **`/ready-for-testing`** |
| 3 | Phases | 4 | 6 | n/a | **6** (deck adds combined run + Jira auto-update) |
| 4 | Create Xray Test cards in Jira? | No (annotations only) | No (annotations only) | 1307 is a pre-existing Test issue | **YES — user override 2026-06-26** — create an Xray Test card per feature, link it to the parent via the `Tests` link type, set `@XrayTest(key=<new card>)`, and publish run results to the card. (Supersedes the deck's "annotations only".) |
| 5 | Labels | `qa-auto-generated`, `qa-context-requested` | "labelled" | `qa-context-requested` observed on LBVOICESER-1076 ✅ | both labels |
| 6 | Run granularity | per-ticket `mvn test` | one combined run | n/a | **one combined `mvn test`** after all gates |

---

## 4. Mandatory Jira fields for SUFFICIENT (context-check gate)

Required on ALL tickets: **Summary, Description, ≥1 testable Acceptance Criterion,
HTTP Method, Endpoint Path**. Method-specific extra:

| Method | Extra required |
|---|---|
| GET | sample response body |
| POST / PUT / PATCH | request body example OR API-docs link |

**Data shape (from live recon):** there are **no dedicated Jira custom fields** for
HTTP method / endpoint / body — Stories carry `description: null` by default, so the
context-check must parse method/endpoint/body/ACs out of **free-text** the QA author
adds to the Description/AC fields. Tickets lacking them go down the INSUFFICIENT path.

---

## 5. Live Jira state observed 2026-06-26 (for the demo)

- cloudId `86a735d2-77c1-49d1-a610-0f381e05ed90`; site `laerdal.atlassian.net`;
  scopes `read:jira-work` + `write:jira-work`.
- Statuses in project: Open(1), Reopened(4), **Ready for testing(10015)**, Done(10005), Closed(6).

### Requirement tickets are Story **OR Task**
The prepared demo tickets are issuetype **Task** (id 10011), not Story. The Phase 1 JQL
MUST use `issuetype IN (Story, Task)` or it returns nothing. (Earlier `LBVOICESER-1076`
was a Story; both types occur.)

### The 3-ticket demo set (prepared by the lead; all Task / Ready for testing / unlabeled / assignee Pruthvi Kumar Reddy / reporter Bhimrao Dadannavar)
| Key | Summary | Verdict | Branch demonstrated |
|---|---|---|---|
| **1330** | TTS POST API | SUFFICIENT — POST `/tts/v1/tts`, ACs all expect 400 for missing fields (correct) | **Green run** → all pass → label `qa-auto-generated` |
| **1335** | TTS STREAM POST API | SUFFICIENT — POST `/tts/v1/tts-stream`, ACs #3/#4 expect **200** for missing fields (API actually returns 400) | **Run finds a real bug** → 2 failures → failure comment @-tagging the **reporter** |
| **1334** | GET API CONFIGURATION | INSUFFICIENT — `description: null` | **Context-request** → comment to the **assignee** + label `qa-context-requested` |

Prior run (2026-06-25) already executed this set once: 1335 and 1334 still carry their
prior comments; 1330 is clean. Labels were reset to empty so the loop re-processes them.
Insufficient comments address the **assignee**; failure comments @-tag the **reporter**.

- `LBVOICESER-1076` (Story) also sits in *Ready for testing* labeled `qa-context-requested`
  from the 2026-06-18 run. It is now **fetched** (no longer excluded) but the Phase 2-B
  timestamp gate skips it silently until its `updated` exceeds its `[qa-auto:context-request]`
  comment's `created` — i.e. until the author actually edits it.

---

## 5b. Xray Test-card traceability (user override, 2026-06-26)

The loop now creates Jira-native traceability after Gate 2:

1. **Create** an Xray **Test** issue (issuetype id `10004`) per feature. Create-meta
   confirms only **Project + Summary + Issue Type** are mandatory — no required Xray
   "Test Type" field — so `createJiraIssue` succeeds with summary + description alone.
2. **Link** it to the parent with link type **`Tests`** (id `10007`,
   *tests* / *tested by*): `createIssueLink(type="Tests", inwardIssue=<TestCard>,
   outwardIssue=<parent>)` ⇒ parent "is tested by" the card.
3. **Annotate** the Java with `@XrayTest(key=<TestCard>)` + `@Requirement({<parent>})`.
4. **Publish** run results as a comment on the Test card (counts, per-method, Allure
   path). Execution is **human-triggered** (Phase 6), not auto.

Constraint: there is **no delete-issue MCP tool** — created Test cards can only be
closed/transitioned or deleted in the Jira UI. Create one per feature; reuse if a
`Tests`-linked `[Automated]` card already exists. Driven by `.claude/prompts/test-card.md`.

## 6. What gets generated (test class contract)

Follows existing patterns. Every generated class includes:
- Happy path derived from the Acceptance Criteria
- Auth failure (no token → ≥ 400, typically 401/403)
- Response-time guard (≤ configured timeout)
- `@Feature`, `@Requirement({"<KEY>"})`, `@XrayTest(key="<KEY>")`, `@DisplayName`

---

## 7. Roadmap (deck "Coming soon")

Webhook auto-trigger on ticket move · GitHub Actions runs the agent · MS Teams
adaptive cards for the two approval gates · results published to a Teams channel.
