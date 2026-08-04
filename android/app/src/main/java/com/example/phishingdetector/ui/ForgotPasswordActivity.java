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
import com.google.android.material.button.MaterialButton;
import com.google.android.material.textfield.TextInputEditText;
import com.google.gson.Gson;

import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

public class ForgotPasswordActivity extends AppCompatActivity {

    private TextInputEditText etEmail;
    private ProgressBar progress;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_forgot_password);

        etEmail = findViewById(R.id.etEmail);
        progress = findViewById(R.id.progress);
        MaterialButton btnSendCode = findViewById(R.id.btnSendCode);
        MaterialButton btnBackToLogin = findViewById(R.id.btnBackToLogin);

        btnSendCode.setOnClickListener(v -> sendCode());
        btnBackToLogin.setOnClickListener(v -> finish());
    }

    private void sendCode() {
        String email = etEmail.getText().toString().trim();
        if (email.isEmpty()) { toast("Enter your account email"); return; }

        setLoading(true);
        ApiClient.get().forgotPassword(new Models.EmailRequest(email))
                .enqueue(new Callback<Models.MessageResponse>() {
                    @Override
                    public void onResponse(Call<Models.MessageResponse> c, Response<Models.MessageResponse> res) {
                        setLoading(false);
                        if (res.isSuccessful()) {
                            Intent i = new Intent(ForgotPasswordActivity.this, ResetPasswordActivity.class);
                            i.putExtra("email", email);
                            startActivity(i);
                        } else {
                            String msg = "Could not send reset code";
                            try {
                                if (res.errorBody() != null) {
                                    Models.MessageResponse err = new Gson().fromJson(
                                            res.errorBody().string(), Models.MessageResponse.class);
                                    if (err != null && err.error != null) msg = err.error;
                                }
                            } catch (Exception ignored) {}
                            toast(msg);
                        }
                    }
                    @Override
                    public void onFailure(Call<Models.MessageResponse> c, Throwable t) {
                        setLoading(false);
                        toast("Network error: " + t.getMessage());
                    }
                });
    }

    private void setLoading(boolean b) { progress.setVisibility(b ? View.VISIBLE : View.GONE); }
    private void toast(String s) { Toast.makeText(this, s, Toast.LENGTH_LONG).show(); }
}
