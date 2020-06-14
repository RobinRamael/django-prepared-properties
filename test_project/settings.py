DEBUG = True
SECRET_KEY = "4l0ngs3cr3tstr1ngw3lln0ts0l0ngw41tn0w1tsl0ng3n0ugh"
ROOT_URLCONF = __name__

urlpatterns = []

# rock_n_roll/apps.py

from django.apps import AppConfig


class TestAppConfig(AppConfig):
    name = "test_project"


DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:",}}

INSTALLED_APPS = ["test_project.settings.TestAppConfig"]
