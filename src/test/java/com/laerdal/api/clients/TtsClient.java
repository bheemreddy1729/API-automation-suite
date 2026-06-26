package com.laerdal.api.clients;

import static io.restassured.RestAssured.given;

import com.laerdal.api.config.EnvConfig;
import com.laerdal.api.config.SpecFactory;
import com.laerdal.api.model.TtsRequest;
import io.qameta.allure.restassured.AllureRestAssured;
import io.restassured.response.Response;

/**
 * Client for {@code POST /tts/v1/tts}. The endpoint returns audio bytes
 * ({@code application/octet-stream}), so callers read the body via
 * {@link Response#asByteArray()}.
 */
public final class TtsClient {

    private TtsClient() {
        // utility class
    }

    /** Synthesize using an explicit bearer token and a {@link TtsRequest} body. */
    public static Response synthesize(String bearerToken, TtsRequest body) {
        return given()
                .spec(SpecFactory.request())
                .filter(new AllureRestAssured())
                .accept("*/*")
                .header("Authorization", "Bearer " + bearerToken)
                .body(body)
        .when()
                .post(EnvConfig.ttsPath());
    }

    /** Synthesize a {@link TtsRequest} using the default tenant's cached token. */
    public static Response synthesize(TtsRequest body) {
        return synthesize(AuthClient.defaultToken(), body);
    }

    /** Call the endpoint with a {@link TtsRequest} but no Authorization header (negative tests). */
    public static Response synthesizeWithoutAuth(TtsRequest body) {
        return given()
                .spec(SpecFactory.request())
                .filter(new AllureRestAssured())
                .accept("*/*")
                .body(body)
        .when()
                .post(EnvConfig.ttsPath());
    }

    /** Stream-synthesize using an explicit bearer token and a {@link TtsRequest} body. */
    public static Response synthesizeStream(String bearerToken, TtsRequest body) {
        return given()
                .spec(SpecFactory.request())
                .filter(new AllureRestAssured())
                .accept("*/*")
                .header("Authorization", "Bearer " + bearerToken)
                .body(body)
        .when()
                .post(EnvConfig.ttsStreamPath());
    }

    /** Stream-synthesize a {@link TtsRequest} using the default tenant's cached token. */
    public static Response synthesizeStream(TtsRequest body) {
        return synthesizeStream(AuthClient.defaultToken(), body);
    }

    /** Call the stream endpoint with a {@link TtsRequest} but no Authorization header (negative tests). */
    public static Response synthesizeStreamWithoutAuth(TtsRequest body) {
        return given()
                .spec(SpecFactory.request())
                .filter(new AllureRestAssured())
                .accept("*/*")
                .body(body)
        .when()
                .post(EnvConfig.ttsStreamPath());
    }
}