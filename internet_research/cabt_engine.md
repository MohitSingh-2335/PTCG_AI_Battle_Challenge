# cabt Engine Summary

The cabt engine is the simulator used for the competition. It provides the game state and legal action choices to the agent each turn.

Observation model:
- `logs`: past action and event logs.
- `current`: the current board state, including players, stadium, and turn progression.
- `select`: the current decision point, including the legal options the agent may choose from.

Important state fields:
- Player state includes active Pokemon, bench, hand, prize cards, deck count, discard pile, bench size limits, and special condition flags.
- The active Pokemon can be empty or face-down in some cases.

API overview:
- `all_card_data()` returns metadata for every available card.
- `all_attack()` returns attack metadata.
- `battle_start(deck0, deck1)` starts a battle with two 60-card decks.
- `battle_select(select_list)` advances the battle using the chosen option indices.
- `battle_finish()` ends the current battle.
- `visualize_data()` gives a human-readable board snapshot for debugging.

Getting-started example from the docs:
- Define `agent(obs_dict)` to return a list of selected option indices.
- Keep deck construction in `deck.csv` with exactly 60 lines.

Practical implication:
- The agent should be written around the simulator's exact observation schema and never assume illegal moves will be filtered later.
