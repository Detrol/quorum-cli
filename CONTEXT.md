# Quorum — Domain Glossary

**Discussion**: A structured multi-model debate on one question, following one Method, ending in a Synthesis.

**Method**: The phase structure of a Discussion (standard, oxford, advocate, socratic, delphi, brainstorm, tradeoff).

**Agent**: An installed agent CLI that can take part in Discussions on the user's own subscription — `claude`, `codex`, `agy` (Antigravity) or `grok`. Not the same as an API provider.

**Participant**: One Agent + one model + one Effort taking part in a specific Discussion. Written `agent:model@effort`, e.g. `claude:opus@high`. The same model reached through two Agents is two different Participants.

**Effort**: How hard a Participant thinks, on one shared scale — `low`, `medium`, `high`, `xhigh`, `max` — translated to each Agent's own setting and clamped to what the model supports.

**Preset**: A named recipe (`quick`, `balanced`, `deep`) that resolves to one Participant per available Agent by role (fast / workhorse / flagship), never by a fixed model version.

**Run**: One started Discussion with an id, a status and a transcript. The calling agent starts a Run and waits on it in slices.

**Dropped Participant**: A Participant that failed (error or timeout) during a Run. The Run continues while at least two Participants remain.

**Synthesis**: The final summary of a Discussion — consensus, the synthesis text and remaining differences — written by the first Participant.
