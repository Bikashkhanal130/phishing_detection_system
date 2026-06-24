package com.phishguard.app.ui.profile;

import android.content.ContentValues;
import android.content.Intent;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Environment;
import android.provider.MediaStore;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.TextView;
import android.widget.Toast;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.core.content.FileProvider;
import androidx.fragment.app.Fragment;
import androidx.recyclerview.widget.ItemTouchHelper;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;

import com.phishguard.app.R;
import com.phishguard.app.data.local.TokenManager;
import com.phishguard.app.data.model.MessageResponse;
import com.phishguard.app.data.model.ProfileResponse;
import com.phishguard.app.data.model.ScanHistory;
import com.phishguard.app.data.model.ScanHistoryPage;
import com.phishguard.app.data.remote.ApiService;
import com.phishguard.app.data.remote.RetrofitClient;
import com.phishguard.app.databinding.FragmentProfileBinding;

import java.io.File;
import java.io.FileOutputStream;
import java.io.OutputStream;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

import okhttp3.ResponseBody;
import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

/**
 * Profile tab: user card, stats, scan-history RecyclerView with swipe-to-delete,
 * and a "Download PDF" button that streams the export and saves to Downloads.
 */
public class ProfileFragment extends Fragment {

    private FragmentProfileBinding binding;
    private ApiService api;
    private TokenManager tokenManager;
    private ScanHistoryAdapter adapter;
    private final ExecutorService io = Executors.newSingleThreadExecutor();

    @Nullable
    @Override
    public View onCreateView(@NonNull LayoutInflater inflater, @Nullable ViewGroup container,
                             @Nullable Bundle savedInstanceState) {
        binding = FragmentProfileBinding.inflate(inflater, container, false);
        return binding.getRoot();
    }

    @Override
    public void onViewCreated(@NonNull View view, @Nullable Bundle savedInstanceState) {
        super.onViewCreated(view, savedInstanceState);
        api = RetrofitClient.getApiService(requireContext());
        tokenManager = TokenManager.getInstance(requireContext());

        // Stat labels.
        setStat(binding.statTotal.getRoot(), "0", getString(R.string.total_scans));
        setStat(binding.statPhishing.getRoot(), "0", getString(R.string.phishing_found));
        setStat(binding.statSafe.getRoot(), "0", getString(R.string.safe_urls));

        adapter = new ScanHistoryAdapter();
        binding.recycler.setLayoutManager(new LinearLayoutManager(requireContext()));
        binding.recycler.setAdapter(adapter);
        attachSwipeToDelete();

        binding.btnDownloadPdf.setOnClickListener(v -> downloadPdf());

        loadProfile();
        loadHistory();
    }

    private void setStat(View statRoot, String value, String label) {
        ((TextView) statRoot.findViewById(R.id.tvStatValue)).setText(value);
        ((TextView) statRoot.findViewById(R.id.tvStatLabel)).setText(label);
    }

    private void loadProfile() {
        api.getProfile().enqueue(new Callback<ProfileResponse>() {
            @Override
            public void onResponse(Call<ProfileResponse> call, Response<ProfileResponse> response) {
                if (binding == null) return;
                if (response.isSuccessful() && response.body() != null) {
                    ProfileResponse p = response.body();
                    String name = p.getName() == null ? "User" : p.getName();
                    binding.tvName.setText(name);
                    binding.tvEmail.setText(p.getEmail());
                    binding.tvAvatar.setText(initials(name));
                    if (p.getCreatedAt() != null) {
                        binding.tvJoined.setText("Joined " + p.getCreatedAt().substring(0, Math.min(10, p.getCreatedAt().length())));
                    }
                    setStat(binding.statTotal.getRoot(), String.valueOf(p.getTotalScans()), getString(R.string.total_scans));
                    setStat(binding.statPhishing.getRoot(), String.valueOf(p.getPhishingCount()), getString(R.string.phishing_found));
                    setStat(binding.statSafe.getRoot(), String.valueOf(p.getSafeCount()), getString(R.string.safe_urls));
                }
            }

            @Override
            public void onFailure(Call<ProfileResponse> call, Throwable t) {
                if (getContext() != null) {
                    Toast.makeText(getContext(), "Failed to load profile", Toast.LENGTH_SHORT).show();
                }
            }
        });
    }

    private void loadHistory() {
        binding.progress.setVisibility(View.VISIBLE);
        api.getHistory(1, 50).enqueue(new Callback<ScanHistoryPage>() {
            @Override
            public void onResponse(Call<ScanHistoryPage> call, Response<ScanHistoryPage> response) {
                if (binding == null) return;
                binding.progress.setVisibility(View.GONE);
                if (response.isSuccessful() && response.body() != null) {
                    adapter.setItems(response.body().getItems());
                }
            }

            @Override
            public void onFailure(Call<ScanHistoryPage> call, Throwable t) {
                if (binding == null) return;
                binding.progress.setVisibility(View.GONE);
                Toast.makeText(requireContext(), "Failed to load history", Toast.LENGTH_SHORT).show();
            }
        });
    }

    private void attachSwipeToDelete() {
        ItemTouchHelper helper = new ItemTouchHelper(new ItemTouchHelper.SimpleCallback(
                0, ItemTouchHelper.LEFT) {
            @Override
            public boolean onMove(@NonNull RecyclerView rv, @NonNull RecyclerView.ViewHolder vh,
                                  @NonNull RecyclerView.ViewHolder target) {
                return false;
            }

            @Override
            public void onSwiped(@NonNull RecyclerView.ViewHolder viewHolder, int direction) {
                int pos = viewHolder.getAdapterPosition();
                ScanHistory item = adapter.getItem(pos);
                deleteScan(item, pos);
            }
        });
        helper.attachToRecyclerView(binding.recycler);
    }

    private void deleteScan(ScanHistory item, int pos) {
        api.deleteScan(item.getId()).enqueue(new Callback<MessageResponse>() {
            @Override
            public void onResponse(Call<MessageResponse> call, Response<MessageResponse> response) {
                if (binding == null) return;
                if (response.isSuccessful()) {
                    adapter.removeAt(pos);
                    loadProfile(); // refresh counts
                } else {
                    adapter.notifyItemChanged(pos); // restore row
                    Toast.makeText(requireContext(), "Delete failed (" + response.code() + ")", Toast.LENGTH_SHORT).show();
                }
            }

            @Override
            public void onFailure(Call<MessageResponse> call, Throwable t) {
                if (binding == null) return;
                adapter.notifyItemChanged(pos);
                Toast.makeText(requireContext(), "Network error", Toast.LENGTH_SHORT).show();
            }
        });
    }

    private void downloadPdf() {
        Toast.makeText(requireContext(), "Generating PDF...", Toast.LENGTH_SHORT).show();
        api.exportPdf().enqueue(new Callback<ResponseBody>() {
            @Override
            public void onResponse(Call<ResponseBody> call, Response<ResponseBody> response) {
                if (response.isSuccessful() && response.body() != null) {
                    final ResponseBody body = response.body();
                    io.execute(() -> savePdf(body));
                } else {
                    Toast.makeText(requireContext(), "Export failed (" + response.code() + ")", Toast.LENGTH_SHORT).show();
                }
            }

            @Override
            public void onFailure(Call<ResponseBody> call, Throwable t) {
                Toast.makeText(requireContext(), "Network error: " + t.getMessage(), Toast.LENGTH_SHORT).show();
            }
        });
    }

    /** Save the PDF bytes to the public Downloads folder, then offer to open it. */
    private void savePdf(ResponseBody body) {
        String name = tokenManager.getUserName() == null ? "user" : tokenManager.getUserName().replace(" ", "_");
        String fileName = "scan_history_" + name + ".pdf";

        try {
            byte[] bytes = body.bytes();

            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                // Scoped storage: write via MediaStore.Downloads.
                ContentValues values = new ContentValues();
                values.put(MediaStore.Downloads.DISPLAY_NAME, fileName);
                values.put(MediaStore.Downloads.MIME_TYPE, "application/pdf");
                values.put(MediaStore.Downloads.IS_PENDING, 1);

                Uri collection = MediaStore.Downloads.EXTERNAL_CONTENT_URI;
                Uri uri = requireContext().getContentResolver().insert(collection, values);
                if (uri == null) {
                    throw new Exception("Could not create download entry");
                }
                try (OutputStream os = requireContext().getContentResolver().openOutputStream(uri)) {
                    os.write(bytes);
                }
                values.clear();
                values.put(MediaStore.Downloads.IS_PENDING, 0);
                requireContext().getContentResolver().update(uri, values, null, null);

                postToMain(() -> {
                    Toast.makeText(requireContext(), "Saved to Downloads: " + fileName, Toast.LENGTH_LONG).show();
                    openPdf(uri);
                });
            } else {
                // API < 29: write to public Downloads dir, share via FileProvider.
                File downloads = Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOWNLOADS);
                if (!downloads.exists()) downloads.mkdirs();
                File out = new File(downloads, fileName);
                try (FileOutputStream fos = new FileOutputStream(out)) {
                    fos.write(bytes);
                }
                Uri uri = FileProvider.getUriForFile(requireContext(),
                        requireContext().getPackageName() + ".fileprovider", out);
                postToMain(() -> {
                    Toast.makeText(requireContext(), "Saved to Downloads: " + fileName, Toast.LENGTH_LONG).show();
                    openPdf(uri);
                });
            }
        } catch (Exception e) {
            postToMain(() -> Toast.makeText(requireContext(), "Save failed: " + e.getMessage(), Toast.LENGTH_LONG).show());
        }
    }

    private void openPdf(Uri uri) {
        Intent intent = new Intent(Intent.ACTION_VIEW);
        intent.setDataAndType(uri, "application/pdf");
        intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_ACTIVITY_NEW_TASK);
        try {
            startActivity(intent);
        } catch (Exception e) {
            Toast.makeText(requireContext(), "No PDF viewer installed", Toast.LENGTH_SHORT).show();
        }
    }

    private void postToMain(Runnable r) {
        if (getActivity() != null) {
            getActivity().runOnUiThread(r);
        }
    }

    private static String initials(String name) {
        if (name == null || name.trim().isEmpty()) {
            return "?";
        }
        String[] parts = name.trim().split("\\s+");
        if (parts.length == 1) {
            return parts[0].substring(0, 1).toUpperCase();
        }
        return (parts[0].substring(0, 1) + parts[1].substring(0, 1)).toUpperCase();
    }

    @Override
    public void onDestroyView() {
        super.onDestroyView();
        binding = null;
    }

    @Override
    public void onDestroy() {
        super.onDestroy();
        io.shutdown();
    }
}
