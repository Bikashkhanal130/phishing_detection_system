package com.example.phishingdetector.ui;

import android.content.Intent;
import android.os.Bundle;
import android.view.View;
import android.widget.ProgressBar;
import android.widget.TextView;
import android.widget.Toast;

import androidx.appcompat.app.AlertDialog;
import androidx.appcompat.app.AppCompatActivity;

import com.example.phishingdetector.R;
import com.example.phishingdetector.api.ApiClient;
import com.example.phishingdetector.api.Models;
import com.google.android.material.textfield.TextInputEditText;
import com.google.gson.Gson;

import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

public class ResetPasswordActivity extends AppCompatActivity {

    private TextInputEditText etCode, etNewPassword, etConfirmPassword;
    private ProgressBar progress;
    private String email;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_reset_password);
        email = getIntent().getStringExtra("email");

        etCode = findViewById(R.id.etCode);
        etNewPassword = findViewById(R.id.etNewPassword);
        etConfirmPassword = findViewById(R.id.etConfirmPassword);
        progress = findViewById(R.id.progress);
        TextView subtitle = findViewById(R.id.tvSubtitle);
        subtitle.setText("Enter the code sent to\n" + email + "\nthen choose a new password");

        findViewById(R.id.btnReset).setOnClickListener(v -> doReset());
        findViewById(R.id.btnResend).setOnClickListener(v -> resend());
    }

    private void doReset() {
        String code = etCode.getText().toString().trim();
        String newPassword = etNewPassword.getText().toString();
        String confirmPassword = etConfirmPassword.getText().toString();

        if (code.isEmpty()) { toast("Enter the code sent to your email"); return; }
        if (newPassword.length() < 6) { toast("Password must be at least 6 characters"); return; }
        if (!newPassword.equals(confirmPassword)) { toast("Passwords do not match"); return; }

        setLoading(true);
        ApiClient.get().resetPassword(new Models.ResetPasswordRequest(email, code, newPassword))
                .enqueue(new Callback<Models.MessageResponse>() {
                    @Override
                    public void onResponse(Call<Models.MessageResponse> c, Response<Models.MessageResponse> res) {
                        setLoading(false);
                        if (res.isSuccessful()) {
                            new AlertDialog.Builder(ResetPasswordActivity.this)
                                    .setTitle("Success")
                                    .setMessage("Your password has been reset. Please log in.")
                                    .setCancelable(false)
                                    .setPositiveButton("OK", (d, w) -> goToLogin())
                                    .show();
                        } else {
                            String msg = "Invalid or expired code";
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

    private void resend() {
        ApiClient.get().forgotPassword(new Models.EmailRequest(email))
                .enqueue(new Callback<Models.MessageResponse>() {
                    @Override
                    public void onResponse(Call<Models.MessageResponse> c, Response<Models.MessageResponse> r) {
                        toast("A new code was sent to your email");
                    }
                    @Override
                    public void onFailure(Call<Models.MessageResponse> c, Throwable t) {
                        toast("Could not resend: " + t.getMessage());
                    }
                });
    }

    private void goToLogin() {
        Intent i = new Intent(this, LoginActivity.class);
        i.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TASK);
        startActivity(i);
        finish();
    }

    private void setLoading(boolean b) { progress.setVisibility(b ? View.VISIBLE : View.GONE); }
    private void toast(String s) { Toast.makeText(this, s, Toast.LENGTH_LONG).show(); }
}
