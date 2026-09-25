# Quorum — Domain Glossary

**Discussion**: A structured multi-model debate on one question, following one Method, ending in a Synthesis.

**Method**: The phase structure of a Discussion (standard, oxford, advocate, socratic, delphi, brainstorm, tradeoff).

**Provider**: Where a Participant's model runs: an Agent, an API provider, or a local provider.

**API provider**: A hosted model API configured with a key and a `*_MODELS` list in `~/.quorum/.env` — openai, anthropic, google, xai, openrouter, custom. Its Participants have no tools: they see only the question and files.

**Local provider**: A model server on the user's own machine or network — ollama (models auto-discovered), lmstudio, llamaswap. No tools, like API providers.

**Agent**: An installed agent CLI that can take part in Discussions on the user's own subscription — `claude`, `codex`, `agy` (Antigravity) or `grok`. Not the same as an API provider.

**Participant**: One Provider + one model + one Effort taking part in a specific Discussion. Written `provider:model@effort`, e.g. `claude:opus@high`, `openai:gpt-5.5@medium`, `ollama:qwen3:8b`. The same model reached through two Providers is two different Participants.

**Effort**: How hard a Participant thinks, on one shared scale — `low`, `medium`, `high`, `xhigh`, `max` — translated to each Agent's own setting and clamped to what the model supports.

**Preset**: A named recipe (`quick`, `balanced`, `deep`) that resolves to one Participant per available Agent by role (fast / workhorse / flagship), never by a fixed model version. API and local providers join a Preset only when chosen explicitly.

**Level**: The user's pick of `quick`, `balanced` or `deep` when choosing Participants; it preselects each Provider's model and Effort from the matching Preset.

**Run**: One started Discussion with an id, a status and a transcript. The calling agent starts a Run and waits on it in slices.

**Dropped Participant**: A Participant that failed (error or timeout) during a Run. The Run continues while at least two Participants remain.

**Synthesis**: The final summary of a Discussion — consensus, the synthesis text and remaining differences — written by the Participant `QUORUM_SYNTHESIZER` selects (the first by default).
