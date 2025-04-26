from rest_framework import serializers
from .models import Interviewer, InterviewTemplate

class InterviewerSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    class Meta:
        model = Interviewer
        fields = ["id", "name"]
        
    def get_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"

class InterviewTemplateSerializer(serializers.ModelSerializer):
    interviewers = InterviewerSerializer(many=True, read_only=True)
    
    class Meta:
        model = InterviewTemplate
        fields = ["id", "name", "duration", "interviewers"]

class AvailableSlotSerializer(serializers.Serializer):
    start = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%SZ")
    end = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%SZ")

class InterviewAvailabilitySerializer(serializers.ModelSerializer):
    interviewId = serializers.IntegerField(source="id")
    name = serializers.CharField()
    durationMinutes = serializers.IntegerField(source="duration")
    interviewers = InterviewerSerializer(many=True, read_only=True)
    availableSlots = serializers.SerializerMethodField()
    
    class Meta:
        model = InterviewTemplate
        fields = ["interviewId", "name", "durationMinutes", "interviewers", "availableSlots"]

    def get_availableSlots(self, obj):
        return self.context.get("available_slots", [])