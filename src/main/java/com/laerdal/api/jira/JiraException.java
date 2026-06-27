package com.laerdal.api.jira;

/**
 * Thrown when a Jira REST call returns a non-2xx status or cannot be completed
 * (network error, serialization failure, unparseable response).
 */
public class JiraException extends RuntimeException {

    private static final long serialVersionUID = 1L;

    /** HTTP status code, or {@code 0} when the failure was not an HTTP response. */
    private final int statusCode;

    public JiraException(String message, int statusCode) {
        super(message);
        this.statusCode = statusCode;
    }

    public JiraException(String message, Throwable cause) {
        super(message, cause);
        this.statusCode = 0;
    }

    /** HTTP status code, or {@code 0} when the failure was not an HTTP response. */
    public int statusCode() {
        return statusCode;
    }
}
