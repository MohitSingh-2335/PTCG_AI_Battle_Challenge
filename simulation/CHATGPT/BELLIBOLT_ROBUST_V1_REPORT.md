# PTCG AI Battle — Bellibolt Robust V1

## Decision
The current Mega Lopunny family was not selected as the next submission. A new Iono's Bellibolt ex / Kilowattrel agent was built from the project evidence and competition-replay analysis.

## Primary package
`submission_bellibolt_robust_v1.tar.gz`

Deck: 22 Basic Lightning Energy; 3 each of Voltorb, Tadbulb, Bellibolt ex, Wattrel, Kilowattrel; 4 Lillie's Determination; 4 Canari; 3 Buddy-Buddy Poffin; 3 Ultra Ball; 3 Levincia; 2 Night Stretcher; 2 Poke Pad; Max Rod; Energy Retrieval.

## Secondary package
`submission_bellibolt_mist_v1.tar.gz`

Same policy, but 20 Basic Lightning Energy + 2 Mist Energy.

## Why this architecture
- Bellibolt ex provides the 230-damage primary attack.
- Kilowattrel is a non-ex attacker and avoids the Crustle ex-immunity wall.
- Voltorb provides another non-ex route and scales with Lightning Energy on the board.
- The policy explicitly models Crustle immunity, Fighting-type threats, attack damage, KO value, energy readiness, bench development, deck-out risk, and deterministic legal fallback.
- No random fallback is used.

## Local evidence
Using the 36 actual opponent decklists recovered from the 519-Elo replay archive:
- Primary/no-Mist build: 5-game broad replay-corpus run = 176 wins / 2 losses / 2 draws (97.8% win rate).
- Primary/no-Mist build: 20-game selected-match runs included 100% vs several major archetypes, 95% vs multiple Lucario/Archaludon/Dragapult variants, 90% vs the recorded Crustle deck, and 65% vs the recorded Iono Bellibolt mirror.
- 100-game head-to-head vs the repository's V13 Lopunny agent: 87-13.
- 100-game head-to-head vs the submitted/current Lopunny agent: 89-11.
- 100-game head-to-head vs the repository's intermediate Mega Lucario agent: 57-42-1.
- 30 self-games from the packaged primary agent: 30/30 completed with zero exceptions.

## Important interpretation
These are local simulations against reconstructed historical opponent decklists. They are not a guarantee of Kaggle Elo. The competition's official evaluation is a live Elo-style ladder against other submissions, and only the latest two submissions are active.

## Submission order
If two submission slots are available, submit the primary 22-Lightning build first and the 2-Mist build second. The primary was selected because its larger energy density materially improved the recorded Bellibolt mirror while retaining very strong results against the rest of the replay corpus.
