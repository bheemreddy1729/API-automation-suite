package com.laerdal.api.jira;

import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.junit.jupiter.api.Assumptions.assumeTrue;

import com.fasterxml.jackson.databind.JsonNode;
import java.util.List;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

/**
 * Live connectivity check for the {@link JiraClient}. This is the smoke test for the
 * "talk to Atlassian directly" capability — proof the app reaches Jira without MCP.
 *
 * <p>Skipped automatically unless credentials are present. To run it:
 * <pre>{@code
 *   set JIRA_EMAIL=you@laerdal.com
 *   set JIRA_API_TOKEN=...                 # from id.atlassian.com API tokens
 *   mvn test -Dtest=JiraConnectionIT
 * }</pre>
 */
class JiraConnectionIT {

    private static boolean credsPresent() {
        return !JiraConfig.email().isEmpty() && !JiraConfig.apiToken().isEmpty();
    }

    @Test
    @DisplayName("myself() authenticates with the API token and returns the current user")
    void authenticates() {
        assumeTrue(credsPresent(), "Set JIRA_EMAIL + JIRA_API_TOKEN to run the live Jira connection check");

        JsonNode me = JiraClient.fromConfig().myself();

        assertTrue(me.hasNonNull("accountId"), "expected an accountId in the /myself response");
        System.out.println("Connected to Jira as: "
                + me.path("displayName").asText() + " <" + me.path("emailAddress").asText("?") + ">");
    }

    @Test
    @DisplayName("Phase-1 JQL returns LBVOICESER tickets ready for testing (incl. re-eval candidates)")
    void phase1Search() {
        assumeTrue(credsPresent(), "Set JIRA_EMAIL + JIRA_API_TOKEN to run the live Jira connection check");

        // Mirrors the timestamp-aware Phase 1 query: excludes only the terminal
        // qa-auto-generated label, so qa-context-requested tickets re-enter for re-eval.
        String jql = "project = " + JiraConfig.projectKey()
                + " AND status = \"Ready for testing\" AND issuetype IN (Story, Task)"
                + " AND (labels IS EMPTY OR labels NOT IN (\"qa-auto-generated\"))"
                + " ORDER BY updated DESC";

        List<JsonNode> issues = JiraClient.fromConfig()
                .searchAll(jql, List.of("summary", "status", "labels", "updated"));

        System.out.println("Phase-1 JQL matched " + issues.size() + " ticket(s):");
        issues.forEach(i -> System.out.println("  " + i.path("key").asText()
                + " — " + i.path("fields").path("summary").asText()
                + "  [labels=" + i.path("fields").path("labels") + "]"));

        assertNotNull(issues, "search should return a (possibly empty) list, never null");
    }
}
