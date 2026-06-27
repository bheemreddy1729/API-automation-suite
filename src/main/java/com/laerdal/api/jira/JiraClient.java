package com.laerdal.api.jira;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;

import java.net.URI;
import java.net.URLEncoder;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.ArrayList;
import java.util.Base64;
import java.util.List;
import java.util.Optional;

/**
 * Minimal, dependency-light client for the <b>Jira Cloud REST API v3</b>, authenticating
 * with HTTP Basic (Atlassian account email + API token).
 *
 * <p>This replaces the Atlassian MCP connection for standalone (non-Claude-Code) use:
 * the application talks to Jira directly over HTTPS. It covers exactly the operations
 * the LBVOICESER QA loop needs — JQL search, get issue, add comment, add/remove labels,
 * create issue, link issues, and read/apply transitions.
 *
 * <p>Built on the JDK's {@link java.net.http.HttpClient}; no MCP, no extra HTTP
 * dependency. Construct once and reuse — the underlying client pools connections.
 *
 * <p><b>Search</b> uses {@code POST /rest/api/3/search/jql} with {@code nextPageToken}
 * pagination; the legacy {@code /rest/api/3/search} endpoint was removed by Atlassian
 * in 2025 and is intentionally not used.
 *
 * <pre>{@code
 *   JiraClient jira = JiraClient.fromConfig();
 *   jira.myself();                                   // connectivity check
 *   var page = jira.searchAll("project = LBVOICESER ...", List.of("summary", "updated"));
 *   jira.addComment("LBVOICESER-1283", "Hi ...");
 *   jira.addLabels("LBVOICESER-1283", "qa-context-requested");
 * }</pre>
 */
public final class JiraClient {

    private final String baseUrl;
    private final String authHeader;
    private final Duration timeout;
    private final HttpClient http;
    private final ObjectMapper mapper = new ObjectMapper();

    public JiraClient(String baseUrl, String email, String apiToken, int timeoutMs) {
        if (isBlank(baseUrl)) {
            throw new IllegalArgumentException("baseUrl is required (jira.base.url / JIRA_BASE_URL)");
        }
        if (isBlank(email)) {
            throw new IllegalArgumentException("email is required (jira.email / JIRA_EMAIL)");
        }
        if (isBlank(apiToken)) {
            throw new IllegalArgumentException("apiToken is required (jira.api.token / JIRA_API_TOKEN)");
        }
        this.baseUrl = baseUrl.endsWith("/") ? baseUrl.substring(0, baseUrl.length() - 1) : baseUrl;
        String creds = email + ":" + apiToken;
        this.authHeader = "Basic " + Base64.getEncoder()
                .encodeToString(creds.getBytes(StandardCharsets.UTF_8));
        this.timeout = Duration.ofMillis(timeoutMs);
        this.http = HttpClient.newBuilder().connectTimeout(this.timeout).build();
    }

    /** Build a client from {@link JiraConfig} (env / system properties / env.properties). */
    public static JiraClient fromConfig() {
        return new JiraClient(JiraConfig.baseUrl(), JiraConfig.email(),
                JiraConfig.apiToken(), JiraConfig.timeoutMs());
    }

    // ---------------------------------------------------------------- connectivity

    /** {@code GET /rest/api/3/myself} — verifies credentials; returns the current user. */
    public JsonNode myself() {
        return send("GET", "/rest/api/3/myself", null);
    }

    // ---------------------------------------------------------------- search

    /** One page of JQL search results plus the token for the next page (null if last). */
    public record SearchPage(List<JsonNode> issues, String nextPageToken) {
    }

    /**
     * Search issues with the enhanced JQL endpoint. Pass {@code nextPageToken} (from a
     * previous page) to continue, or {@code null} for the first page. Note the new API
     * returns only {@code id}/{@code key} unless {@code fields} are requested explicitly.
     */
    public SearchPage searchJql(String jql, List<String> fields, Integer maxResults, String nextPageToken) {
        ObjectNode body = mapper.createObjectNode();
        body.put("jql", jql);
        if (fields != null && !fields.isEmpty()) {
            ArrayNode arr = body.putArray("fields");
            fields.forEach(arr::add);
        }
        if (maxResults != null) {
            body.put("maxResults", maxResults);
        }
        if (!isBlank(nextPageToken)) {
            body.put("nextPageToken", nextPageToken);
        }
        JsonNode resp = send("POST", "/rest/api/3/search/jql", body);
        List<JsonNode> issues = new ArrayList<>();
        if (resp.has("issues")) {
            resp.get("issues").forEach(issues::add);
        }
        String token = resp.hasNonNull("nextPageToken") ? resp.get("nextPageToken").asText() : null;
        return new SearchPage(issues, token);
    }

    /** Search every page, following {@code nextPageToken} until exhausted. */
    public List<JsonNode> searchAll(String jql, List<String> fields) {
        List<JsonNode> all = new ArrayList<>();
        String token = null;
        do {
            SearchPage page = searchJql(jql, fields, 100, token);
            all.addAll(page.issues());
            token = page.nextPageToken();
        } while (!isBlank(token));
        return all;
    }

    // ---------------------------------------------------------------- issue read

    /** {@code GET /rest/api/3/issue/{key}} with an optional explicit field list. */
    public JsonNode getIssue(String key, List<String> fields) {
        String query = (fields != null && !fields.isEmpty())
                ? "?fields=" + String.join(",", fields)
                : "";
        return send("GET", "/rest/api/3/issue/" + enc(key) + query, null);
    }

    // ---------------------------------------------------------------- comments

    /** Add a comment (plain text, wrapped into ADF as required by API v3). */
    public void addComment(String key, String text) {
        ObjectNode body = mapper.createObjectNode();
        body.set("body", Adf.fromPlainText(mapper, text));
        send("POST", "/rest/api/3/issue/" + enc(key) + "/comment", body);
    }

    // ---------------------------------------------------------------- labels

    /** Add one or more labels without disturbing existing labels. */
    public void addLabels(String key, String... labels) {
        updateLabels(key, labels, true);
    }

    /** Remove one or more labels without disturbing the others. */
    public void removeLabels(String key, String... labels) {
        updateLabels(key, labels, false);
    }

    private void updateLabels(String key, String[] labels, boolean add) {
        ObjectNode body = mapper.createObjectNode();
        ArrayNode ops = body.putObject("update").putArray("labels");
        for (String label : labels) {
            ops.addObject().put(add ? "add" : "remove", label);
        }
        send("PUT", "/rest/api/3/issue/" + enc(key), body);
    }

    // ---------------------------------------------------------------- create issue

    /**
     * Create an issue. Only project key, issue type name, and summary are required in
     * this project. {@code descriptionText} may be {@code null}/blank. Returns the new key.
     */
    public String createIssue(String projectKey, String issueTypeName, String summary, String descriptionText) {
        ObjectNode fields = mapper.createObjectNode();
        fields.putObject("project").put("key", projectKey);
        fields.putObject("issuetype").put("name", issueTypeName);
        fields.put("summary", summary);
        if (!isBlank(descriptionText)) {
            fields.set("description", Adf.fromPlainText(mapper, descriptionText));
        }
        ObjectNode body = mapper.createObjectNode();
        body.set("fields", fields);
        JsonNode resp = send("POST", "/rest/api/3/issue", body);
        return resp.get("key").asText();
    }

    // ---------------------------------------------------------------- issue links

    /**
     * Link two issues. For the {@code Tests} link type, {@code inwardIssue} is the Test
     * card and {@code outwardIssue} is the parent ⇒ "parent is tested by the Test card".
     */
    public void createIssueLink(String typeName, String inwardKey, String outwardKey) {
        ObjectNode body = mapper.createObjectNode();
        body.putObject("type").put("name", typeName);
        body.putObject("inwardIssue").put("key", inwardKey);
        body.putObject("outwardIssue").put("key", outwardKey);
        send("POST", "/rest/api/3/issueLink", body);
    }

    // ---------------------------------------------------------------- transitions

    /** An available workflow transition: its id and display name. */
    public record Transition(String id, String name) {
    }

    /** Transitions available from the issue's current status. */
    public List<Transition> getTransitions(String key) {
        JsonNode resp = send("GET", "/rest/api/3/issue/" + enc(key) + "/transitions", null);
        List<Transition> out = new ArrayList<>();
        if (resp.has("transitions")) {
            for (JsonNode t : resp.get("transitions")) {
                out.add(new Transition(t.get("id").asText(), t.get("name").asText()));
            }
        }
        return out;
    }

    /** Resolve a transition by (case-insensitive) name; empty if not reachable from the current status. */
    public Optional<Transition> findTransition(String key, String name) {
        return getTransitions(key).stream()
                .filter(t -> t.name().equalsIgnoreCase(name))
                .findFirst();
    }

    /** Apply a transition by its id (resolve via {@link #findTransition} / {@link #getTransitions}). */
    public void transition(String key, String transitionId) {
        ObjectNode body = mapper.createObjectNode();
        body.putObject("transition").put("id", transitionId);
        send("POST", "/rest/api/3/issue/" + enc(key) + "/transitions", body);
    }

    // ---------------------------------------------------------------- core HTTP

    private JsonNode send(String method, String path, JsonNode body) {
        HttpRequest.Builder builder = HttpRequest.newBuilder(URI.create(baseUrl + path))
                .timeout(timeout)
                .header("Authorization", authHeader)
                .header("Accept", "application/json");
        if (body != null) {
            String json;
            try {
                json = mapper.writeValueAsString(body);
            } catch (Exception e) {
                throw new JiraException("Failed to serialize request body for " + path, e);
            }
            builder.header("Content-Type", "application/json")
                    .method(method, HttpRequest.BodyPublishers.ofString(json, StandardCharsets.UTF_8));
        } else {
            builder.method(method, HttpRequest.BodyPublishers.noBody());
        }

        HttpResponse<String> resp;
        try {
            resp = http.send(builder.build(), HttpResponse.BodyHandlers.ofString(StandardCharsets.UTF_8));
        } catch (Exception e) {
            throw new JiraException(method + " " + path + " failed: " + e.getMessage(), e);
        }

        int status = resp.statusCode();
        if (status < 200 || status >= 300) {
            throw new JiraException(method + " " + path + " -> HTTP " + status + ": " + truncate(resp.body()), status);
        }

        String responseBody = resp.body();
        if (isBlank(responseBody)) {
            return mapper.nullNode();
        }
        try {
            return mapper.readTree(responseBody);
        } catch (Exception e) {
            throw new JiraException("Failed to parse response from " + path, e);
        }
    }

    private static String enc(String segment) {
        return URLEncoder.encode(segment, StandardCharsets.UTF_8);
    }

    private static boolean isBlank(String s) {
        return s == null || s.trim().isEmpty();
    }

    private static String truncate(String s) {
        if (s == null) {
            return "";
        }
        return s.length() > 500 ? s.substring(0, 500) + "..." : s;
    }
}
