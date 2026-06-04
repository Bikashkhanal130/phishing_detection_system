package com.example.phishingdetector.ui;

import android.content.Intent;
import android.graphics.Color;
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

public class HomeActivity extends AppCompatActivity {

    private TextInputEditText etUrl;
    private ProgressBar progress;
    private View resultCard;
    private TextView tvResult, tvConfidence, tvCheckedUrl, tvWelcome;
    private SessionManager session;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_home);
        session = new SessionManager(this);

        etUrl = findViewById(R.id.etUrl);
        progress = findViewById(R.id.progress);
        resultCard = findViewById(R.id.resultCard);
        tvResult = findViewById(R.id.tvResult);
        tvConfidence = findViewById(R.id.tvConfidence);
        tvCheckedUrl = findViewById(R.id.tvCheckedUrl);
        tvWelcome = findViewById(R.id.tvWelcome);
        tvWelcome.setText("Welcome, " + session.getName());

        findViewById(R.id.btnCheck).setOnClickListener(v -> checkUrl());
        findViewById(R.id.btnHistory).setOnClickListener(v ->
                startActivity(new Intent(this, HistoryActivity.class)));
        findViewById(R.id.btnProfile).setOnClickListener(v ->
                startActivity(new Intent(this, ProfileActivity.class)));
        findViewById(R.id.btnLogout).setOnClickListener(v -> logout());
    }

    private void checkUrl() {
        String url = etUrl.getText().toString().trim();
        if (url.isEmpty()) { toast("Enter a URL"); return; }
        setLoading(true);
        resultCard.setVisibility(View.GONE);

        ApiClient.get().predict(session.bearer(), new Models.PredictRequest(url))
                .enqueue(new Callback<Models.PredictResponse>() {
                    @Override
                    public void onResponse(Call<Models.PredictResponse> c, Response<Models.PredictResponse> res) {
                        setLoading(false);
                        Models.PredictResponse body = res.body();
                        if (res.isSuccessful() && body != null && body.error == null) {
                            showResult(body);
                        } else if (res.code() == 401) {
                            toast("Session expired, please log in again");
                            logout();
                        } else {
                            toast(body != null && body.error != null ? body.error : "Check failed");
                        }
                    }
                    @Override
                    public void onFailure(Call<Models.PredictResponse> c, Throwable t) {
                        setLoading(false);
                        toast("Network error: " + t.getMessage());
                    }
                });
    }

    private void showResult(Models.PredictResponse r) {
        resultCard.setVisibility(View.VISIBLE);
        boolean phishing = r.isPhishing;
        int color = phishing ? Color.parseColor("#C0392B") : Color.parseColor("#1E8E3E");
        tvResult.setText(phishing ? "⚠ Phishing / Scam" : "✓ Safe");
        tvResult.setTextColor(color);
        tvConfidence.setText("Confidence: " + String.format("%.1f", r.confidence) + "%");
        tvCheckedUrl.setText(r.url);
    }

    private void logout() {
        session.logout();
        Intent i = new Intent(this, LoginActivity.class);
        i.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TASK);
        startActivity(i);
        finish();
    }

    private void setLoading(boolean b) { progress.setVisibility(b ? View.VISIBLE : View.GONE); }
    private void toast(String s) { Toast.makeText(this, s, Toast.LENGTH_LONG).show(); }
}
