"""Shared specs for the OpenAI-compatible Chinese model providers.

One table drives the provider tests in test_config.py, test_providers.py,
test_model_factory.py and test_api_providers.py so the eight providers are
covered by the same set of assertions.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProviderSpec:
    """One OpenAI-compatible provider: its key, env vars and defaults.

    The provider key is the name used by `quorum.providers` and by the
    `provider:model` participant syntax. The env prefix is the uppercase
    name used for the `*_API_KEY` / `*_BASE_URL` / `*_MODELS` variables -
    Volcengine Ark uses ARK_* while its provider key stays "volcengine".

    `sample_models` are real model ids from the same provider, used as
    fixtures for the routing and catalog tests. Routing only looks a model
    up in the configured *_MODELS list, so any id works; using real ones
    keeps the fixture from teaching a stale model name.
    """

    key: str
    env_prefix: str
    default_base_url: str
    sample_models: tuple[str, ...]

    @property
    def sample_model(self) -> str:
        """The model id used as the single-model fixture."""
        return self.sample_models[0]

    @property
    def api_key_env(self) -> str:
        """Env var holding the provider API key."""
        return f"{self.env_prefix}_API_KEY"

    @property
    def base_url_env(self) -> str:
        """Env var overriding the provider base URL."""
        return f"{self.env_prefix}_BASE_URL"

    @property
    def models_env(self) -> str:
        """Env var listing the provider models."""
        return f"{self.env_prefix}_MODELS"

    @property
    def api_key_attr(self) -> str:
        """Settings attribute holding the provider API key."""
        return f"{self.key}_api_key"

    @property
    def base_url_attr(self) -> str:
        """Settings attribute holding the provider base URL."""
        return f"{self.key}_base_url"

    @property
    def models_attr(self) -> str:
        """Settings attribute holding the provider model list."""
        return f"{self.key}_models"

    @property
    def has_attr(self) -> str:
        """Settings property telling whether the provider is configured."""
        return f"has_{self.key}"


CN_PROVIDERS = (
    ProviderSpec(
        key="minimax",
        env_prefix="MINIMAX",
        default_base_url="https://api.minimaxi.com/v1",
        sample_models=("MiniMax-M3.1-Flash", "MiniMax-M3"),
    ),
    ProviderSpec(
        key="zhipu",
        env_prefix="ZHIPU",
        default_base_url="https://open.bigmodel.cn/api/paas/v4",
        sample_models=("glm-5.3", "glm-5.3-flash"),
    ),
    ProviderSpec(
        key="moonshot",
        env_prefix="MOONSHOT",
        default_base_url="https://api.moonshot.cn/v1",
        sample_models=("kimi-k3.1-pro", "kimi-k3"),
    ),
    ProviderSpec(
        key="stepfun",
        env_prefix="STEPFUN",
        default_base_url="https://api.stepfun.com/v1",
        sample_models=("step-5-preview", "step-3.7-flash"),
    ),
    ProviderSpec(
        key="volcengine",
        env_prefix="ARK",
        default_base_url="https://ark.cn-beijing.volces.com/api/v3",
        sample_models=("doubao-seed-2-1-pro-260915", "doubao-seed-2-1-lite-260915"),
    ),
    ProviderSpec(
        key="qianfan",
        env_prefix="QIANFAN",
        default_base_url="https://qianfan.baidubce.com/v2",
        sample_models=("ernie-5.1", "ernie-4.5-turbo-128k"),
    ),
    ProviderSpec(
        key="tokenhub",
        env_prefix="TOKENHUB",
        default_base_url="https://tokenhub.tencentcloudmaas.com/v1",
        # Hunyuan is served through this slot; the legacy api.hunyuan endpoint
        # retires on 2026-09-30, so there is no separate Hunyuan provider.
        sample_models=("hy4-preview", "hy3"),
    ),
    ProviderSpec(
        key="baichuan",
        env_prefix="BAICHUAN",
        default_base_url="https://api.baichuan-ai.com/v1",
        sample_models=("Baichuan4-Turbo", "Baichuan4-Air"),
    ),
)

# Every provider env var that must be cleared before a test, so a developer's
# own .env cannot leak into a test run.
PROVIDER_ENV_VARS = (
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "GOOGLE_API_KEY",
    "XAI_API_KEY",
    "OPENAI_MODELS",
    "ANTHROPIC_MODELS",
    "GOOGLE_MODELS",
    "XAI_MODELS",
    "OLLAMA_API_KEY",
    "OLLAMA_BASE_URL",
    "DEEPSEEK_API_KEY",
    "DEEPSEEK_BASE_URL",
    "DEEPSEEK_MODELS",
    "ALIYUN_API_KEY",
    "ALIYUN_BASE_URL",
    "ALIYUN_MODELS",
    "OPENROUTER_API_KEY",
    "OPENROUTER_BASE_URL",
    "OPENROUTER_MODELS",
    "LMSTUDIO_API_KEY",
    "LMSTUDIO_BASE_URL",
    "LMSTUDIO_MODELS",
    "LLAMASWAP_API_KEY",
    "LLAMASWAP_BASE_URL",
    "LLAMASWAP_MODELS",
    "CUSTOM_API_KEY",
    "CUSTOM_BASE_URL",
    "CUSTOM_MODELS",
    *(
        var
        for spec in CN_PROVIDERS
        for var in (spec.api_key_env, spec.base_url_env, spec.models_env)
    ),
)

# Quorum's own settings - unrelated to providers, but still environment driven.
QUORUM_ENV_VARS = (
    "QUORUM_METHOD",
    "QUORUM_SYNTHESIZER",
    "QUORUM_ROUNDS_PER_AGENT",
    "QUORUM_DEFAULT_LANGUAGE",
)


def env_example_vars() -> dict[str, str]:
    """Read the commented variable examples from the repo's .env.example.

    The example file is the user-facing configuration reference; the values
    there must match what the code defaults to, or the docs would send users
    to the wrong endpoint. Keys are lowercased variable names.
    """
    import re
    from pathlib import Path

    path = Path(__file__).resolve().parent.parent / ".env.example"
    out: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^#\s*([A-Z][A-Z0-9_]*)=(.*)$", line.strip())
        if not m:
            continue
        value = m.group(2)
        # Some lines carry a trailing comment: "# VAR=value    # note"
        value = value.split("  #")[0].strip()
        out[m.group(1).lower()] = value
    return out


def env_example_models() -> dict[str, str]:
    """The *_MODELS entries of .env.example, keyed by variable prefix."""
    return {k[: -len("_models")]: v for k, v in env_example_vars().items() if k.endswith("_models")}


# DeepSeek and Aliyun joined the same pattern earlier; they are listed here so
# the .env.example and README comparisons cover every compatible provider.
COMPAT_PROVIDERS = (
    ProviderSpec(
        key="deepseek",
        env_prefix="DEEPSEEK",
        default_base_url="https://api.deepseek.com/v1",
        sample_models=("deepseek-chat", "deepseek-reasoner"),
    ),
    ProviderSpec(
        key="aliyun",
        env_prefix="ALIYUN",
        default_base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        sample_models=("qwen3.8-max", "qwen3.8-flash"),
    ),
)

ALL_COMPAT_PROVIDERS = COMPAT_PROVIDERS + CN_PROVIDERS


def readme_base_urls() -> dict[str, str]:
    """The *_BASE_URL examples from README.md, values only.

    The README is prose and its formatting changes often, so only the URL
    itself is compared - a trailing comment or a reindented code block must
    not fail the test, but a wrong endpoint must.
    """
    import re
    from pathlib import Path

    path = Path(__file__).resolve().parent.parent / "README.md"
    out: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\s*#\s*([A-Z][A-Z0-9_]*)_BASE_URL=(\S+)", line)
        if m:
            out[f"{m.group(1).lower()}_base_url"] = m.group(2)
    return out
