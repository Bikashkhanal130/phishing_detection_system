package com.example.phishingdetector.api;

import com.google.gson.annotations.SerializedName;
import java.util.List;

/**
 * All request/response shapes for the API, grouped as static nested classes.
 * e.g. Models.User, Models.AuthResponse, Models.PredictResponse
 */
public class Models {

    // ---------- requests ----------
    public static class RegisterRequest {
        @SerializedName("full_name") public String fullName;
        public String email;
        public String password;
        public RegisterRequest(String fullName, String email, String password) {
            this.fullName = fullName; this.email = email; this.password = password;
        }
    }

    public static class LoginRequest {
        public String email;
        public String password;
        public LoginRequest(String email, String password) {
            this.email = email; this.password = password;
        }
    }

    public static class VerifyRequest {
        public String email;
        public String code;
        public VerifyRequest(String email, String code) {
            this.email = email; this.code = code;
        }
    }

    public static class EmailRequest {
        public String email;
        public EmailRequest(String email) { this.email = email; }
    }

    public static class ResetPasswordRequest {
        public String email;
        public String code;
        @SerializedName("new_password") public String newPassword;
        public ResetPasswordRequest(String email, String code, String newPassword) {
            this.email = email; this.code = code; this.newPassword = newPassword;
        }
    }

    public static class PredictRequest {
        public String url;
        public PredictRequest(String url) { this.url = url; }
    }

    public static class ProfileUpdate {
        @SerializedName("full_name") public String fullName;
        public String phone;
        public String bio;
    }

    // ---------- responses ----------
    public static class User {
        public int id;
        @SerializedName("full_name") public String fullName;
        public String email;
        @SerializedName("is_verified") public boolean isVerified;
        public String phone;
        public String bio;
        @SerializedName("profile_image") public String profileImage;
    }

    public static class AuthResponse {
        public String message;
        public String token;
        public User user;
        public String error;
        @SerializedName("need_verification") public boolean needVerification;
        public String email;
    }

    public static class MessageResponse {
        public String message;
        public String error;
        public String email;
        @SerializedName("profile_image") public String profileImage;
        public User user;
    }

    public static class PredictResponse {
        public String url;
        public String result;                 // "Phishing" or "Safe"
        @SerializedName("is_phishing") public boolean isPhishing;
        public double confidence;             // 0..100
        @SerializedName("checked_at") public String checkedAt;
        public String error;
    }

    public static class HistoryItem {
        public int id;
        public String url;
        public String result;
        public double confidence;
        @SerializedName("created_at") public String createdAt;
    }

    public static class HistoryResponse {
        public List<HistoryItem> history;
        public int count;
        public String error;
    }
}
