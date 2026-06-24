package com.phishguard.app.data.model;

import com.google.gson.annotations.SerializedName;

/** Body for /api/auth/refresh: { refresh_token }. */
public class RefreshRequest {
    @SerializedName("refresh_token")
    private String refreshToken;

    public RefreshRequest(String refreshToken) { this.refreshToken = refreshToken; }

    public String getRefreshToken() { return refreshToken; }
    public void setRefreshToken(String refreshToken) { this.refreshToken = refreshToken; }
}
