package com.phishguard.app.data.model;

/** Body for register/send-otp: { name, email }. */
public class RegisterRequest {
    private String name;
    private String email;

    public RegisterRequest(String name, String email) {
        this.name = name;
        this.email = email;
    }

    public String getName() { return name; }
    public void setName(String name) { this.name = name; }

    public String getEmail() { return email; }
    public void setEmail(String email) { this.email = email; }
}
