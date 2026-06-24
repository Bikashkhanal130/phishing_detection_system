package com.phishguard.app.ui.auth;

import android.content.Intent;
import android.os.Bundle;
import android.text.TextUtils;
import android.util.Patterns;
import android.view.View;
import android.widget.Toast;

import androidx.appcompat.app.AppCompatActivity;

import com.phishguard.app.data.model.MessageResponse;
import com.phishguard.app.data.model.SendOtpRequest;
import com.phishguard.app.data.remote.ApiService;
import com.phishguard.app.data.remote.RetrofitClient;
import com.phishguard.app.databinding.ActivityLoginBinding;

import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

/**
 * Email-only login. Sends an OTP, then navigates to OtpVerifyActivity.
 * No password fields anywhere.
 */
public class LoginActivity extends AppCompatActivity {

    private ActivityLoginBinding binding;
    private ApiService api;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        binding = ActivityLoginBinding.inflate(getLayoutInflater());
        setContentView(binding.getRoot());

        api = RetrofitClient.getApiService(this);

        binding.btnSendOtp.setOnClickListener(v -> sendOtp());
        binding.tvGoRegister.setOnClickListener(v ->
                startActivity(new Intent(this, RegisterActivity.class)));
    }

    private void sendOtp() {
        String email = binding.etEmail.getText() == null ? "" : binding.etEmail.getText().toString().trim();
        if (TextUtils.isEmpty(email) || !Patterns.EMAIL_ADDRESS.matcher(email).matches()) {
            binding.tilEmail.setError("Enter a valid email");
            return;
        }
        binding.tilEmail.setError(null);
        setLoading(true);

        api.sendLoginOtp(new SendOtpRequest(email)).enqueue(new Callback<MessageResponse>() {
            @Override
            public void onResponse(Call<MessageResponse> call, Response<MessageResponse> response) {
                setLoading(false);
                if (response.isSuccessful()) {
                    Intent intent = new Intent(LoginActivity.this, OtpVerifyActivity.class);
                    intent.putExtra(OtpVerifyActivity.EXTRA_EMAIL, email);
                    intent.putExtra(OtpVerifyActivity.EXTRA_PURPOSE, "login");
                    startActivity(intent);
                } else if (response.code() == 404) {
                    Toast.makeText(LoginActivity.this, "No account for this email. Please register.", Toast.LENGTH_LONG).show();
                } else {
                    Toast.makeText(LoginActivity.this, "Failed to send OTP (" + response.code() + ")", Toast.LENGTH_SHORT).show();
                }
            }

            @Override
            public void onFailure(Call<MessageResponse> call, Throwable t) {
                setLoading(false);
                Toast.makeText(LoginActivity.this, "Network error: " + t.getMessage(), Toast.LENGTH_SHORT).show();
            }
        });
    }

    private void setLoading(boolean loading) {
        binding.progress.setVisibility(loading ? View.VISIBLE : View.GONE);
        binding.btnSendOtp.setEnabled(!loading);
    }
}
