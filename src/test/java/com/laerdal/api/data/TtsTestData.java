package com.laerdal.api.data;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.laerdal.api.model.TtsRequest;
import java.io.IOException;
import java.io.InputStream;
import java.util.Collections;
import java.util.List;
import java.util.concurrent.ThreadLocalRandom;

/**
 * Loads TTS request fixtures from {@code testdata/tts-requests.json} and serves
 * them to tests.
 *
 * <p>{@link #random()} returns a different fixture on each call, so every test
 * run exercises a (randomly) different voice / speech text.
 */
public final class TtsTestData {

    private static final String RESOURCE = "testdata/tts-requests.json";
    private static final ObjectMapper MAPPER = new ObjectMapper();
    private static final List<TtsRequest> DATA = load();

    private TtsTestData() {
        // utility class
    }

    /** All fixtures (immutable). */
    public static List<TtsRequest> all() {
        return DATA;
    }

    /** A randomly chosen fixture — varies per run. */
    public static TtsRequest random() {
        if (DATA.isEmpty()) {
            throw new IllegalStateException("No TTS test data found in " + RESOURCE);
        }
        return DATA.get(ThreadLocalRandom.current().nextInt(DATA.size()));
    }

    private static List<TtsRequest> load() {
        try (InputStream in = TtsTestData.class.getClassLoader().getResourceAsStream(RESOURCE)) {
            if (in == null) {
                throw new IllegalStateException("Missing test data resource: " + RESOURCE);
            }
            List<TtsRequest> list = MAPPER.readValue(
                    in,
                    MAPPER.getTypeFactory().constructCollectionType(List.class, TtsRequest.class));
            return Collections.unmodifiableList(list);
        } catch (IOException e) {
            throw new IllegalStateException("Failed to load " + RESOURCE, e);
        }
    }
}
