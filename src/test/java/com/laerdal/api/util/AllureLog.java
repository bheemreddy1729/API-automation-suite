package com.laerdal.api.util;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import io.qameta.allure.Allure;
import io.restassured.response.Response;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

/**
 * Attaches HTTP request/response bodies to the Allure report as readable JSON.
 *
 * <p>We log bodies explicitly (rather than relying on the default REST Assured
 * filter) because request bodies are POJOs — Jackson serializes them to proper
 * JSON here. Sensitive fields (e.g. {@code tenantSecret}) are masked so reports
 * are safe to share; binary responses (TTS audio) are summarized, not dumped.
 */
public final class AllureLog {

    private static final ObjectMapper MAPPER = new ObjectMapper();

    /** Lower-cased field names whose values are masked in attachments. */
    private static final Set<String> SENSITIVE_KEYS = new HashSet<>(
            Arrays.asList("tenantsecret", "secret", "password", "authorization"));

    private static final String MASK = "***MASKED***";

    private AllureLog() {
        // utility class
    }

    /** Attach a request body (POJO or JSON string) as pretty, masked JSON. */
    public static void attachRequestBody(String name, Object body) {
        if (body == null) {
            Allure.addAttachment(name, "text/plain", "(no body)", ".txt");
            return;
        }
        try {
            JsonNode root = (body instanceof String)
                    ? MAPPER.readTree((String) body)
                    : MAPPER.valueToTree(body);
            mask(root);
            Allure.addAttachment(name, "application/json", pretty(root), ".json");
        } catch (Exception e) {
            Allure.addAttachment(name, "text/plain", String.valueOf(body), ".txt");
        }
    }

    /** Attach a response body. JSON/text is pretty-printed; binary is summarized. */
    public static void attachResponse(String name, Response response) {
        String contentType = response.getContentType();
        if (isTextual(contentType)) {
            String raw = response.asString();
            String body;
            try {
                JsonNode root = MAPPER.readTree(raw);
                mask(root);
                body = pretty(root);
            } catch (Exception notJson) {
                body = raw;
            }
            Allure.addAttachment(name, "application/json", body, ".json");
        } else {
            byte[] bytes = response.asByteArray();
            String summary = "Binary response (not rendered)\n"
                    + "Status: " + response.statusCode() + "\n"
                    + "Content-Type: " + contentType + "\n"
                    + "Bytes: " + bytes.length;
            Allure.addAttachment(name, "text/plain", summary, ".txt");
        }
    }

    private static boolean isTextual(String contentType) {
        if (contentType == null) {
            return false;
        }
        String ct = contentType.toLowerCase();
        return ct.contains("json") || ct.contains("text") || ct.contains("xml");
    }

    private static String pretty(JsonNode node) throws Exception {
        return MAPPER.writerWithDefaultPrettyPrinter().writeValueAsString(node);
    }

    private static void mask(JsonNode node) {
        if (node instanceof ObjectNode) {
            ObjectNode obj = (ObjectNode) node;
            List<String> fields = new ArrayList<>();
            obj.fieldNames().forEachRemaining(fields::add);
            for (String field : fields) {
                if (SENSITIVE_KEYS.contains(field.toLowerCase())) {
                    obj.put(field, MASK);
                } else {
                    mask(obj.get(field));
                }
            }
        } else if (node instanceof ArrayNode) {
            for (JsonNode child : node) {
                mask(child);
            }
        }
    }
}
