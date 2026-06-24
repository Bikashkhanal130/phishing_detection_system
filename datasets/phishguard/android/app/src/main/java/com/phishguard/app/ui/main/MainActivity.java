package com.phishguard.app.ui.main;

import android.content.Intent;
import android.os.Bundle;
import android.widget.Toast;

import androidx.annotation.NonNull;
import androidx.appcompat.app.AppCompatActivity;
import androidx.fragment.app.Fragment;

import com.phishguard.app.data.local.TokenManager;
import com.phishguard.app.data.model.MessageResponse;
import com.phishguard.app.data.remote.ApiService;
import com.phishguard.app.data.remote.RetrofitClient;
import com.phishguard.app.data.remote.SessionManager;
import com.phishguard.app.databinding.ActivityMainBinding;
import com.phishguard.app.ui.auth.LoginActivity;
import com.phishguard.app.ui.profile.ProfileFragment;
import com.phishguard.app.ui.scanner.ScannerFragment;

import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

/** Hosts the Scanner and Profile fragments via a BottomNavigationView. */
public class MainActivity extends AppCompatActivity {

    private ActivityMainBinding binding;
    private ApiService api;
    private TokenManager tokenManager;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        binding = ActivityMainBinding.inflate(getLayoutInflater());
        setContentView(binding.getRoot());

        api = RetrofitClient.getApiService(this);
        tokenManager = TokenManager.getInstance(this);

        setSupportActionBar(binding.toolbar);

        if (savedInstanceState == null) {
            showFragment(new ScannerFragment());
        }

        binding.bottomNav.setOnItemSelectedListener(item -> {
            int id = item.getItemId();
            if (id == com.phishguard.app.R.id.nav_scanner) {
                showFragment(new ScannerFragment());
                return true;
            } else if (id == com.phishguard.app.R.id.nav_profile) {
                showFragment(new ProfileFragment());
                return true;
            }
            return false;
        });

        // Redirect to login if the session expires (refresh token failed).
        SessionManager.getSessionExpired().observe(this, expired -> {
            if (Boolean.TRUE.equals(expired)) {
                SessionManager.reset();
                forceLogout();
            }
        });

        binding.toolbar.setOnMenuItemClickListener(item -> {
            if (item.getItemId() == com.phishguard.app.R.id.action_logout) {
                logout();
                return true;
            }
            return false;
        });
        binding.toolbar.inflateMenu(com.phishguard.app.R.menu.toolbar_menu);
    }

    private void showFragment(@NonNull Fragment fragment) {
        getSupportFragmentManager()
                .beginTransaction()
                .replace(com.phishguard.app.R.id.fragmentContainer, fragment)
                .commit();
    }

    private void logout() {
        api.logout().enqueue(new Callback<MessageResponse>() {
            @Override
            public void onResponse(Call<MessageResponse> call, Response<MessageResponse> response) {
                forceLogout();
            }

            @Override
            public void onFailure(Call<MessageResponse> call, Throwable t) {
                // Even if the network call fails, clear locally.
                forceLogout();
            }
        });
    }

    private void forceLogout() {
        tokenManager.clearTokens();
        Intent intent = new Intent(this, LoginActivity.class);
        intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TASK);
        startActivity(intent);
        finish();
    }
}
