package com.phishguard.app.ml;

import android.content.Context;
import android.util.Log;

import ai.onnxruntime.OnnxTensor;
import ai.onnxruntime.OnnxValue;
import ai.onnxruntime.OrtEnvironment;
import ai.onnxruntime.OrtException;
import ai.onnxruntime.OrtSession;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.nio.FloatBuffer;
import java.util.Collections;
import java.util.Map;

/**
 * Loads phishing_model.onnx from assets/ and runs inference.
 *
 * ONNX I/O contract (must match the exported model):
 *   input  "float_input"  : float32 [1, 15]
 *   output "label"        : int64   [1]      -> predicted class (0 legit, 1 phish)
 *   output "probabilities": float32 [1, 2]   -> [P(legit), P(phishing)]
 */
public class PhishingDetector {

    private static final String TAG = "PhishingDetector";
    private static final String MODEL_ASSET = "phishing_model.onnx";
    private static final String INPUT_NAME = "float_input";

    private final OrtEnvironment env;
    private OrtSession session;

    public PhishingDetector(Context context) throws OrtException, IOException {
        env = OrtEnvironment.getEnvironment();
        byte[] modelBytes = readAsset(context, MODEL_ASSET);
        OrtSession.SessionOptions opts = new OrtSession.SessionOptions();
        session = env.createSession(modelBytes, opts);
        Log.i(TAG, "ONNX session created. Inputs=" + session.getInputNames()
                + " Outputs=" + session.getOutputNames());
    }

    /**
     * Run the full pipeline for a URL: extract 15 features -> ONNX inference ->
     * PredictionResult. Never throws; returns a safe default on failure.
     */
    public PredictionResult predict(String url) {
        float[] features = FeatureExtractor.extractFeatures(url);
        long now = System.currentTimeMillis();

        // float[1][15] input tensor.
        float[][] input = new float[1][FeatureExtractor.FEATURE_COUNT];
        System.arraycopy(features, 0, input[0], 0, FeatureExtractor.FEATURE_COUNT);

        OnnxTensor inputTensor = null;
        OrtSession.Result result = null;
        try {
            inputTensor = OnnxTensor.createTensor(env, input);
            Map<String, OnnxTensor> inputs = Collections.singletonMap(INPUT_NAME, inputTensor);
            result = session.run(inputs);

            boolean isPhishing = false;
            float confidence = 0f;

            // ---- label output (int64 [1]) ----
            OnnxValue labelValue = result.get("label").orElse(null);
            if (labelValue != null) {
                Object lv = labelValue.getValue();
                if (lv instanceof long[]) {
                    isPhishing = ((long[]) lv)[0] == 1L;
                }
            }

            // ---- probabilities output (float [1][2]) ----
            OnnxValue probValue = result.get("probabilities").orElse(null);
            if (probValue != null) {
                Object pv = probValue.getValue();
                if (pv instanceof float[][]) {
                    float[] probs = ((float[][]) pv)[0];
                    float pLegit = probs.length > 0 ? probs[0] : 0f;
                    float pPhish = probs.length > 1 ? probs[1] : 0f;
                    // Confidence is the probability of the predicted class.
                    confidence = isPhishing ? pPhish : pLegit;
                }
            }

            return new PredictionResult(isPhishing, confidence, url, now);
        } catch (OrtException e) {
            Log.e(TAG, "Inference failed for url=" + url, e);
            // Safe fallback: treat as non-phishing with 0 confidence.
            return new PredictionResult(false, 0f, url, now);
        } finally {
            if (inputTensor != null) {
                inputTensor.close();
            }
            if (result != null) {
                result.close();
            }
        }
    }

    /** Release the ONNX session. Call from ViewModel.onCleared(). */
    public void close() {
        try {
            if (session != null) {
                session.close();
                session = null;
            }
        } catch (OrtException e) {
            Log.e(TAG, "Error closing session", e);
        }
    }

    private static byte[] readAsset(Context context, String name) throws IOException {
        try (InputStream is = context.getAssets().open(name);
             ByteArrayOutputStream bos = new ByteArrayOutputStream()) {
            byte[] buf = new byte[8192];
            int n;
            while ((n = is.read(buf)) != -1) {
                bos.write(buf, 0, n);
            }
            return bos.toByteArray();
        }
    }
}
