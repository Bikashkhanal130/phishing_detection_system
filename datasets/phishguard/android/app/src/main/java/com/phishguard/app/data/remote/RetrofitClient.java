package com.phishguard.app.data.remote;

import android.content.Context;

import com.phishguard.app.data.local.TokenManager;

import java.util.concurrent.TimeUnit;

import okhttp3.OkHttpClient;
import okhttp3.logging.HttpLoggingInterceptor;
import retrofit2.Retrofit;
import retrofit2.converter.gson.GsonConverterFactory;

/**
 * Singleton Retrofit/OkHttp provider with the AuthInterceptor wired in.
 *
 * BASE_URL:
 *   - Emulator -> http://10.0.2.2:8000/api/   (10.0.2.2 = host machine)
 *   - Real device -> replace with your server's LAN IP, e.g. http://192.168.x.x:8000/api/
 */
public class RetrofitClient {

    // NOTE: trailing slash is required so the relative @POST paths resolve.
    public static final String BASE_URL = "http://10.0.2.2:8000/api/";

    private static volatile ApiService apiService;

    private RetrofitClient() {}

    public static ApiService getApiService(Context context) {
        if (apiService == null) {
            synchronized (RetrofitClient.class) {
                if (apiService == null) {
                    apiService = build(context.getApplicationContext());
                }
            }
        }
        return apiService;
    }

    private static ApiService build(Context appContext) {
        TokenManager tokenManager = TokenManager.getInstance(appContext);

        HttpLoggingInterceptor logging = new HttpLoggingInterceptor();
        logging.setLevel(HttpLoggingInterceptor.Level.BODY);

        OkHttpClient client = new OkHttpClient.Builder()
                // AuthInterceptor first so it adds the header; logging observes the final request.
                .addInterceptor(new AuthInterceptor(tokenManager, BASE_URL))
                .addInterceptor(logging)
                .connectTimeout(30, TimeUnit.SECONDS)
                .readTimeout(30, TimeUnit.SECONDS)
                .writeTimeout(30, TimeUnit.SECONDS)
                .build();

        Retrofit retrofit = new Retrofit.Builder()
                .baseUrl(BASE_URL)
                .client(client)
                .addConverterFactory(GsonConverterFactory.create())
                .build();

        return retrofit.create(ApiService.class);
    }
}
