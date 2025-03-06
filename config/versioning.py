from rest_framework import versioning


class CustomURLPathVersioning(versioning.URLPathVersioning):
    default_version = 'v1'
    allowed_versions = ['v1']
