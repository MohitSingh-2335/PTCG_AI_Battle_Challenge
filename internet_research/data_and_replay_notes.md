# Data and Replay Notes

The competition data page provides card metadata and reference materials for the simulator card pool.

What is in the dataset:
- Card ID lists for English and Japanese reference documents.
- English and Japanese card data CSVs.
- Card metadata covering card name, expansion, collection number, stage/type, HP, weakness, resistance, retreat, attacks, cost, damage, and effect text.

Replay notes:
- Episode replays are available from the Submissions page.
- Replays can also be downloaded through Kaggle CLI or MCP tooling.
- Kaggle mentions daily exports of top-rated episodes to help with behavioral cloning, reinforcement learning, and imitation learning.

Useful packaging facts from the competition page:
- Card data is tied to the available simulator card pool.
- The dataset contains public and private test-related materials, but the split is not exposed.

Practical implication:
- Card ID mapping and replay review are the two main tools for diagnosing the agent: one for understanding the move space, the other for understanding why a battle failed or won.
