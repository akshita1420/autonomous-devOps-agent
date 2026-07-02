package com.autonomous.devops_orchestrator.service;

import com.autonomous.devops_orchestrator.model.AnalysisResponse;
import com.autonomous.devops_orchestrator.model.LogRequest;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClient;

@Service
public class AiServiceClient {

    private final RestClient restClient;

    // This automatically pulls your Python URL from application.properties!
    public AiServiceClient(@Value("${ai.service.url}") String aiServiceUrl) {
        this.restClient = RestClient.builder()
                .baseUrl(aiServiceUrl)
                .build();
    }

    public AnalysisResponse sendLogToAi(String logText) {
        try {
            // Wrap the raw string inside our Request model
            LogRequest request = new LogRequest(logText);

            // Make a POST request to Python over the network
            return restClient.post()
                    .contentType(MediaType.APPLICATION_JSON)
                    .body(request)
                    .retrieve()
                    .body(AnalysisResponse.class); // Automatically maps the JSON to Java!
        } catch (Exception e) {
            System.err.println("CRITICAL: Failed to communicate with Python AI Service: " + e.getMessage());
            throw new RuntimeException("AI Diagnostic Service is currently unreachable.", e);
        }
    }
}