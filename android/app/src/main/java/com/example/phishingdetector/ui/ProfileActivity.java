package com.example.phishingdetector.ui;

import android.app.Dialog;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.view.View;
import android.widget.ImageView;
import android.widget.ProgressBar;
import android.widget.Toast;

import androidx.activity.result.ActivityResultLauncher;
import androidx.activity.result.contract.ActivityResultContracts;
import androidx.appcompat.app.AppCompatActivity;

import com.bumptech.glide.Glide;
import com.example.phishingdetector.R;
import com.example.phishingdetector.api.ApiClient;
import com.example.phishingdetector.api.Models;
import com.example.phishingdetector.util.SessionManager;
import com.google.android.material.appbar.MaterialToolbar;
import com.google.android.material.bottomnavigation.BottomNavigationView;
import com.google.android.material.textfield.TextInputEditText;

import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;

import okhttp3.MediaType;
import okhttp3.MultipartBody;
import okhttp3.RequestBody;
import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

public class ProfileActivity extends AppCompatActivity {

    private TextInputEditText etName, etEmail, etPhone, etBio;
    private ImageView imgProfile;
    private ProgressBar progress;
    private SessionManager session;
    private Object currentPhotoSource; // Uri of a freshly picked photo, or the server image URL string

    private final ActivityResultLauncher<String> pickImage =
            registerForActivityResult(new ActivityResultContracts.GetContent(), uri -> {
                if (uri != null) {
                    imgProfile.setPadding(0, 0, 0, 0);
                    imgProfile.setImageURI(uri);
                    currentPhotoSource = uri;
                    uploadImage(uri);
                }
            });

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_profile);
        session = new SessionManager(this);

        MaterialToolbar toolbar = findViewById(R.id.toolbar);
        toolbar.setNavigationOnClickListener(v -> finish());

        etName = findViewById(R.id.etName);
        etEmail = findViewById(R.id.etEmail);
        etPhone = findViewById(R.id.etPhone);
        etBio = findViewById(R.id.etBio);
        imgProfile = findViewById(R.id.imgProfile);
        progress = findViewById(R.id.progress);

        findViewById(R.id.btnPickImage).setOnClickListener(v -> pickImage.launch("image/*"));
        imgProfile.setOnClickListener(v -> showFullPhoto());
        findViewById(R.id.btnSave).setOnClickListener(v -> saveProfile());
        findViewById(R.id.btnLogout).setOnClickListener(v -> logout());

        BottomNavigationView bottomNav = findViewById(R.id.bottomNav);
        bottomNav.setSelectedItemId(R.id.nav_profile);
        bottomNav.setOnItemSelectedListener(item -> {
            int id = item.getItemId();
            if (id == R.id.nav_home) {
                startActivity(new Intent(this, HomeActivity.class));
                overridePendingTransition(0, 0);
                finish();
                return true;
            } else if (id == R.id.nav_history) {
                startActivity(new Intent(this, HistoryActivity.class));
                overridePendingTransition(0, 0);
                return true;
            }
            return true;
        });

        loadProfile();
    }

    private void loadProfile() {
        setLoading(true);
        ApiClient.get().getProfile(session.bearer())
                .enqueue(new Callback<Models.MessageResponse>() {
                    @Override
                    public void onResponse(Call<Models.MessageResponse> c, Response<Models.MessageResponse> res) {
                        setLoading(false);
                        Models.MessageResponse body = res.body();
                        if (body != null && body.user != null) {
                            Models.User u = body.user;
                            etName.setText(u.fullName);
                            etEmail.setText(u.email);
                            etPhone.setText(u.phone);
                            etBio.setText(u.bio);
                            if (u.profileImage != null) {
                                imgProfile.setPadding(0, 0, 0, 0);
                                currentPhotoSource = ApiClient.BASE_URL + "uploads/" + u.profileImage;
                                Glide.with(ProfileActivity.this)
                                        .load(currentPhotoSource)
                                        .circleCrop()
                                        .into(imgProfile);
                            }
                        }
                    }
                    @Override
                    public void onFailure(Call<Models.MessageResponse> c, Throwable t) {
                        setLoading(false);
                        toast("Could not load profile: " + t.getMessage());
                    }
                });
    }

    private void saveProfile() {
        Models.ProfileUpdate u = new Models.ProfileUpdate();
        u.fullName = etName.getText().toString().trim();
        u.phone = etPhone.getText().toString().trim();
        u.bio = etBio.getText().toString().trim();
        setLoading(true);
        ApiClient.get().updateProfile(session.bearer(), u)
                .enqueue(new Callback<Models.MessageResponse>() {
                    @Override
                    public void onResponse(Call<Models.MessageResponse> c, Response<Models.MessageResponse> res) {
                        setLoading(false);
                        toast("Profile saved");
                    }
                    @Override
                    public void onFailure(Call<Models.MessageResponse> c, Throwable t) {
                        setLoading(false);
                        toast("Save failed: " + t.getMessage());
                    }
                });
    }

    private void uploadImage(Uri uri) {
        try {
            File temp = new File(getCacheDir(), "upload.jpg");
            try (InputStream in = getContentResolver().openInputStream(uri);
                 FileOutputStream out = new FileOutputStream(temp)) {
                byte[] buf = new byte[8192];
                int n;
                while ((n = in.read(buf)) > 0) out.write(buf, 0, n);
            }
            RequestBody rb = RequestBody.create(temp, MediaType.parse("image/*"));
            MultipartBody.Part part = MultipartBody.Part.createFormData("image", "profile.jpg", rb);
            setLoading(true);
            ApiClient.get().uploadImage(session.bearer(), part)
                    .enqueue(new Callback<Models.MessageResponse>() {
                        @Override
                        public void onResponse(Call<Models.MessageResponse> c, Response<Models.MessageResponse> res) {
                            setLoading(false);
                            toast("Photo updated");
                        }
                        @Override
                        public void onFailure(Call<Models.MessageResponse> c, Throwable t) {
                            setLoading(false);
                            toast("Upload failed: " + t.getMessage());
                        }
                    });
        } catch (Exception e) {
            toast("Could not read image: " + e.getMessage());
        }
    }

    private void showFullPhoto() {
        if (currentPhotoSource == null) {
            toast("No photo yet. Tap Change Photo to add one.");
            return;
        }
        View view = getLayoutInflater().inflate(R.layout.dialog_photo_view, null);
        ImageView imgFull = view.findViewById(R.id.imgFull);
        Glide.with(this).load(currentPhotoSource).into(imgFull);

        Dialog dialog = new Dialog(this, android.R.style.Theme_Black_NoTitleBar_Fullscreen);
        dialog.setContentView(view);
        view.setOnClickListener(v -> dialog.dismiss());
        view.findViewById(R.id.btnCloseFull).setOnClickListener(v -> dialog.dismiss());
        dialog.show();
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
