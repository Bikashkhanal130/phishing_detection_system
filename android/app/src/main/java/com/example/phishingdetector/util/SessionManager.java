package com.example.phishingdetector.util;

import android.content.Context;
import android.content.SharedPreferences;

/** Stores the JWT token + basic user info in SharedPreferences. */
public class SessionManager {

    private static final String PREF = "phishing_session";
    private static final String KEY_TOKEN = "token";
    private static final String KEY_NAME = "name";
    private static final String KEY_EMAIL = "email";

    private final SharedPreferences prefs;

    public SessionManager(Context ctx) {
        prefs = ctx.getApplicationContext().getSharedPreferences(PREF, Context.MODE_PRIVATE);
    }

    public void save(String token, String name, String email) {
        prefs.edit()
                .putString(KEY_TOKEN, token)
                .putString(KEY_NAME, name)
                .putString(KEY_EMAIL, email)
                .apply();
    }

    public String getToken() { return prefs.getString(KEY_TOKEN, null); }

    /** Ready-to-use Authorization header value. */
    public String bearer() { return "Bearer " + getToken(); }

    public String getName() { return prefs.getString(KEY_NAME, ""); }

    public String getEmail() { return prefs.getString(KEY_EMAIL, ""); }

    public boolean isLoggedIn() { return getToken() != null; }

    public void logout() { prefs.edit().clear().apply(); }
}
