package com.phishguard.app.data.model;

import com.google.gson.annotations.SerializedName;

/** Body for POST /api/scans. */
public class ScanRequest {
    private String url;

    @SerializedName("is_phishing")
    private boolean isPhishing;

    private float confidence;
    private String domain;

    public ScanRequest(String url, boolean isPhishing, float confidence, String domain) {
        this.url = url;
        this.isPhishing = isPhishing;
        this.confidence = confidence;
        this.domain = domain;
    }

    public String getUrl() { return url; }
    public void setUrl(String url) { this.url = url; }

    public boolean isPhishing() { return isPhishing; }
    public void setPhishing(boolean phishing) { isPhishing = phishing; }

    public float getConfidence() { return confidence; }
    public void setConfidence(float confidence) { this.confidence = confidence; }

    public String getDomain() { return domain; }
    public void setDomain(String domain) { this.domain = domain; }
}
