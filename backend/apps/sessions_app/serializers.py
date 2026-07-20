"""
Sessions App – Serializers
"""
from rest_framework import serializers
from .models import Session


class SessionSerializer(serializers.ModelSerializer):
    duration_seconds = serializers.ReadOnlyField()

    class Meta:
        model = Session
        fields = '__all__'
