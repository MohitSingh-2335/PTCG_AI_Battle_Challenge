# Simulation Track Summary

The simulation competition is the actual AI battle benchmark. The task is to build an agent that plays Pokemon TCG matches in the cabt simulator and earns rating through repeated episodes against similar agents.

Key points:
- Agents receive an observation each turn and return the indices of legal options to execute.
- The simulator only exposes legal moves.
- New submissions are first validated against themselves to check that they run without errors.
- Submission results are tracked by an estimated skill rating modeled with uncertainty.
- Daily submission limit is 5, and only the latest 2 submissions are kept active for final submissions.
- Final leaderboard results continue to update after the submission deadline until the evaluation window closes.

Submission format:
- A `.tar.gz` bundle.
- `main.py` must be at the top level, not nested.
- `deck.csv` must be included.
- Kaggle notes that files are available in `/kaggle_simulations/agent/` during submission runtime.

Operational constraints from the competition page:
- Submission size limit is 197.7 MiB.
- The environment is resource constrained: 2 vCPUs, 12.2 GiB RAM, 11.8 GiB HDD space.
- Replays are available from the Submissions page and via Kaggle CLI/MCP tooling.

Practical implication:
- The agent must be deterministic enough to survive validation, robust enough to avoid crashes, and effective enough to exploit a narrow but strong deck plan.
