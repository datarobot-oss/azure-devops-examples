package com.example.hello;

import java.util.Map;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@SpringBootApplication
@RestController
public class Hello {
  public static void main(String[] args) {
    SpringApplication.run(Hello.class, args);
  }

  @GetMapping("/")
  public Map<String, String> root() {
    return Map.of("message", "Welcome to the Spring Boot application!");
  }

  @GetMapping("/hello")
  public Map<String, String> hello() {
    return Map.of("message", "Hello World!");
  }
}
