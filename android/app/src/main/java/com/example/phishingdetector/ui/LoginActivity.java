package com.example.phishingdetector.ui;

import android.content.Intent;
import android.os.Bundle;
import android.view.View;
import android.widget.ProgressBar;
import android.widget.Toast;

import androidx.appcompat.app.AppCompatActivity;

import com.example.phishingdetector.R;
import com.example.phishingdetector.api.ApiClient;
import com.example.phishingdetector.api.Models;
import com.example.phishingdetector.util.SessionManager;
import com.google.android.material.button.MaterialButton;
import com.google.android.material.textfield.TextInputEditText;

import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

public class LoginActivity extends AppCompatActivity {

    private TextInputEditText etEmail, etPassword;
    private ProgressBar progress;
    private SessionManager session;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_login);
        session = new SessionManager(this);

        // already logged in? skip to home
        if (session.isLoggedIn()) {
            goHome();
            return;
        }

        etEmail = findViewById(R.id.etEmail);
        etPassword = findViewById(R.id.etPassword);
        progress = findViewById(R.id.progress);
        MaterialButton btnLogin = findViewById(R.id.btnLogin);
        MaterialButton btnGoRegister = findViewById(R.id.btnGoRegister);

        btnLogin.setOnClickListener(v -> doLogin());
        btnGoRegister.setOnClickListener(v ->
                startActivity(new Intent(this, RegisterActivity.class)));
    }

    private void doLogin() {
        String email = etEmail.getText().toString().trim();
        String pass = etPassword.getText().toString();
        if (email.isEmpty() || pass.isEmpty()) {
            toast("Enter email and password");
            return;
        }
        setLoading(true);
        ApiClient.get().login(new Models.LoginRequest(email, pass))
                .enqueue(new Callback<Models.AuthResponse>() {
                    @Override
                    public void onResponse(Call<Models.AuthResponse> call, Response<Models.AuthResponse> res) {
                        setLoading(false);
                        Models.AuthResponse body = res.body();
                        if (res.isSuccessful() && body != null && body.token != null) {
                            session.save(body.token, body.user.fullName, body.user.email);
                            goHome();
                        } else if (body != null && body.needVerification) {
                            // backend re-sent a code; go verify
                            Intent i = new Intent(LoginActivity.this, OtpActivity.class);
                            i.putExtra("email", body.email != null ? body.email : email);
                            startActivity(i);
                        } else {
                            toast(body != null && body.error != null ? body.error : "Login failed");
                        }
                    }
                    @Override
                    public void onFailure(Call<Models.AuthResponse> call, Throwable t) {
                        setLoading(false);
                        toast("Network error: " + t.getMessage());
                    }
                });
    }

    private void goHome() {
        startActivity(new Intent(this, HomeActivity.class));
        finish();
    }

    private void setLoading(boolean b) {
        progress.setVisibility(b ? View.VISIBLE : View.GONE);
    }

    private void toast(String s) {
        Toast.makeText(this, s, Toast.LENGTH_LONG).show();
    }
}
