package com.phishguard.app.data.model;

import com.google.gson.annotations.SerializedName;

/**
 * Response from GET /api/users/profile. The backend returns a flat object
 * (id, name, email, created_at, total_scans, phishing_count, safe_count).
 */
public class ProfileResponse {
    private Long id;
    private String name;
    private String email;

    @SerializedName("created_at")
    private String createdAt;

    @SerializedName("total_scans")
    private int totalScans;

    @SerializedName("phishing_count")
    private int phishingCount;

    @SerializedName("safe_count")
    private int safeCount;

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public String getName() { return name; }
    public void setName(String name) { this.name = name; }

    public String getEmail() { return email; }
    public void setEmail(String email) { this.email = email; }

    public String getCreatedAt() { return createdAt; }
    public void setCreatedAt(String createdAt) { this.createdAt = createdAt; }

    public int getTotalScans() { return totalScans; }
    public void setTotalScans(int totalScans) { this.totalScans = totalScans; }

    public int getPhishingCount() { return phishingCount; }
    public void setPhishingCount(int phishingCount) { this.phishingCount = phishingCount; }

    public int getSafeCount() { return safeCount; }
    public void setSafeCount(int safeCount) { this.safeCount = safeCount; }
}
