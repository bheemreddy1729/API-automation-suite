package com.laerdal.api.jira;

import java.io.IOException;
import java.io.InputStream;
import java.util.Properties;

/**
 * Read-only configuration for the Jira Cloud REST client.
 *
 * <p>Mirrors {@code com.laerdal.api.config.EnvConfig}'s resolution order so the two
 * suites read config the same way (first hit wins):
 * <ol>
 *   <li>JVM system property (e.g. {@code -Djira.base.url=...})</li>
 *   <li>OS environment variable (UPPER_SNAKE_CASE, e.g. {@code JIRA_BASE_URL})</li>
 *   <li>{@code config/env.properties} on the classpath (non-secret values only)</li>
 *   <li>the hard-coded default</li>
 * </ol>
 *
 * <p><b>Secrets:</b> {@code jira.api.token} must come from a system property or an
 * environment variable ({@code JIRA_API_TOKEN}) — never from {@code env.properties}.
 * Create a token at {@code https://id.atlassian.com/manage-profile/security/api-tokens}.
 */
public final class JiraConfig {

    private static final Properties FILE_PROPS = loadFileProps();

    private JiraConfig() {
        // utility class
    }

    /** Jira Cloud site base URL, e.g. {@code https://laerdal.atlassian.net}. */
    public static String baseUrl() {
        return stripTrailingSlash(get("jira.base.url", "https://laerdal.atlassian.net"));
    }

    /** Atlassian account email used as the Basic-auth username. */
    public static String email() {
        return get("jira.email", "");
    }

    /** Atlassian API token (secret) — read from system property or env var only. */
    public static String apiToken() {
        return get("jira.api.token", "");
    }

    /** Connect/request timeout in milliseconds. */
    public static int timeoutMs() {
        return Integer.parseInt(get("jira.timeout.ms", "30000"));
    }

    /** Default Jira project key for the QA loop. */
    public static String projectKey() {
        return get("jira.project.key", "LBVOICESER");
    }

    /**
     * Resolve a single key by logical (dot.case) name. The OS env var form is the
     * UPPER_SNAKE_CASE of the same name (e.g. {@code jira.base.url} → {@code JIRA_BASE_URL}).
     */
    public static String get(String key, String defaultValue) {
        String sys = System.getProperty(key);
        if (isSet(sys)) {
            return sys.trim();
        }
        String env = System.getenv(toEnvVar(key));
        if (isSet(env)) {
            return env.trim();
        }
        String file = FILE_PROPS.getProperty(key);
        if (isSet(file)) {
            return file.trim();
        }
        return defaultValue;
    }

    private static boolean isSet(String value) {
        return value != null && !value.trim().isEmpty();
    }

    private static String toEnvVar(String key) {
        return key.toUpperCase().replace('.', '_');
    }

    private static String stripTrailingSlash(String url) {
        return url.endsWith("/") ? url.substring(0, url.length() - 1) : url;
    }

    private static Properties loadFileProps() {
        Properties props = new Properties();
        try (InputStream in = JiraConfig.class.getClassLoader()
                .getResourceAsStream("config/env.properties")) {
            if (in != null) {
                props.load(in);
            }
        } catch (IOException e) {
            throw new IllegalStateException("Failed to load config/env.properties", e);
        }
        return props;
    }
}
