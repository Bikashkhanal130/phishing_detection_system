package com.example.phishingdetector.ui;

import android.content.Intent;
import android.os.Bundle;
import android.view.View;
import android.widget.ProgressBar;
import android.widget.TextView;
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

public class OtpActivity extends AppCompatActivity {

    private TextInputEditText etCode;
    private ProgressBar progress;
    private SessionManager session;
    private String email;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_otp);
        session = new SessionManager(this);
        email = getIntent().getStringExtra("email");

        etCode = findViewById(R.id.etCode);
        progress = findViewById(R.id.progress);
        TextView subtitle = findViewById(R.id.tvSubtitle);
        subtitle.setText("Enter the 6-digit code sent to\n" + email);

        findViewById(R.id.btnVerify).setOnClickListener(v -> verify());
        findViewById(R.id.btnResend).setOnClickListener(v -> resend());
    }

    private void verify() {
        String code = etCode.getText().toString().trim();
        if (code.length() < 4) { toast("Enter the code"); return; }
        setLoading(true);
        ApiClient.get().verifyOtp(new Models.VerifyRequest(email, code))
                .enqueue(new Callback<Models.AuthResponse>() {
                    @Override
                    public void onResponse(Call<Models.AuthResponse> c, Response<Models.AuthResponse> res) {
                        setLoading(false);
                        Models.AuthResponse body = res.body();
                        if (res.isSuccessful() && body != null && body.token != null) {
                            session.save(body.token, body.user.fullName, body.user.email);
                            Intent i = new Intent(OtpActivity.this, HomeActivity.class);
                            i.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TASK);
                            startActivity(i);
                            finish();
                        } else {
                            toast(body != null && body.error != null ? body.error : "Verification failed");
                        }
                    }
                    @Override
                    public void onFailure(Call<Models.AuthResponse> c, Throwable t) {
                        setLoading(false);
                        toast("Network error: " + t.getMessage());
                    }
                });
    }

    private void resend() {
        ApiClient.get().resendOtp(new Models.EmailRequest(email))
                .enqueue(new Callback<Models.MessageResponse>() {
                    @Override
                    public void onResponse(Call<Models.MessageResponse> c, Response<Models.MessageResponse> r) {
                        toast("A new code was sent");
                    }
                    @Override
                    public void onFailure(Call<Models.MessageResponse> c, Throwable t) {
                        toast("Could not resend: " + t.getMessage());
                    }
                });
    }

    private void setLoading(boolean b) { progress.setVisibility(b ? View.VISIBLE : View.GONE); }
    private void toast(String s) { Toast.makeText(this, s, Toast.LENGTH_LONG).show(); }
}
