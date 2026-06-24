package com.phishguard.app.data.model;

import com.google.gson.annotations.SerializedName;

/** Response from /api/auth/refresh. */
public class AccessTokenResponse {
    @SerializedName("access_token")
    private String accessToken;

    public String getAccessToken() { return accessToken; }
    public void setAccessToken(String accessToken) { this.accessToken = accessToken; }
}
