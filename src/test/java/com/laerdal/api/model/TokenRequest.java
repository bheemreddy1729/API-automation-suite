package com.laerdal.api.model;

/**
 * Body for {@code POST /account/v1/token}.
 *
 * <pre>{@code
 * {
 *   "tenantSecret": "...",
 *   "tenantId": "201",
 *   "scope": { "role": "vsim_admin", "langCode": "en", "userId": "1" },
 *   "grantType": "oauth2.0"
 * }
 * }</pre>
 */
public class TokenRequest {

    public String tenantSecret;
    public String tenantId;
    public Scope scope;
    public String grantType;

    public TokenRequest() {
    }

    public TokenRequest(String tenantSecret, String tenantId, Scope scope, String grantType) {
        this.tenantSecret = tenantSecret;
        this.tenantId = tenantId;
        this.scope = scope;
        this.grantType = grantType;
    }
}
