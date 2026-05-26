from architect_job_agent.core.config import reload_settings


def test_config_loads_countries_and_roles():
    s = reload_settings()
    assert "Germany" in s.countries
    assert any("Architect" in r or "Engineer" in r for r in s.roles)
    assert s.profile.experience_years >= 0
    assert s.search.minimum_match_score >= 0
