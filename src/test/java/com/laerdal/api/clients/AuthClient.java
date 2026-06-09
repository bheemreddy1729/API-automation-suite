package com.laerdal.api.clients;

import static io.restassured.RestAssured.given;

import com.laerdal.api.config.EnvConfig;
import com.laerdal.api.config.SpecFactory;
import com.laerdal.api.config.TenantConfig;
import com.laerdal.api.model.TokenRequest;
import com.laerdal.api.util.AllureLog;
import io.restassured.response.Response;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * Client for the token/auth endpoint.
 *
 * <p>{@link #tokenFor(String)} fetches a JWT once per tenant and caches it for
 * the JVM run, so every subsequent API call reuses the same token (the token is
 * a ~24h JWT). {@link #requestToken(Object)} performs a raw, unasserted call for
 * negative tests.
 */
public final class AuthClient {

    /** tenantId -> cached bearer token. */
    private static final Map<String, String> TOKEN_CACHE = new ConcurrentHashMap<>();

    private AuthClient() {
        // utility class
    }

    /** Raw token request with no assertions. Request/response logged to Allure (secret masked). */
    public static Response requestToken(TokenRequest body) {
        AllureLog.attachRequestBody("Token request body", body);
        Response response = given()
                .spec(SpecFactory.request())
                .body(body)
        .when()
                .post(EnvConfig.tokenPath());
        AllureLog.attachResponse("Token response body", response);
        return response;
    }

    /** Cached, valid bearer token for the given tenant (fetched on first use). */
    public static String tokenFor(String tenantId) {
        return TOKEN_CACHE.computeIfAbsent(tenantId, AuthClient::fetchAndCache);
    }

    /** Cached, valid bearer token for the default tenant. */
    public static String defaultToken() {
        return tokenFor(TenantConfig.defaultTenantId());
    }

    /** Drop a cached token (e.g. after a 401) so the next call re-authenticates. */
    public static void invalidate(String tenantId) {
        TOKEN_CACHE.remove(tenantId);
    }

    public static void clearCache() {
        TOKEN_CACHE.clear();
    }

    private static String fetchAndCache(String tenantId) {
        Response response = requestToken(TenantConfig.get(tenantId).toTokenRequest());
        if (response.statusCode() != 200) {
            throw new IllegalStateException("Token request failed for tenant '" + tenantId
                    + "': HTTP " + response.statusCode() + " - " + response.asString());
        }
        String token = response.path("data.token");
        if (token == null || token.trim().isEmpty()) {
            throw new IllegalStateException("No data.token in token response: " + response.asString());
        }
        return token;
    }
}
