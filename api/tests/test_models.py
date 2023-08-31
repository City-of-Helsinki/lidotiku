import pytest
from api.models import Counter  # pylint: disable=import-error


@pytest.mark.django_db
def test_readonly_models():
    with pytest.raises(NotImplementedError):
        Counter.objects.create(id=1, name="Test")
    with pytest.raises(NotImplementedError):
        counter = Counter()
        counter.create(id=1, name="Test")
    counter = Counter(id=1, name="Test")
    with pytest.raises(NotImplementedError):
        counter.save()
    with pytest.raises(NotImplementedError):
        counter = Counter(id=1, name="Test")
        counter.update()
    with pytest.raises(NotImplementedError):
        counter.delete()
