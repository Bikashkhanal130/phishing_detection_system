package com.phishguard.app.ui.scanner;

import android.app.Application;
import android.util.Log;

import androidx.annotation.NonNull;
import androidx.lifecycle.AndroidViewModel;
import androidx.lifecycle.LiveData;
import androidx.lifecycle.MutableLiveData;

import com.phishguard.app.data.model.ScanHistory;
import com.phishguard.app.data.model.ScanRequest;
import com.phishguard.app.data.remote.ApiService;
import com.phishguard.app.data.remote.RetrofitClient;
import com.phishguard.app.ml.FeatureExtractor;
import com.phishguard.app.ml.PhishingDetector;
import com.phishguard.app.ml.PredictionResult;

import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

/**
 * Runs the scan pipeline off the main thread with an ExecutorService:
 *   1. FeatureExtractor extracts 15 features
 *   2. PhishingDetector runs ONNX inference -> PredictionResult
 *   3. Retrofit POST /api/scans saves the result
 *
 * Exposes LiveData for the result, errors, and loading state.
 */
public class ScannerViewModel extends AndroidViewModel {

    private static final String TAG = "ScannerViewModel";

    private final ExecutorService executor = Executors.newSingleThreadExecutor();
    private final ApiService api;
    private PhishingDetector detector;
    private String initError;

    private final MutableLiveData<PredictionResult> result = new MutableLiveData<>();
    private final MutableLiveData<String> error = new MutableLiveData<>();
    private final MutableLiveData<Boolean> loading = new MutableLiveData<>(false);

    public ScannerViewModel(@NonNull Application application) {
        super(application);
        api = RetrofitClient.getApiService(application);
        try {
            detector = new PhishingDetector(application);
        } catch (Throwable t) {
            Log.e(TAG, "Failed to load ONNX model", t);
            initError = "Model not available: " + t.getMessage();
        }
    }

    public LiveData<PredictionResult> getResult() { return result; }
    public LiveData<String> getError() { return error; }
    public LiveData<Boolean> getLoading() { return loading; }

    public void scan(final String url) {
        if (url == null || url.trim().isEmpty()) {
            error.postValue("Please enter a URL");
            return;
        }
        if (detector == null) {
            error.postValue(initError != null ? initError : "Model not loaded");
            return;
        }

        loading.postValue(true);
        executor.execute(() -> {
            try {
                // Steps a + b: features -> ONNX inference.
                PredictionResult prediction = detector.predict(url.trim());
                result.postValue(prediction);
                loading.postValue(false);

                // Step c: persist to backend (best-effort; failure doesn't block UI).
                saveScan(url.trim(), prediction);
            } catch (Throwable t) {
                Log.e(TAG, "Scan failed", t);
                loading.postValue(false);
                error.postValue("Scan failed: " + t.getMessage());
            }
        });
    }

    private void saveScan(String url, PredictionResult prediction) {
        String domain = FeatureExtractor.getDomain(url);
        ScanRequest body = new ScanRequest(
                url,
                prediction.isPhishing(),
                prediction.getConfidence(),
                domain
        );
        api.saveScan(body).enqueue(new Callback<ScanHistory>() {
            @Override
            public void onResponse(Call<ScanHistory> call, Response<ScanHistory> response) {
                if (!response.isSuccessful()) {
                    Log.w(TAG, "saveScan returned " + response.code());
                }
            }

            @Override
            public void onFailure(Call<ScanHistory> call, Throwable t) {
                Log.w(TAG, "saveScan network error: " + t.getMessage());
            }
        });
    }

    @Override
    protected void onCleared() {
        super.onCleared();
        if (detector != null) {
            detector.close();
        }
        executor.shutdown();
    }
}
