package com.phishguard.app.data.remote;

import com.phishguard.app.data.model.AccessTokenResponse;
import com.phishguard.app.data.model.AuthResponse;
import com.phishguard.app.data.model.MessageResponse;
import com.phishguard.app.data.model.OtpRequest;
import com.phishguard.app.data.model.ProfileResponse;
import com.phishguard.app.data.model.RefreshRequest;
import com.phishguard.app.data.model.RegisterRequest;
import com.phishguard.app.data.model.ScanHistory;
import com.phishguard.app.data.model.ScanHistoryPage;
import com.phishguard.app.data.model.ScanRequest;
import com.phishguard.app.data.model.SendOtpRequest;

import okhttp3.ResponseBody;
import retrofit2.Call;
import retrofit2.http.Body;
import retrofit2.http.DELETE;
import retrofit2.http.GET;
import retrofit2.http.POST;
import retrofit2.http.Path;
import retrofit2.http.Query;
import retrofit2.http.Streaming;

/** Retrofit API surface for the PhishGuard backend. */
public interface ApiService {

    // ---- Auth (no password, OTP only) ----
    @POST("auth/register/send-otp")
    Call<MessageResponse> sendRegisterOtp(@Body RegisterRequest body);

    @POST("auth/register/verify-otp")
    Call<AuthResponse> verifyRegisterOtp(@Body OtpRequest body);

    @POST("auth/login/send-otp")
    Call<MessageResponse> sendLoginOtp(@Body SendOtpRequest body);

    @POST("auth/login/verify-otp")
    Call<AuthResponse> verifyLoginOtp(@Body OtpRequest body);

    @POST("auth/refresh")
    Call<AccessTokenResponse> refresh(@Body RefreshRequest body);

    @POST("auth/logout")
    Call<MessageResponse> logout();

    // ---- Scans (require Bearer JWT) ----
    @POST("scans")
    Call<ScanHistory> saveScan(@Body ScanRequest body);

    @GET("scans/history")
    Call<ScanHistoryPage> getHistory(@Query("page") int page, @Query("limit") int limit);

    @DELETE("scans/{id}")
    Call<MessageResponse> deleteScan(@Path("id") long id);

    @Streaming
    @GET("scans/export")
    Call<ResponseBody> exportPdf();

    // ---- User ----
    @GET("users/profile")
    Call<ProfileResponse> getProfile();
}
