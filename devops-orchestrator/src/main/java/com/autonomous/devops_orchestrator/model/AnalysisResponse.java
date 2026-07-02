package com.autonomous.devops_orchestrator.model;

import lombok.Data;
import java.util.List;

@Data
public class AnalysisResponse {
    private String status;
    private String root_cause;
    private String suggested_fix;
    private List<String> commands_to_execute;
    private double confidence_score;
}