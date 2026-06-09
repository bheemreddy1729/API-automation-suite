package com.laerdal.api.tests;

import static org.hamcrest.Matchers.greaterThanOrEqualTo;

import app.getxray.xray.junit.customjunitxml.annotations.Requirement;
import app.getxray.xray.junit.customjunitxml.annotations.XrayTest;
import com.laerdal.api.clients.AuthClient;
import com.laerdal.api.clients.TtsClient;
import com.laerdal.api.data.TtsTestData;
import com.laerdal.api.model.TtsRequest;
import io.qameta.allure.Description;
import io.qameta.allure.Feature;
import io.qameta.allure.TmsLink;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

/**
 * Automation for Xray test LBVOICESER-1307 — "TTS Post API".
 *
 * <p>Covers all manual test cases defined in the Xray Test Details panel:
 * valid request, missing/invalid auth, empty body, missing required fields.
 */
@Feature("TTS Post API")
@XrayTest(key = "LBVOICESER-1307")
@Requirement({"LBVOICESER-1307"})
@TmsLink("LBVOICESER-1307")
class TtsPostApiTest {

    @Test
    @DisplayName("TC01 - Send valid voice and speech text")
    @Description("POST with valid Bearer token, valid voice, valid speechText → 200 OK and audio bytes returned.")
    void tc01_validVoiceAndSpeechText() {
        TtsClient.synthesize(TtsTestData.random())
                .then().statusCode(200);
    }

    @Test
    @DisplayName("TC02 - Send request without Authorization token")
    @Description("POST to /tts/v1/tts with no Authorization header → API rejects the request (≥400).")
    void tc02_missingAuthorizationToken() {
        TtsClient.synthesizeWithoutAuth(TtsTestData.random())
                .then().statusCode(greaterThanOrEqualTo(400));
    }

    @Test
    @DisplayName("TC04 - Send request with empty body")
    @Description("POST with an empty JSON body {} (voice and speechText both null) → 400 Bad Request.")
    void tc04_emptyBody() {
        String token = AuthClient.defaultToken();
        TtsClient.synthesize(token, new TtsRequest())
                .then().statusCode(greaterThanOrEqualTo(400));
    }

    @Test
    @DisplayName("TC05 - Send request with missing voice field")
    @Description("POST with only speechText provided, voice field omitted → 400 Bad Request.")
    void tc05_missingVoiceField() {
        String token = AuthClient.defaultToken();
        TtsClient.synthesize(token, new TtsRequest(null, "Missing voice field test"))
                .then().statusCode(greaterThanOrEqualTo(400));
    }

    @Test
    @DisplayName("TC06 - Send request with missing speechText field")
    @Description("POST with only voice provided, speechText field omitted → 400 Bad Request.")
    void tc06_missingSpeechTextField() {
        String token = AuthClient.defaultToken();
        TtsClient.synthesize(token, new TtsRequest("Male_Davis_Terrified_1", null))
                .then().statusCode(greaterThanOrEqualTo(400));
    }
}
