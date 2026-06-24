package com.example.phishingdetector.api;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;

import java.util.concurrent.TimeUnit;

import okhttp3.OkHttpClient;
import okhttp3.logging.HttpLoggingInterceptor;
import retrofit2.Retrofit;
import retrofit2.converter.gson.GsonConverterFactory;

/**
 * Single shared Retrofit instance.
 *
 * IMPORTANT — set BASE_URL to where your Flask server runs:
 *   - Android emulator  -> http://10.0.2.2:5000/   (10.0.2.2 = your PC's localhost)
 *   - Real phone on same Wi-Fi -> http://YOUR_PC_IP:5000/   (e.g. 192.168.1.20)
 * The trailing slash is required.
 */
public class ApiClient {

    public static final String BASE_URL = "https://unrepulsed-diedre-nonfrenetic.ngrok-free.dev/";
    //public static final String BASE_URL = "http://192.168.1.22:5000/";
    //public static final String BASE_URL = "http://10.0.2.2:5000/";

    private static Retrofit retrofit;

    public static ApiService get() {
        if (retrofit == null) {
            HttpLoggingInterceptor logging = new HttpLoggingInterceptor();
            logging.setLevel(HttpLoggingInterceptor.Level.BODY);

            OkHttpClient client = new OkHttpClient.Builder()
                    .addInterceptor(logging)
                    .connectTimeout(30, TimeUnit.SECONDS)
                    .readTimeout(30, TimeUnit.SECONDS)
                    .build();

            Gson gson = new GsonBuilder().setLenient().create();

            retrofit = new Retrofit.Builder()
                    .baseUrl(BASE_URL)
                    .client(client)
                    .addConverterFactory(GsonConverterFactory.create(gson))
                    .build();
        }
        return retrofit.create(ApiService.class);
    }
}
