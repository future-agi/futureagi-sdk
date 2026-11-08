"""Clear error for the former agent-learning-kit namespace; no behavior shim."""

from fi._alk_moved import namespace_moved

raise namespace_moved("fi.simulate", "fi.alk.simulate")
