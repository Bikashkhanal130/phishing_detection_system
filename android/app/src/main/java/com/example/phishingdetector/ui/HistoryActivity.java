package com.example.phishingdetector.ui;

import android.content.ContentValues;
import android.content.Intent;
import android.os.Bundle;
import android.os.Environment;
import android.provider.MediaStore;
import android.net.Uri;
import android.view.View;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.TextView;
import android.widget.Toast;

import androidx.appcompat.app.AlertDialog;
import androidx.appcompat.app.AppCompatActivity;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;

import com.example.phishingdetector.R;
import com.example.phishingdetector.api.ApiClient;
import com.example.phishingdetector.api.Models;
import com.example.phishingdetector.util.SessionManager;
import com.google.android.material.appbar.MaterialToolbar;
import com.google.android.material.bottomnavigation.BottomNavigationView;

import java.io.OutputStream;
import java.util.ArrayList;
import java.util.List;

import okhttp3.ResponseBody;
import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

public class HistoryActivity extends AppCompatActivity {

    private RecyclerView recycler;
    private ProgressBar progress;
    private LinearLayout layoutEmpty;
    private SessionManager session;
    private final List<Models.HistoryItem> items = new ArrayList<>();

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        setContentView(R.layout.activity_history);
        session = new SessionManager(this);

        MaterialToolbar toolbar = findViewById(R.id.toolbar);
        toolbar.setNavigationOnClickListener(v -> finish());

        recycler = findViewById(R.id.recycler);
        progress = findViewById(R.id.progress);
        layoutEmpty = findViewById(R.id.layoutEmpty);
        recycler.setLayoutManager(new LinearLayoutManager(this));
        recycler.setAdapter(new HistoryAdapter(items));

        findViewById(R.id.btnDownloadPdf).setOnClickListener(v -> downloadPdf());

        BottomNavigationView bottomNav = findViewById(R.id.bottomNav);
        bottomNav.setSelectedItemId(R.id.nav_history);
        bottomNav.setOnItemSelectedListener(item -> {
            int id = item.getItemId();
            if (id == R.id.nav_home) {
                startActivity(new Intent(this, HomeActivity.class));
                overridePendingTransition(0, 0);
                finish();
                return true;
            } else if (id == R.id.nav_profile) {
                startActivity(new Intent(this, ProfileActivity.class));
                overridePendingTransition(0, 0);
                return true;
            }
            return true;
        });

        loadHistory();
    }

    private void loadHistory() {
        setLoading(true);
        ApiClient.get().history(session.bearer())
                .enqueue(new Callback<Models.HistoryResponse>() {
                    @Override
                    public void onResponse(Call<Models.HistoryResponse> c, Response<Models.HistoryResponse> res) {
                        setLoading(false);
                        Models.HistoryResponse body = res.body();
                        if (body != null && body.history != null) {
                            items.clear();
                            items.addAll(body.history);
                            recycler.getAdapter().notifyDataSetChanged();
                            layoutEmpty.setVisibility(items.isEmpty() ? View.VISIBLE : View.GONE);
                            recycler.setVisibility(items.isEmpty() ? View.GONE : View.VISIBLE);
                        }
                    }
                    @Override
                    public void onFailure(Call<Models.HistoryResponse> c, Throwable t) {
                        setLoading(false);
                        toast("Could not load history: " + t.getMessage());
                    }
                });
    }

    private void downloadPdf() {
        setLoading(true);
        ApiClient.get().historyPdf(session.bearer())
                .enqueue(new Callback<ResponseBody>() {
                    @Override
                    public void onResponse(Call<ResponseBody> c, Response<ResponseBody> res) {
                        setLoading(false);
                        if (res.isSuccessful() && res.body() != null) {
                            savePdfToDownloads(res.body());
                        } else {
                            toast("Download failed");
                        }
                    }
                    @Override
                    public void onFailure(Call<ResponseBody> c, Throwable t) {
                        setLoading(false);
                        toast("Download error: " + t.getMessage());
                    }
                });
    }

    private void savePdfToDownloads(ResponseBody body) {
        String fileName = "scan_history_" + System.currentTimeMillis() + ".pdf";
        try {
            ContentValues values = new ContentValues();
            values.put(MediaStore.Downloads.DISPLAY_NAME, fileName);
            values.put(MediaStore.Downloads.MIME_TYPE, "application/pdf");
            values.put(MediaStore.Downloads.RELATIVE_PATH, Environment.DIRECTORY_DOWNLOADS);

            Uri uri = getContentResolver().insert(MediaStore.Downloads.EXTERNAL_CONTENT_URI, values);
            if (uri == null) { toast("Could not create file"); return; }

            try (OutputStream out = getContentResolver().openOutputStream(uri)) {
                out.write(body.bytes());
            }

            // Offer to open the file immediately after download
            new AlertDialog.Builder(this)
                    .setTitle("Download complete")
                    .setMessage(fileName + "\nSaved to Downloads folder.")
                    .setPositiveButton("Open", (d, w) -> openPdf(uri))
                    .setNegativeButton("Cancel", null)
                    .show();

        } catch (Exception e) {
            toast("Save failed: " + e.getMessage());
        }
    }

    private void openPdf(Uri uri) {
        try {
            Intent intent = new Intent(Intent.ACTION_VIEW);
            intent.setDataAndType(uri, "application/pdf");
            intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
            startActivity(Intent.createChooser(intent, "Open PDF with…"));
        } catch (Exception e) {
            toast("No PDF viewer found. File is in your Downloads folder.");
        }
    }

    private void setLoading(boolean b) { progress.setVisibility(b ? View.VISIBLE : View.GONE); }
    private void toast(String s) { Toast.makeText(this, s, Toast.LENGTH_LONG).show(); }
}
