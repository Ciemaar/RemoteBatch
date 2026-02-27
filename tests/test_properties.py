from hypothesis import given
from hypothesis import strategies as st

from model import Job


@given(st.text(), st.text(), st.integers())
def test_job_attributes(id_val, type_val, size_val):
    job = Job()
    job.id = id_val
    job.type = type_val
    job.size = size_val

    assert job.id == id_val
    assert job.type == type_val
    assert job.size == size_val


def test_job_str():
    job = Job()
    job.id = "123"
    job.path = "/tmp/path"
    job.jobfile = "file.txt"
    s = str(job)
    assert "id: 123" in s
    assert "path:\n/tmp/path" in s
    assert "\nfile.txt" in s
