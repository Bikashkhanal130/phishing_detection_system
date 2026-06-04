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

import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

public class RegisterActivity extends AppCompatActivity {

    private TextInputEditText etName, etEmail, etPassword;
    private ProgressBar progress;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_register);

        etName = findViewById(R.id.etName);
        etEmail = findViewById(R.id.etEmail);
        etPassword = findViewById(R.id.etPassword);
        progress = findViewById(R.id.progress);

        MaterialButton btnRegister = findViewById(R.id.btnRegister);
        MaterialButton btnGoLogin = findViewById(R.id.btnGoLogin);

        btnRegister.setOnClickListener(v -> doRegister());
        btnGoLogin.setOnClickListener(v -> finish());
    }

    private void doRegister() {
        String name = etName.getText().toString().trim();
        String email = etEmail.getText().toString().trim();
        String pass = etPassword.getText().toString();

        if (name.isEmpty() || email.isEmpty() || pass.length() < 6) {
            toast("Fill all fields. Password must be 6+ characters.");
            return;
        }
        setLoading(true);
        ApiClient.get().register(new Models.RegisterRequest(name, email, pass))
                .enqueue(new Callback<Models.MessageResponse>() {
                    @Override
                    public void onResponse(Call<Models.MessageResponse> c, Response<Models.MessageResponse> res) {
                        setLoading(false);
                        Models.MessageResponse body = res.body();
                        if (res.isSuccessful() && body != null && body.error == null) {
                            toast("Code sent to your email");
                            Intent i = new Intent(RegisterActivity.this, OtpActivity.class);
                            i.putExtra("email", email);
                            startActivity(i);
                            finish();
                        } else {
                            toast(body != null && body.error != null ? body.error : "Registration failed");
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
