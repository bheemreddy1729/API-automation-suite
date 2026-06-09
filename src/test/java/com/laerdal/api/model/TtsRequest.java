package com.laerdal.api.model;

/**
 * Body for {@code POST /tts/v1/tts}.
 *
 * <pre>{@code
 * { "voice": "Female_Aria_Hopeful_LowPitch", "speechText": "..." }
 * }</pre>
 */
public class TtsRequest {

    public String voice;
    public String speechText;

    public TtsRequest() {
    }

    public TtsRequest(String voice, String speechText) {
        this.voice = voice;
        this.speechText = speechText;
    }
}
