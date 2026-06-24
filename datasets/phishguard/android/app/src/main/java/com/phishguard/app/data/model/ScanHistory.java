package com.phishguard.app.data.model;

import com.google.gson.annotations.SerializedName;

/** A single scan record from GET /api/scans/history. */
public class ScanHistory {
    private Long id;
    private String url;

    @SerializedName("is_phishing")
    private boolean isPhishing;

    private float confidence;

    @SerializedName("scanned_at")
    private String scannedAt;

    private String domain;

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public String getUrl() { return url; }
    public void setUrl(String url) { this.url = url; }

    public boolean isPhishing() { return isPhishing; }
    public void setPhishing(boolean phishing) { isPhishing = phishing; }

    public float getConfidence() { return confidence; }
    public void setConfidence(float confidence) { this.confidence = confidence; }

    public String getScannedAt() { return scannedAt; }
    public void setScannedAt(String scannedAt) { this.scannedAt = scannedAt; }

    public String getDomain() { return domain; }
    public void setDomain(String domain) { this.domain = domain; }
}
