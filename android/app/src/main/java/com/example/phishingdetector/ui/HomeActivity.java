package com.example.phishingdetector.ui;

import android.content.Intent;
import android.graphics.Color;
import android.os.Bundle;
import android.view.View;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.TextView;
import android.widget.Toast;

import com.google.gson.Gson;

import androidx.appcompat.app.AppCompatActivity;

import com.example.phishingdetector.R;
import com.example.phishingdetector.api.ApiClient;
import com.example.phishingdetector.api.Models;
import com.example.phishingdetector.util.SessionManager;
import com.google.android.material.bottomnavigation.BottomNavigationView;
import com.google.android.material.textfield.TextInputEditText;

import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

public class HomeActivity extends AppCompatActivity {

    private TextInputEditText etUrl;
    private ProgressBar progress;
    private LinearLayout resultCard;
    private TextView tvResult, tvConfidence, tvCheckedUrl, tvWelcome, tvAvatar;
    private ImageView imgResultIcon;
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
        tvAvatar = findViewById(R.id.tvAvatar);
        imgResultIcon = findViewById(R.id.imgResultIcon);

        String name = session.getName();
        tvWelcome.setText("Welcome, " + name + "!");
        if (name != null && !name.isEmpty()) {
            tvAvatar.setText(String.valueOf(name.charAt(0)).toUpperCase());
        }

        findViewById(R.id.btnCheck).setOnClickListener(v -> checkUrl());

        BottomNavigationView bottomNav = findViewById(R.id.bottomNav);
        bottomNav.setSelectedItemId(R.id.nav_home);
        bottomNav.setOnItemSelectedListener(item -> {
            int id = item.getItemId();
            if (id == R.id.nav_history) {
                startActivity(new Intent(this, HistoryActivity.class));
                overridePendingTransition(0, 0);
                return true;
            } else if (id == R.id.nav_profile) {
                startActivity(new Intent(this, ProfileActivity.class));
                overridePendingTransition(0, 0);
                return true;
            }
            return true;
        });
    }

    private void checkUrl() {
        String raw = etUrl.getText().toString().trim();
        if (raw.isEmpty()) { toast("Enter a URL"); return; }

        // Auto-add scheme so bare domains like "google.com" work
        String url = raw.matches("(?i)^[a-z][a-z0-9+.\\-]*://.*") ? raw : "http://" + raw;

        setLoading(true);
        resultCard.setVisibility(View.GONE);

        ApiClient.get().predict(session.bearer(), new Models.PredictRequest(url))
                .enqueue(new Callback<Models.PredictResponse>() {
                    @Override
                    public void onResponse(Call<Models.PredictResponse> c, Response<Models.PredictResponse> res) {
                        setLoading(false);
                        if (res.isSuccessful()) {
                            Models.PredictResponse body = res.body();
                            if (body != null) showResult(body);
                        } else if (res.code() == 401) {
                            toast("Session expired, please log in again");
                            logout();
                        } else {
                            // For error responses (4xx/5xx) the body is in errorBody(), not body()
                            String msg = "Check failed";
                            try {
                                if (res.errorBody() != null) {
                                    Models.PredictResponse err = new Gson().fromJson(
                                            res.errorBody().string(), Models.PredictResponse.class);
                                    if (err != null && err.error != null) msg = err.error;
                                }
                            } catch (Exception ignored) {}
                            toast(msg);
                        }
                    }
                    @Override
                    public void onFailure(Call<Models.PredictResponse> c, Throwable t) {
                        setLoading(false);
                        toast("Could not reach server. Check your connection.");
                    }
                });
    }

    private void showResult(Models.PredictResponse r) {
        resultCard.setVisibility(View.VISIBLE);
        boolean phishing = r.isPhishing;

        if (phishing) {
            tvResult.setText("Phishing / Scam");
            tvResult.setTextColor(Color.parseColor("#C0392B"));
            imgResultIcon.setImageResource(R.drawable.ic_warning_circle);
            resultCard.setBackground(getDrawable(R.drawable.bg_result_danger));
        } else {
            tvResult.setText("Safe");
            tvResult.setTextColor(Color.parseColor("#1E8E3E"));
            imgResultIcon.setImageResource(R.drawable.ic_check_circle);
            resultCard.setBackground(getDrawable(R.drawable.bg_result_safe));
        }

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
