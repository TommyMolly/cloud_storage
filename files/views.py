""" Views для работы с файлами."""

import os
import uuid
import logging
from django.conf import settings
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status

from .models import File

logger = logging.getLogger(__name__)


class FileListView(APIView):
    """Список файлов"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        storage_user_id = request.query_params.get("user_id")
        if storage_user_id and request.user.is_admin:
            files = File.objects.filter(owner_id=storage_user_id)
        else:
            files = File.objects.filter(owner=request.user)
        data = [
            {
                "id": f.id,
                "name": f.name,
                "comment": f.comment,
                "size": f.size,
                "uploaded_at": f.uploaded_at,
                "updated_at": f.updated_at,
                "last_downloaded_at": f.last_downloaded_at,
                "share_token": f.share_token,
            }
            for f in files
        ]
        logger.info("%s requested file list", request.user.username)
        return Response(data)


class FileUploadView(APIView):
    """Загрузка файла"""

    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        uploaded_file = request.FILES.get("file")
        if not uploaded_file:
            return Response({"error": "No file uploaded"}, status=status.HTTP_400_BAD_REQUEST)

        user_folder = os.path.join(settings.MEDIA_ROOT, request.user.storage_path)
        os.makedirs(user_folder, exist_ok=True)
        unique_name = f"{uuid.uuid4().hex}_{uploaded_file.name}"
        file_path = os.path.join(user_folder, unique_name)

        with open(file_path, "wb+") as dest:
            for chunk in uploaded_file.chunks():
                dest.write(chunk)

        comment = request.data.get("comment", "")

        file_obj = File.objects.create(
            owner=request.user,
            file=os.path.join(request.user.storage_path, unique_name),
            name=uploaded_file.name,
            original_name=uploaded_file.name,
            size=uploaded_file.size,
            comment=comment,  
        )

        return Response({
            "id": file_obj.id,
            "name": file_obj.name,
            "comment": file_obj.comment,
            "file": request.build_absolute_uri(file_obj.file.url),
            "size": file_obj.size,
        }, status=status.HTTP_201_CREATED)


class FileDownloadView(APIView):
    """Скачивание файла"""

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        file_obj = get_object_or_404(File, id=pk)
        if file_obj.owner != request.user and not request.user.is_admin:
            return Response({"error": "Permission denied"}, status=403)

        file_obj.last_downloaded_at = timezone.now()
        file_obj.save(update_fields=["last_downloaded_at"])

        file_path = os.path.join(settings.MEDIA_ROOT, file_obj.file.name)
        if not os.path.exists(file_path):
            return Response({"error": "File not found"}, status=404)

        response = FileResponse(open(file_path, "rb"), as_attachment=True, filename=file_obj.original_name)
        logger.info("%s downloaded file %s", request.user.username, file_obj.name)
        return response


class FileRenameView(APIView):
    """Переименование файла"""

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        file_obj = get_object_or_404(File, id=pk)
        if file_obj.owner != request.user and not request.user.is_admin:
            return Response({"error": "Permission denied"}, status=403)

        new_name = request.data.get("name")
        if not new_name:
            return Response({"error": "No new name provided"}, status=400)

        file_obj.name = new_name
        file_obj.save(update_fields=["name"])
        logger.info("%s renamed file %s to %s", request.user.username, file_obj.id, new_name)
        return Response({"id": file_obj.id, "name": file_obj.name})


class FileCommentView(APIView):
    """Добавление или изменение комментария к файлу."""

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        file_obj = get_object_or_404(File, id=pk)
        if file_obj.owner != request.user and not request.user.is_admin:
            return Response({"error": "Permission denied"}, status=403)

        comment = request.data.get("comment", "")
        file_obj.comment = comment
        file_obj.save(update_fields=["comment"])
        logger.info("%s updated comment for file %s", request.user.username, file_obj.id)
        return Response({"id": file_obj.id, "comment": file_obj.comment})


class FileDeleteView(APIView):
    """Удаление файла."""

    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        file_obj = get_object_or_404(File, id=pk)
        if file_obj.owner != request.user and not request.user.is_admin:
            return Response({"error": "Permission denied"}, status=403)

        file_path = os.path.join(settings.MEDIA_ROOT, file_obj.file.name)
        if os.path.exists(file_path):
            os.remove(file_path)
        file_obj.delete()
        logger.info("%s deleted file %s", request.user.username, pk)
        return Response(status=status.HTTP_204_NO_CONTENT)


class FileSharedView(APIView):
    """Создание публичной ссылки для файла."""

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        file_obj = get_object_or_404(File, id=pk)
        if file_obj.owner != request.user and not request.user.is_admin:
            return Response({"error": "Permission denied"}, status=403)

        if not file_obj.share_token:
            file_obj.share_token = uuid.uuid4().hex
            file_obj.save(update_fields=["share_token"])

        share_url = request.build_absolute_uri(f"/api/files/shared/{file_obj.share_token}/")
        logger.info("%s created share link for file %s", request.user.username, pk)
        return Response({"file_id": file_obj.id, "share_url": share_url})


class FileDownloadSharedView(APIView):
    """Скачивание файла по публичной ссылке."""

    def get(self, request, token):
        file_obj = get_object_or_404(File, share_token=token)
        file_path = os.path.join(settings.MEDIA_ROOT, file_obj.file.name)
        if not os.path.exists(file_path):
            return Response({"error": "File not found"}, status=404)

        response = FileResponse(open(file_path, "rb"), as_attachment=True, filename=file_obj.original_name)
        logger.info("Shared file downloaded: %s", file_obj.id)
        return response
