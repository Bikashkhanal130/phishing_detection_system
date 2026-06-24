package com.phishguard.app.data.model;

/** Body for login/send-otp: { email }. */
public class SendOtpRequest {
    private String email;

    public SendOtpRequest(String email) { this.email = email; }

    public String getEmail() { return email; }
    public void setEmail(String email) { this.email = email; }
}
