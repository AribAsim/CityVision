---
trigger: always_on
---

# AGENT RULES

1. Read /brain before making changes.

2. Never assume the architecture.
   The BRAIN is the source of truth.

3. Never retrain the existing YOLO model unless explicitly requested.

4. Never replace the existing model with another model without approval.

5. Never introduce a new framework when an existing framework can solve the problem.

6. Do not implement future-scope features during MVP development. 

7. Preserve working existing functionality.

8. Prefer small modular changes.

9. Run tests after meaningful changes.

10. Update IMPLEMENTATION_STATUS.md after completing a task.

11. If implementation differs from the architecture,
    update the relevant BRAIN document.

12. Do not silently change API contracts.

13. Do not hardcode data that should come from the backend.

14. Do not create duplicate implementations of the same functionality.

15. Optimize for a reliable hackathon demo over theoretical production scalability.

16. When uncertain, inspect the repository before guessing.