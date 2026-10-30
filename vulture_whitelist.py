# Names vulture reports as unused but that a framework reads. Vulture picks
# this file up because `vulture .` scans it alongside the sources.
# ruff: noqa
# fmt: off
_ = object()

# dspy BaseCallback hooks, invoked by dspy with these keyword arguments.
_.on_module_start
_.on_module_end
_.on_lm_start
_.on_lm_end
call_id
exception
# Last-call state kept on the callback for inspection.
_.current_completion
_.current_generation

# dspy.OutputField declarations, filled by the LM.
interests
personality_traits

# Enum members and dataclass fields: part of the profile data model.
ACTIVE
RELAXED
PARTY
INTELLECTUAL
graduation_year
created_at

# Public client API.
_.submit_reply
