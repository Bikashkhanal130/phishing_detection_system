package com.phishguard.app.ui.auth;

import android.content.Intent;
import android.os.Bundle;
import android.os.CountDownTimer;
import android.text.Editable;
import android.text.TextUtils;
import android.text.TextWatcher;
import android.view.View;
import android.widget.EditText;
import android.widget.Toast;

import androidx.appcompat.app.AppCompatActivity;

import com.phishguard.app.data.local.TokenManager;
import com.phishguard.app.data.model.AuthResponse;
import com.phishguard.app.data.model.MessageResponse;
import com.phishguard.app.data.model.OtpRequest;
import com.phishguard.app.data.model.RegisterRequest;
import com.phishguard.app.data.model.SendOtpRequest;
import com.phishguard.app.data.remote.ApiService;
import com.phishguard.app.data.remote.RetrofitClient;
import com.phishguard.app.databinding.ActivityOtpVerifyBinding;
import com.phishguard.app.ui.main.MainActivity;

import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

/**
 * 6-box OTP entry with auto-advance and a 60s resend countdown. Verifies via
 * the login or register endpoint depending on the "purpose" extra.
 */
public class OtpVerifyActivity extends AppCompatActivity {

    public static final String EXTRA_EMAIL = "extra_email";
    public static final String EXTRA_NAME = "extra_name";
    public static final String EXTRA_PURPOSE = "extra_purpose"; // "login" | "register"

    private ActivityOtpVerifyBinding binding;
    private ApiService api;
    private TokenManager tokenManager;

    private String email;
    private String name;
    private String purpose;

    private EditText[] boxes;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        binding = ActivityOtpVerifyBinding.inflate(getLayoutInflater());
        setContentView(binding.getRoot());

        api = RetrofitClient.getApiService(this);
        tokenManager = TokenManager.getInstance(this);

        email = getIntent().getStringExtra(EXTRA_EMAIL);
        name = getIntent().getStringExtra(EXTRA_NAME);
        purpose = getIntent().getStringExtra(EXTRA_PURPOSE);

        binding.tvEmail.setText(getString(com.phishguard.app.R.string.code_sent_to, email));

        boxes = new EditText[]{
                binding.otp1, binding.otp2, binding.otp3,
                binding.otp4, binding.otp5, binding.otp6
        };
        setupAutoAdvance();

        binding.btnVerify.setOnClickListener(v -> verify());
        binding.tvResend.setOnClickListener(v -> resend());

        startResendCountdown();
    }

    private void setupAutoAdvance() {
        for (int i = 0; i < boxes.length; i++) {
            final int idx = i;
            boxes[i].addTextChangedListener(new TextWatcher() {
                @Override public void beforeTextChanged(CharSequence s, int a, int b, int c) {}
                @Override public void onTextChanged(CharSequence s, int a, int b, int c) {}

                @Override
                public void afterTextChanged(Editable s) {
                    if (s.length() == 1 && idx < boxes.length - 1) {
                        boxes[idx + 1].requestFocus();
                    } else if (s.length() == 0 && idx > 0) {
                        boxes[idx - 1].requestFocus();
                    }
                }
            });
        }
    }

    private String collectOtp() {
        StringBuilder sb = new StringBuilder();
        for (EditText box : boxes) {
            sb.append(box.getText() == null ? "" : box.getText().toString().trim());
        }
        return sb.toString();
    }

    private void verify() {
        String otp = collectOtp();
        if (otp.length() != 6) {
            Toast.makeText(this, "Enter the 6-digit code", Toast.LENGTH_SHORT).show();
            return;
        }
        setLoading(true);

        Call<AuthResponse> call = "register".equals(purpose)
                ? api.verifyRegisterOtp(new OtpRequest(email, otp))
                : api.verifyLoginOtp(new OtpRequest(email, otp));

        call.enqueue(new Callback<AuthResponse>() {
            @Override
            public void onResponse(Call<AuthResponse> call, Response<AuthResponse> response) {
                setLoading(false);
                if (response.isSuccessful() && response.body() != null) {
                    AuthResponse auth = response.body();
                    tokenManager.saveTokens(auth.getAccessToken(), auth.getRefreshToken());
                    if (auth.getUser() != null) {
                        tokenManager.saveUser(auth.getUser().getId(), auth.getUser().getName(), auth.getUser().getEmail());
                    }
                    goToMain();
                } else {
                    handleError(response.code());
                }
            }

            @Override
            public void onFailure(Call<AuthResponse> call, Throwable t) {
                setLoading(false);
                Toast.makeText(OtpVerifyActivity.this, "Network error: " + t.getMessage(), Toast.LENGTH_SHORT).show();
            }
        });
    }

    private void handleError(int code) {
        String msg;
        switch (code) {
            case 400:
                msg = "Invalid code. Please try again.";
                break;
            case 410:
                msg = "Code expired, please resend.";
                break;
            case 429:
                msg = "Too many wrong attempts. Please resend a new code.";
                break;
            case 404:
                msg = "No active code. Please resend.";
                break;
            default:
                msg = "Verification failed (" + code + ")";
        }
        Toast.makeText(this, msg, Toast.LENGTH_LONG).show();
        clearBoxes();
    }

    private void clearBoxes() {
        for (EditText b : boxes) {
            b.setText("");
        }
        boxes[0].requestFocus();
    }

    private void resend() {
        setLoading(true);
        Callback<MessageResponse> cb = new Callback<MessageResponse>() {
            @Override
            public void onResponse(Call<MessageResponse> call, Response<MessageResponse> response) {
                setLoading(false);
                if (response.isSuccessful()) {
                    Toast.makeText(OtpVerifyActivity.this, "Code resent", Toast.LENGTH_SHORT).show();
                    clearBoxes();
                    startResendCountdown();
                } else {
                    Toast.makeText(OtpVerifyActivity.this, "Resend failed (" + response.code() + ")", Toast.LENGTH_SHORT).show();
                }
            }

            @Override
            public void onFailure(Call<MessageResponse> call, Throwable t) {
                setLoading(false);
                Toast.makeText(OtpVerifyActivity.this, "Network error: " + t.getMessage(), Toast.LENGTH_SHORT).show();
            }
        };

        if ("register".equals(purpose)) {
            api.sendRegisterOtp(new RegisterRequest(name, email)).enqueue(cb);
        } else {
            api.sendLoginOtp(new SendOtpRequest(email)).enqueue(cb);
        }
    }

    private void startResendCountdown() {
        binding.tvResend.setEnabled(false);
        new CountDownTimer(60_000, 1_000) {
            @Override
            public void onTick(long millisUntilFinished) {
                binding.tvResend.setText("Resend code in " + (millisUntilFinished / 1000) + "s");
            }

            @Override
            public void onFinish() {
                binding.tvResend.setEnabled(true);
                binding.tvResend.setText(com.phishguard.app.R.string.resend_otp);
            }
        }.start();
    }

    private void goToMain() {
        Intent intent = new Intent(this, MainActivity.class);
        intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TASK);
        startActivity(intent);
        finish();
    }

    private void setLoading(boolean loading) {
        binding.progress.setVisibility(loading ? View.VISIBLE : View.GONE);
        binding.btnVerify.setEnabled(!loading);
    }
}
