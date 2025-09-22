"""Serializers for File model and related operations."""
from rest_framework import serializers
from .models import File

class FileSerializer(serializers.ModelSerializer):
    """Serializer для полной информации о файле."""

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
        read_only_fields = [
            "id",
            "owner",
            "size", 
            "uploaded_at", 
            "last_downloaded", 
            "share_token", 
            "is_shared",
            ]


class FileUploadSerializer(serializers.ModelSerializer):
    """Serializer для загрузки файла с комментарием."""

    class Meta:
        model = File
        fields = ["file", "comment"]

    def create(self, validated_data):
        """Привязка загружаемого файла к текущему пользователю."""
        request = self.context.get("request")
        user = request.user if request else None
        return File.objects.create(owner=user, **validated_data)


class FileRenameSerializer(serializers.Serializer):
    """Serializer для переименования файла."""

    name = serializers.CharField(max_length=255)

    def create(self, validated_data):
        """Нереализовано, так как не создаём новые объекты здесь."""
        return validated_data

    def update(self, instance, validated_data):
        """Обновление имени файла."""
        instance.name = validated_data.get("name", instance.name)
        instance.save(update_fields=["name"])
        return instance


class FileCommentSerializer(serializers.Serializer):
    """Serializer для изменения комментария к файлу."""

    comment = serializers.CharField(max_length=1024)

    def create(self, validated_data):
        """Нереализовано, так как не создаём новые объекты здесь."""
        return validated_data

    def update(self, instance, validated_data):
        """Обновление комментария."""
        instance.comment = validated_data.get("comment", instance.comment)
        instance.save(update_fields=["comment"])
        return instance