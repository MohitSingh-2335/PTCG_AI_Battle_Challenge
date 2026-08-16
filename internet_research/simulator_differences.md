# Known Simulator Differences

The official discussion thread documents a few ways the simulator differs from the paper TCG rules. These matter because the simulator behavior is the truth for competition play.

Known differences:
- Some attacks that would be legal to declare in the real game may be unselectable in the simulator if their effects cannot resolve meaningfully in the current state.
- Mega Zygarde ex's Nullifying Zero resolves target order automatically from left to right instead of letting the player choose the order.
- Simultaneous Knock Out prize ordering is handled differently than in the official TCG.

Behavior that was clarified in the thread:
- The simulator only exposes legal actions in the option list.
- Continuous effects are applied automatically and do not need to be re-activated each turn.
- During setup bench selection, the absence of an explicit end-turn option does not automatically mean the agent must bench every basic Pokemon; `minCount` controls whether selection is optional.
- Retreating and re-promoting a Pokemon can reset certain attack restrictions if the simulator treats the Pokemon as leaving and re-entering play.
- The thread includes a clarifying ruling that Mega Lopunny ex's Gale Thrust checks whether Mega Lopunny ex itself moved from Bench to Active, not whether the pre-evolution Buneary moved.

Practical implication:
- If the agent uses a combo or exploit, the replay thread is the best place to check whether the simulator really supports it the way the deck plan expects.
