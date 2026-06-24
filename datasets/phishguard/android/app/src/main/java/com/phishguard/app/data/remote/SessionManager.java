package com.phishguard.app.data.remote;

import androidx.lifecycle.LiveData;
import androidx.lifecycle.MutableLiveData;

/**
 * Broadcasts a "session expired" signal (e.g. refresh token failed) so the
 * UI layer can redirect to the login screen. Observed by MainActivity.
 */
public final class SessionManager {

    private static final MutableLiveData<Boolean> sessionExpired = new MutableLiveData<>(false);

    private SessionManager() {}

    /** Called from the AuthInterceptor (background thread) on refresh failure. */
    public static void notifySessionExpired() {
        sessionExpired.postValue(true);
    }

    public static LiveData<Boolean> getSessionExpired() {
        return sessionExpired;
    }

    /** Reset after the UI has handled the redirect. */
    public static void reset() {
        sessionExpired.postValue(false);
    }
}
