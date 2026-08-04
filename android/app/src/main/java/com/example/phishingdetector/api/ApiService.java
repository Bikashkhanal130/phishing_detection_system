package com.example.phishingdetector.api;

import okhttp3.MultipartBody;
import okhttp3.ResponseBody;
import retrofit2.Call;
import retrofit2.http.Body;
import retrofit2.http.GET;
import retrofit2.http.Header;
import retrofit2.http.Multipart;
import retrofit2.http.POST;
import retrofit2.http.PUT;
import retrofit2.http.Part;
import retrofit2.http.Streaming;

/** Maps each Flask endpoint to a Java method. */
public interface ApiService {

    @POST("api/register")
    Call<Models.MessageResponse> register(@Body Models.RegisterRequest body);

    @POST("api/verify-otp")
    Call<Models.AuthResponse> verifyOtp(@Body Models.VerifyRequest body);

    @POST("api/resend-otp")
    Call<Models.MessageResponse> resendOtp(@Body Models.EmailRequest body);

    @POST("api/login")
    Call<Models.AuthResponse> login(@Body Models.LoginRequest body);

    @POST("api/forgot-password")
    Call<Models.MessageResponse> forgotPassword(@Body Models.EmailRequest body);

    @POST("api/reset-password")
    Call<Models.MessageResponse> resetPassword(@Body Models.ResetPasswordRequest body);

    @GET("api/profile")
    Call<Models.MessageResponse> getProfile(@Header("Authorization") String bearer);

    @PUT("api/profile")
    Call<Models.MessageResponse> updateProfile(@Header("Authorization") String bearer,
                                               @Body Models.ProfileUpdate body);

    @Multipart
    @POST("api/profile/image")
    Call<Models.MessageResponse> uploadImage(@Header("Authorization") String bearer,
                                             @Part MultipartBody.Part image);

    @POST("api/predict")
    Call<Models.PredictResponse> predict(@Header("Authorization") String bearer,
                                         @Body Models.PredictRequest body);

    @GET("api/history")
    Call<Models.HistoryResponse> history(@Header("Authorization") String bearer);

    @Streaming
    @GET("api/history/pdf")
    Call<ResponseBody> historyPdf(@Header("Authorization") String bearer);
}
