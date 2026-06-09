from rest_framework import serializers
from superadmin_app.models import *




class LoginSerializer(serializers.Serializer):
    user_id = serializers.CharField()
    password = serializers.CharField()
    category_id = serializers.IntegerField(required=False, allow_null=True)