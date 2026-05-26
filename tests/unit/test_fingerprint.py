from architect_job_agent.domain.entities import Job


def test_fingerprint_is_deterministic():
    fp1 = Job.make_fingerprint("Staff Engineer", "Acme", "Berlin", "https://x.com/1")
    fp2 = Job.make_fingerprint("staff engineer", "ACME", " Berlin ", "https://x.com/1")
    assert fp1 == fp2


def test_fingerprint_changes_on_different_url():
    fp1 = Job.make_fingerprint("Engineer", "Acme", "Dublin", "https://x.com/1")
    fp2 = Job.make_fingerprint("Engineer", "Acme", "Dublin", "https://x.com/2")
    assert fp1 != fp2


def test_url_validator_rejects_garbage():
    job = Job(
        fingerprint="x",
        title="t",
        company_name="c",
        source="linkedin",
        url="not-a-url",
    )
    assert job.url is None
