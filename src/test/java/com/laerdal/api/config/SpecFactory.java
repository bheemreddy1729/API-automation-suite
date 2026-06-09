package com.laerdal.api.config;

import io.restassured.builder.RequestSpecBuilder;
import io.restassured.builder.ResponseSpecBuilder;
import io.restassured.config.HttpClientConfig;
import io.restassured.config.RestAssuredConfig;
import io.restassured.http.ContentType;
import io.restassured.specification.RequestSpecification;
import io.restassured.specification.ResponseSpecification;
import org.hamcrest.Matchers;

/**
 * Builds the shared REST Assured request/response specifications so every test
 * starts from the same base URI, headers, auth, timeouts, and Allure logging.
 *
 * <p>Usage in a test:
 * <pre>{@code
 *   given().spec(SpecFactory.request())
 *   .when().get("/users/2")
 *   .then().spec(SpecFactory.okJson()).body("data.id", equalTo(2));
 * }</pre>
 */
public final class SpecFactory {

    private SpecFactory() {
        // utility class
    }

    /**
     * Shared request spec: base URI/path, JSON content type, auth, timeout.
     *
     * <p>TTS clients attach request/response via {@code AllureRestAssured} filter.
     * Auth clients use {@code AllureLog} (Jackson-serialized + secret-masked).
     */
    public static RequestSpecification request() {
        RestAssuredConfig config = RestAssuredConfig.config()
                .httpClient(HttpClientConfig.httpClientConfig()
                        .setParam("http.connection.timeout", EnvConfig.timeoutMs())
                        .setParam("http.socket.timeout", EnvConfig.timeoutMs()));

        RequestSpecBuilder builder = new RequestSpecBuilder()
                .setBaseUri(EnvConfig.baseUri())
                .setBasePath(EnvConfig.basePath())
                .setContentType(ContentType.JSON)
                .setAccept(ContentType.JSON)
                .setConfig(config);

        applyAuth(builder);
        return builder.build();
    }

    /** Convenience response spec asserting HTTP 200 + JSON body. */
    public static ResponseSpecification okJson() {
        return jsonStatus(200);
    }

    /** Response spec asserting a given status code + JSON content type. */
    public static ResponseSpecification jsonStatus(int statusCode) {
        return new ResponseSpecBuilder()
                .expectStatusCode(statusCode)
                .expectContentType(ContentType.JSON)
                .build();
    }

    /** Response spec for a successful TTS call: 200, audio bytes, within timeout. */
    public static ResponseSpecification audioOk() {
        return new ResponseSpecBuilder()
                .expectStatusCode(200)
                .expectContentType("application/octet-stream")
                .expectResponseTime(Matchers.lessThan((long) EnvConfig.timeoutMs()))
                .build();
    }

    private static void applyAuth(RequestSpecBuilder builder) {
        String token = EnvConfig.authToken();
        switch (EnvConfig.authType()) {
            case "bearer":
                if (!token.isEmpty()) {
                    builder.addHeader("Authorization", "Bearer " + token);
                }
                break;
            case "apikey":
                if (!token.isEmpty()) {
                    builder.addHeader(EnvConfig.apiKeyHeader(), token);
                }
                break;
            case "basic":
                // For basic auth, set API_AUTH_TOKEN to a pre-encoded "user:pass" base64 value,
                // or switch to RestAssured.given().auth().preemptive().basic(user, pass) per test.
                if (!token.isEmpty()) {
                    builder.addHeader("Authorization", "Basic " + token);
                }
                break;
            case "none":
            default:
                // no auth header
                break;
        }
    }
}
