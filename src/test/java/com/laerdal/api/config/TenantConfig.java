package com.laerdal.api.config;

import com.laerdal.api.model.Scope;
import com.laerdal.api.model.TokenRequest;
import java.io.IOException;
import java.io.InputStream;
import java.util.Properties;

/**
 * Read-only access to per-tenant credentials.
 *
 * <p>Secrets resolve as: env var {@code TENANT_<id>_SECRET} (preferred for CI) →
 * {@code config/tenants.properties} (git-ignored). Non-secret attributes
 * (role / langCode / userId) resolve via system property → env var → file → default.
 */
public final class TenantConfig {

    private static final Properties PROPS = load();

    private TenantConfig() {
        // utility class
    }

    /** Tenant id used when a test does not specify one. */
    public static String defaultTenantId() {
        return resolve("tenant.default", "201");
    }

    public static Tenant defaultTenant() {
        return get(defaultTenantId());
    }

    /** Resolve the full credential set for a tenant; fails fast if no secret is configured. */
    public static Tenant get(String tenantId) {
        String secret = secretFor(tenantId);
        if (secret == null || secret.trim().isEmpty()) {
            throw new IllegalStateException("No secret configured for tenant '" + tenantId
                    + "'. Set env var TENANT_" + tenantId + "_SECRET or 'tenant." + tenantId
                    + ".secret' in src/test/resources/config/tenants.properties");
        }
        return new Tenant(
                tenantId,
                secret.trim(),
                resolve("tenant." + tenantId + ".role", "vsim_admin"),
                resolve("tenant." + tenantId + ".langCode", "en"),
                resolve("tenant." + tenantId + ".userId", "1"));
    }

    private static String secretFor(String tenantId) {
        String env = System.getenv("TENANT_" + tenantId + "_SECRET");
        if (env != null && !env.trim().isEmpty()) {
            return env;
        }
        return PROPS.getProperty("tenant." + tenantId + ".secret");
    }

    private static String resolve(String key, String defaultValue) {
        String sys = System.getProperty(key);
        if (isSet(sys)) {
            return sys.trim();
        }
        String env = System.getenv(key.toUpperCase().replace('.', '_'));
        if (isSet(env)) {
            return env.trim();
        }
        String file = PROPS.getProperty(key);
        if (isSet(file)) {
            return file.trim();
        }
        return defaultValue;
    }

    private static boolean isSet(String value) {
        return value != null && !value.trim().isEmpty();
    }

    private static Properties load() {
        Properties props = new Properties();
        try (InputStream in = TenantConfig.class.getClassLoader()
                .getResourceAsStream("config/tenants.properties")) {
            if (in != null) {
                props.load(in);
            }
        } catch (IOException e) {
            throw new IllegalStateException("Failed to load config/tenants.properties", e);
        }
        return props;
    }

    /** Immutable credential set for a single tenant. */
    public static final class Tenant {
        public final String id;
        public final String secret;
        public final String role;
        public final String langCode;
        public final String userId;

        Tenant(String id, String secret, String role, String langCode, String userId) {
            this.id = id;
            this.secret = secret;
            this.role = role;
            this.langCode = langCode;
            this.userId = userId;
        }

        /** Build the token request body for this tenant. */
        public TokenRequest toTokenRequest() {
            return new TokenRequest(secret, id, new Scope(role, langCode, userId), "oauth2.0");
        }
    }
}
