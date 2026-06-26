package com.laerdal.api.config;

import java.io.IOException;
import java.io.InputStream;
import java.util.Properties;

/**
 * Central, read-only access to environment configuration.
 *
 * <p>Resolution order for every key (first hit wins):
 * <ol>
 *   <li>JVM system property (e.g. {@code -Dapi.base.uri=...})</li>
 *   <li>OS environment variable (UPPER_SNAKE_CASE, e.g. {@code API_BASE_URI})</li>
 *   <li>{@code src/test/resources/config/env.properties}</li>
 *   <li>the hard-coded default passed by the caller</li>
 * </ol>
 *
 * <p>Secrets (tokens, API keys) should come from env vars / a git-ignored
 * {@code .env}, never from {@code env.properties}.
 */
public final class EnvConfig {

    private static final Properties FILE_PROPS = loadFileProps();

    private EnvConfig() {
        // utility class
    }

    /** Base URI of the system under test, e.g. {@code https://api.example.com}. */
    public static String baseUri() {
        return get("api.base.uri", "https://reqres.in");
    }

    /** Optional base path prefixed to every request, e.g. {@code /api}. Empty by default. */
    public static String basePath() {
        return get("api.base.path", "");
    }

    /** Auth scheme: {@code none}, {@code bearer}, {@code apikey}, or {@code basic}. */
    public static String authType() {
        return get("api.auth.type", "none").toLowerCase();
    }

    /** Bearer token / API-key value (read from env or system property only). */
    public static String authToken() {
        return get("api.auth.token", "");
    }

    /** Header name used when {@link #authType()} is {@code apikey}. */
    public static String apiKeyHeader() {
        return get("api.auth.header", "x-api-key");
    }

    /** Request/response timeout in milliseconds. */
    public static int timeoutMs() {
        return Integer.parseInt(get("api.timeout.ms", "30000"));
    }

    /** Path of the token/auth endpoint, relative to {@link #baseUri()}. */
    public static String tokenPath() {
        return get("token.path", "/account/v1/token");
    }

    /** Path of the TTS endpoint, relative to {@link #baseUri()}. */
    public static String ttsPath() {
        return get("tts.path", "/tts/v1/tts");
    }

    /** Path of the TTS streaming endpoint, relative to {@link #baseUri()}. */
    public static String ttsStreamPath() {
        return get("tts.stream.path", "/tts/v1/tts-stream");
    }

    /**
     * Resolve a single key by logical (dot.case) name.
     * The OS env var form is the UPPER_SNAKE_CASE of the same name.
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

    private static Properties loadFileProps() {
        Properties props = new Properties();
        try (InputStream in = EnvConfig.class.getClassLoader()
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
