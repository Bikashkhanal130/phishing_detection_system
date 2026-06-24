package com.phishguard.app.data.remote;

import androidx.annotation.NonNull;

import com.google.gson.Gson;
import com.phishguard.app.data.local.TokenManager;
import com.phishguard.app.data.model.AccessTokenResponse;
import com.phishguard.app.data.model.RefreshRequest;

import java.io.IOException;

import okhttp3.Interceptor;
import okhttp3.MediaType;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.RequestBody;
import okhttp3.Response;
import okhttp3.ResponseBody;

/**
 * OkHttp interceptor that:
 *  1. Adds "Authorization: Bearer {accessToken}" to every request.
 *  2. On a 401 response, synchronously calls POST /auth/refresh to mint a new
 *     access token, then retries the original request once.
 *  3. If refresh fails, clears tokens and signals re-login via SessionManager.
 */
public class AuthInterceptor implements Interceptor {

    private static final MediaType JSON = MediaType.parse("application/json; charset=utf-8");

    private final TokenManager tokenManager;
    private final String baseUrl;
    private final Gson gson = new Gson();

    public AuthInterceptor(TokenManager tokenManager, String baseUrl) {
        this.tokenManager = tokenManager;
        this.baseUrl = baseUrl;
    }

    @NonNull
    @Override
    public Response intercept(@NonNull Chain chain) throws IOException {
        Request original = chain.request();

        // Don't attach/refresh tokens for the auth endpoints themselves.
        String path = original.url().encodedPath();
        boolean isAuthCall = path.contains("/auth/");

        Request authed = isAuthCall ? original : withBearer(original);
        Response response = chain.proceed(authed);

        if (response.code() == 401 && !isAuthCall) {
            // Attempt a synchronous token refresh.
            response.close();
            String newToken = refreshAccessTokenSync();
            if (newToken != null) {
                Request retry = original.newBuilder()
                        .header("Authorization", "Bearer " + newToken)
                        .build();
                return chain.proceed(retry);
            } else {
                // Refresh failed -> clear session and notify the app to re-login.
                tokenManager.clearTokens();
                SessionManager.notifySessionExpired();
            }
        }
        return response;
    }

    private Request withBearer(Request original) {
        String token = tokenManager.getAccessToken();
        if (token == null) {
            return original;
        }
        return original.newBuilder()
                .header("Authorization", "Bearer " + token)
                .build();
    }

    /**
     * Calls /auth/refresh with its own bare OkHttpClient (no interceptor, to
     * avoid recursion) and returns the new access token, or null on failure.
     */
    private String refreshAccessTokenSync() {
        String refreshToken = tokenManager.getRefreshToken();
        if (refreshToken == null) {
            return null;
        }
        try {
            OkHttpClient bare = new OkHttpClient();
            String body = gson.toJson(new RefreshRequest(refreshToken));
            Request req = new Request.Builder()
                    .url(baseUrl + "auth/refresh")
                    .post(RequestBody.create(body, JSON))
                    .build();

            try (Response resp = bare.newCall(req).execute()) {
                if (!resp.isSuccessful() || resp.body() == null) {
                    return null;
                }
                ResponseBody rb = resp.body();
                AccessTokenResponse parsed = gson.fromJson(rb.string(), AccessTokenResponse.class);
                if (parsed != null && parsed.getAccessToken() != null) {
                    tokenManager.updateAccessToken(parsed.getAccessToken());
                    return parsed.getAccessToken();
                }
            }
        } catch (Exception e) {
            return null;
        }
        return null;
    }
}
