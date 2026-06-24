package com.phishguard.app.ui.auth;

import android.content.Intent;
import android.os.Bundle;
import android.text.TextUtils;
import android.util.Patterns;
import android.view.View;
import android.widget.Toast;

import androidx.appcompat.app.AppCompatActivity;

import com.phishguard.app.data.model.MessageResponse;
import com.phishguard.app.data.model.RegisterRequest;
import com.phishguard.app.data.remote.ApiService;
import com.phishguard.app.data.remote.RetrofitClient;
import com.phishguard.app.databinding.ActivityRegisterBinding;

import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

/** Name + email registration. Sends an OTP, then navigates to OtpVerifyActivity. */
public class RegisterActivity extends AppCompatActivity {

    private ActivityRegisterBinding binding;
    private ApiService api;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        binding = ActivityRegisterBinding.inflate(getLayoutInflater());
        setContentView(binding.getRoot());

        api = RetrofitClient.getApiService(this);

        binding.btnSendOtp.setOnClickListener(v -> sendOtp());
        binding.tvGoLogin.setOnClickListener(v -> finish());
    }

    private void sendOtp() {
        String name = binding.etName.getText() == null ? "" : binding.etName.getText().toString().trim();
        String email = binding.etEmail.getText() == null ? "" : binding.etEmail.getText().toString().trim();

        if (TextUtils.isEmpty(name)) {
            binding.tilName.setError("Enter your name");
            return;
        }
        binding.tilName.setError(null);
        if (TextUtils.isEmpty(email) || !Patterns.EMAIL_ADDRESS.matcher(email).matches()) {
            binding.tilEmail.setError("Enter a valid email");
            return;
        }
        binding.tilEmail.setError(null);
        setLoading(true);

        api.sendRegisterOtp(new RegisterRequest(name, email)).enqueue(new Callback<MessageResponse>() {
            @Override
            public void onResponse(Call<MessageResponse> call, Response<MessageResponse> response) {
                setLoading(false);
                if (response.isSuccessful()) {
                    Intent intent = new Intent(RegisterActivity.this, OtpVerifyActivity.class);
                    intent.putExtra(OtpVerifyActivity.EXTRA_EMAIL, email);
                    intent.putExtra(OtpVerifyActivity.EXTRA_NAME, name);
                    intent.putExtra(OtpVerifyActivity.EXTRA_PURPOSE, "register");
                    startActivity(intent);
                } else if (response.code() == 409) {
                    Toast.makeText(RegisterActivity.this, "Email already registered. Please sign in.", Toast.LENGTH_LONG).show();
                } else {
                    Toast.makeText(RegisterActivity.this, "Failed to send OTP (" + response.code() + ")", Toast.LENGTH_SHORT).show();
                }
            }

            @Override
            public void onFailure(Call<MessageResponse> call, Throwable t) {
                setLoading(false);
                Toast.makeText(RegisterActivity.this, "Network error: " + t.getMessage(), Toast.LENGTH_SHORT).show();
            }
        });
    }

    private void setLoading(boolean loading) {
        binding.progress.setVisibility(loading ? View.VISIBLE : View.GONE);
        binding.btnSendOtp.setEnabled(!loading);
    }
}
