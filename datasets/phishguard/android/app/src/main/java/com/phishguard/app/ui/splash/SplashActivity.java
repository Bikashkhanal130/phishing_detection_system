package com.phishguard.app.ui.splash;

import android.content.Intent;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;

import androidx.appcompat.app.AppCompatActivity;

import com.phishguard.app.data.local.TokenManager;
import com.phishguard.app.databinding.ActivitySplashBinding;
import com.phishguard.app.ui.auth.LoginActivity;
import com.phishguard.app.ui.main.MainActivity;

/**
 * Checks for a stored access token and routes to MainActivity (logged in) or
 * LoginActivity (not logged in).
 */
public class SplashActivity extends AppCompatActivity {

    private ActivitySplashBinding binding;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        binding = ActivitySplashBinding.inflate(getLayoutInflater());
        setContentView(binding.getRoot());

        new Handler(Looper.getMainLooper()).postDelayed(this::route, 900);
    }

    private void route() {
        TokenManager tokenManager = TokenManager.getInstance(this);
        Intent intent = tokenManager.isLoggedIn()
                ? new Intent(this, MainActivity.class)
                : new Intent(this, LoginActivity.class);
        startActivity(intent);
        finish();
    }
}
