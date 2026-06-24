package com.phishguard.app.ml;

import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Extracts the 15 numeric features from a URL string.
 *
 * THIS MUST STAY BYTE-FOR-BYTE IN SYNC WITH the Python feature_extractor.py
 * used to train the model. Any divergence means the ONNX model receives
 * different inputs on-device than it was trained on.
 *
 * Feature order (index : name):
 *   [0]  url_length
 *   [1]  num_dots
 *   [2]  num_hyphens
 *   [3]  num_underscores
 *   [4]  num_slashes
 *   [5]  num_questionmarks
 *   [6]  num_equals
 *   [7]  num_at
 *   [8]  num_ampersand
 *   [9]  has_ip_address      (0f / 1f)
 *   [10] is_https            (0f / 1f)
 *   [11] domain_length
 *   [12] num_subdomains
 *   [13] has_suspicious_keywords (0f / 1f)
 *   [14] has_numbers_in_domain   (0f / 1f)
 */
public final class FeatureExtractor {

    public static final int FEATURE_COUNT = 15;

    /** Keep this list identical (and lowercase) to SUSPICIOUS_KEYWORDS in Python. */
    private static final String[] SUSPICIOUS_KEYWORDS = {
            "login", "verify", "account", "secure", "update", "confirm", "banking", "paypal"
    };

    private static final Pattern IP_REGEX =
            Pattern.compile("(\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\.\\d{1,3})");

    private FeatureExtractor() {}

    /**
     * Extract the 15 features. Returns float[15] of zeros on any parse error,
     * matching the Python contract.
     */
    public static float[] extractFeatures(String url) {
        try {
            if (url == null) {
                url = "";
            }
            url = url.trim();
            String lower = url.toLowerCase();

            String host = extractHost(url);

            float urlLength = url.length();
            float numDots = count(url, '.');
            float numHyphens = count(url, '-');
            float numUnderscores = count(url, '_');
            float numSlashes = count(url, '/');
            float numQuestionmarks = count(url, '?');
            float numEquals = count(url, '=');
            float numAt = count(url, '@');
            float numAmpersand = count(url, '&');

            Matcher ipMatcher = IP_REGEX.matcher(url);
            float hasIp = ipMatcher.find() ? 1f : 0f;

            float isHttps = lower.startsWith("https://") ? 1f : 0f;

            float domainLength = host.length();

            // num_subdomains = max(0, (count of dot-separated host parts) - 2)
            // Use limit -1 so trailing empty parts are kept, matching Python's
            // str.split(".") behaviour exactly.
            float numSubdomains = 0f;
            if (!host.isEmpty()) {
                String[] parts = host.split("\\.", -1);
                numSubdomains = Math.max(0, parts.length - 2);
            }

            float hasSuspicious = 0f;
            for (String kw : SUSPICIOUS_KEYWORDS) {
                if (lower.contains(kw)) {
                    hasSuspicious = 1f;
                    break;
                }
            }

            float hasNumbersInDomain = 0f;
            for (int i = 0; i < host.length(); i++) {
                if (Character.isDigit(host.charAt(i))) {
                    hasNumbersInDomain = 1f;
                    break;
                }
            }

            return new float[]{
                    urlLength,
                    numDots,
                    numHyphens,
                    numUnderscores,
                    numSlashes,
                    numQuestionmarks,
                    numEquals,
                    numAt,
                    numAmpersand,
                    hasIp,
                    isHttps,
                    domainLength,
                    numSubdomains,
                    hasSuspicious,
                    hasNumbersInDomain
            };
        } catch (Exception e) {
            // Mirror Python: return float[15]{0f} on any error.
            return new float[FEATURE_COUNT];
        }
    }

    /**
     * Extract the host/domain part of a URL. Mirrors Python _extract_host:
     * strip scheme, cut at first '/','?','#', strip userinfo and port.
     */
    private static String extractHost(String url) {
        if (url == null) {
            return "";
        }
        String work = url.trim();

        int schemeIdx = work.indexOf("://");
        if (schemeIdx != -1) {
            work = work.substring(schemeIdx + 3);
        }

        work = cutAtAny(work, '/', '?', '#');

        int atIdx = work.indexOf('@');
        if (atIdx != -1) {
            work = work.substring(atIdx + 1);
        }

        int colonIdx = work.indexOf(':');
        if (colonIdx != -1) {
            work = work.substring(0, colonIdx);
        }

        return work;
    }

    private static String cutAtAny(String s, char... seps) {
        int cut = -1;
        for (char sep : seps) {
            int idx = s.indexOf(sep);
            if (idx != -1 && (cut == -1 || idx < cut)) {
                cut = idx;
            }
        }
        return cut == -1 ? s : s.substring(0, cut);
    }

    private static int count(String s, char c) {
        int n = 0;
        for (int i = 0; i < s.length(); i++) {
            if (s.charAt(i) == c) {
                n++;
            }
        }
        return n;
    }

    /** Helper used by the scan flow to record the domain alongside the result. */
    public static String getDomain(String url) {
        return extractHost(url);
    }
}
