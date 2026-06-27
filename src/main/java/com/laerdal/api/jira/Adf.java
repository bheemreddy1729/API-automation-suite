package com.laerdal.api.jira;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.ArrayList;
import java.util.List;

/**
 * Builds minimal Atlassian Document Format (ADF) bodies. REST API v3 requires ADF
 * (not plain strings) for rich-text fields such as comment bodies and issue
 * descriptions.
 */
final class Adf {

    private Adf() {
        // utility class
    }

    /**
     * Wrap plain text into an ADF {@code doc}. Blank line(s) separate paragraphs;
     * consecutive non-blank lines within a paragraph are joined with {@code hardBreak}
     * nodes. This preserves the layout of multi-line comments (e.g. the story-update
     * template) <b>without ever emitting an empty-content paragraph</b>, which the v3
     * API can reject.
     */
    static ObjectNode fromPlainText(ObjectMapper mapper, String text) {
        ObjectNode doc = mapper.createObjectNode();
        doc.put("type", "doc");
        doc.put("version", 1);
        ArrayNode content = doc.putArray("content");

        List<String> block = new ArrayList<>();
        for (String line : text.split("\n", -1)) {
            if (line.isEmpty()) {
                flushParagraph(content, block);
                block.clear();
            } else {
                block.add(line);
            }
        }
        flushParagraph(content, block);

        // Guarantee a valid, non-empty document even if the input was blank.
        if (content.isEmpty()) {
            ObjectNode paragraph = content.addObject();
            paragraph.put("type", "paragraph");
            paragraph.putArray("content").addObject().put("type", "text").put("text", " ");
        }
        return doc;
    }

    /** Append one paragraph for the buffered lines (text nodes separated by hardBreaks). */
    private static void flushParagraph(ArrayNode content, List<String> lines) {
        if (lines.isEmpty()) {
            return;
        }
        ObjectNode paragraph = content.addObject();
        paragraph.put("type", "paragraph");
        ArrayNode paragraphContent = paragraph.putArray("content");
        for (int i = 0; i < lines.size(); i++) {
            if (i > 0) {
                paragraphContent.addObject().put("type", "hardBreak");
            }
            paragraphContent.addObject().put("type", "text").put("text", lines.get(i));
        }
    }
}
