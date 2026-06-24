package com.phishguard.app.data.model;

/** User payload returned by the backend. */
public class UserDto {
    private Long id;
    private String name;
    private String email;

    public UserDto() {}

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public String getName() { return name; }
    public void setName(String name) { this.name = name; }

    public String getEmail() { return email; }
    public void setEmail(String email) { this.email = email; }
}
