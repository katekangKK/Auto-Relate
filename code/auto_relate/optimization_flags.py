import os


def _env_enabled(name: str) -> bool:
    value = os.environ.get(name, "")
    return value.strip().lower() in {"1", "true", "yes", "on"}


def disable_groupby_bound() -> bool:
    return _env_enabled("AUTO_RELATE_DISABLE_GROUPBY_BOUND")


def disable_closed_form() -> bool:
    return _env_enabled("AUTO_RELATE_DISABLE_CLOSED_FORM")


def disable_binomial_bound() -> bool:
    return _env_enabled("AUTO_RELATE_DISABLE_BINOMIAL_BOUND")
