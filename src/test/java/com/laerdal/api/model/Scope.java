package com.laerdal.api.model;

/** {@code scope} object of a token request. */
public class Scope {

    public String role;
    public String langCode;
    public String userId;

    public Scope() {
    }

    public Scope(String role, String langCode, String userId) {
        this.role = role;
        this.langCode = langCode;
        this.userId = userId;
    }
}
