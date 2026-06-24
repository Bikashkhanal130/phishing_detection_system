package com.phishguard.app.ml;

/** POJO returned by PhishingDetector.predict(). */
public class PredictionResult {
    private boolean isPhishing;
    private float confidence;
    private String url;
    private long timestamp;

    public PredictionResult(boolean isPhishing, float confidence, String url, long timestamp) {
        this.isPhishing = isPhishing;
        this.confidence = confidence;
        this.url = url;
        this.timestamp = timestamp;
    }

    public boolean isPhishing() { return isPhishing; }
    public float getConfidence() { return confidence; }
    public String getUrl() { return url; }
    public long getTimestamp() { return timestamp; }

    /** Confidence as a 0-100 percentage. */
    public int getConfidencePercent() { return Math.round(confidence * 100f); }
}
