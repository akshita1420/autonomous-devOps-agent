package com.autonomous.devops_orchestrator.service;

import org.springframework.stereotype.Service;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.util.List;

@Service
public class CommandExecutionService {

    public void executeMitigationCommands(List<String> commands) {
        if (commands == null || commands.isEmpty()) {
            System.out.println("[Execution Engine] No automated mitigation commands provided by AI.");
            return;
        }

        System.out.println("[Execution Engine] WARNING: AI requested execution of " + commands.size() + " command(s).");

        for (String command : commands) {
            System.out.println("[Execution Engine] Running command: " + command);
            try {
                ProcessBuilder processBuilder = new ProcessBuilder();

                // Determine OS to use the correct shell launcher
                if (System.getProperty("os.name").toLowerCase().contains("win")) {
                    processBuilder.command("powershell.exe", "-Command", command);
                } else {
                    processBuilder.command("bash", "-c", command);
                }

                Process process = processBuilder.start();

                // Stream the output to the Java console in real-time
                try (BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()))) {
                    String line;
                    while ((line = reader.readLine()) != null) {
                        System.out.println("  > " + line);
                    }
                }

                int exitCode = process.waitFor();
                if (exitCode == 0) {
                    System.out.println("[Execution Engine] Command executed successfully (Exit Code: 0).");
                } else {
                    System.err.println("[Execution Engine] Command failed with exit code: " + exitCode);
                }

            } catch (Exception e) {
                System.err.println("[Execution Engine] Critical failure executing command: " + e.getMessage());
            }
        }
    }
}