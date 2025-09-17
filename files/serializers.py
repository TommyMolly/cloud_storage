from rest_framework import serializers
from .models import File

class FileSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = [
            "id",
            "owner",
            "original_name",
            "file",
            "size",
            "uploaded_at",
            "last_downloaded",
            "comment",
            "share_token",
            "is_shared",
        ]
        read_only_fields = ["id", "owner", "size", "uploaded_at", "last_downloaded", "share_token", "is_shared"]


class FileUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = ["file", "comment"]

    def create(self, validated_data):
        request = self.context.get("request")
        user = request.user if request else None
        return File.objects.create(owner=user, **validated_data)


class FileRenameSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)


class FileCommentSerializer(serializers.Serializer):
    comment = serializers.CharField(max_length=1024)
