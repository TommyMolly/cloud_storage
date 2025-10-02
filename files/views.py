import os
import uuid
import logging
from django.conf import settings
from django.http import FileResponse
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status

from .models import File

logger = logging.getLogger(__name__)

try:
    import magic  # type: ignore
    _MAGIC_AVAILABLE = True
except Exception:
    magic = None  # type: ignore
    _MAGIC_AVAILABLE = False

ALLOWED_EXTENSIONS = {
    "txt", "pdf", "png", "jpg", "jpeg", "gif",
    "csv", "json",
    "doc", "docx", "xls", "xlsx", "ppt", "pptx",
    "zip", "7z", "tar", "gz",
    "mp3", "wav", "mp4", "mov", "avi",
}

ALLOWED_MIMES = {
    # текст/документы
    "text/plain", "application/pdf", "text/csv", "application/json",
    "application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-powerpoint", "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    # изображения
    "image/png", "image/jpeg", "image/gif",
    # архивы
    "application/zip", "application/x-7z-compressed", "application/x-tar", "application/gzip",
    # медиа
    "audio/mpeg", "audio/wav", "video/mp4", "video/quicktime", "video/x-msvideo",
}


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

    def post(self, request):
        """Загрузка файла (REST: POST /files/)"""
        uploaded_file = request.FILES.get("file")
        if not uploaded_file:
            return Response({"error": "No file uploaded"}, status=status.HTTP_400_BAD_REQUEST)

        max_size_mb = 100
        max_size_bytes = max_size_mb * 1024 * 1024
        if hasattr(uploaded_file, "size") and uploaded_file.size > max_size_bytes:
            return Response({"error": f"File too large (>{max_size_mb}MB)"}, status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)

        original_name = os.path.basename(uploaded_file.name or "")
        if not original_name or ".." in original_name or "/" in original_name or "\\" in original_name:
            return Response({"error": "Invalid file name"}, status=status.HTTP_400_BAD_REQUEST)

        name_lower = original_name.lower()
        dangerous_ext = {".exe", ".dll", ".so", ".js", ".jsp", ".php", ".asp", ".aspx", ".cgi", ".sh", ".bat", ".cmd", ".ps1", ".py", ".com", ".msi"}
        _, ext = os.path.splitext(name_lower)
        ext_no_dot = ext.lstrip(".")
        if ext in dangerous_ext or ext_no_dot not in ALLOWED_EXTENSIONS:
            return Response({"error": "This file type is not allowed"}, status=status.HTTP_400_BAD_REQUEST)

        detected_mime = None
        try:
            head = uploaded_file.read(2048)
            try:
                uploaded_file.seek(0)
            except Exception:
                pass
            if _MAGIC_AVAILABLE and head is not None:
                try:
                    detected_mime = magic.from_buffer(head, mime=True)  # type: ignore
                except Exception:
                    detected_mime = None
        except Exception:
            detected_mime = None

        if not detected_mime:
            detected_mime = getattr(uploaded_file, "content_type", None)
        if not detected_mime or detected_mime not in ALLOWED_MIMES:
            return Response({"error": "MIME type is not allowed"}, status=status.HTTP_400_BAD_REQUEST)

        comment = request.data.get("comment", "")
        file_obj = File(owner=request.user, original_name=original_name, name=original_name, comment=comment)
        file_obj.file.save(original_name, uploaded_file, save=False)
        file_obj.size = getattr(uploaded_file, "size", 0)
        file_obj.save()

        return Response(
            {
                "id": file_obj.id,
                "name": file_obj.name,
                "comment": file_obj.comment,
                "file": request.build_absolute_uri(file_obj.file.url),
                "size": file_obj.size,
            },
            status=status.HTTP_201_CREATED,
        )


class FileUploadView(APIView):
    """Загрузка файла"""

    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        uploaded_file = request.FILES.get("file")
        if not uploaded_file:
            return Response({"error": "No file uploaded"}, status=status.HTTP_400_BAD_REQUEST)

        max_size_mb = 100
        max_size_bytes = max_size_mb * 1024 * 1024
        if hasattr(uploaded_file, "size") and uploaded_file.size > max_size_bytes:
            return Response({"error": f"File too large (>{max_size_mb}MB)"}, status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)

        original_name = os.path.basename(uploaded_file.name or "")
        if not original_name or ".." in original_name or "/" in original_name or "\\" in original_name:
            return Response({"error": "Invalid file name"}, status=status.HTTP_400_BAD_REQUEST)

        name_lower = original_name.lower()
        dangerous_ext = {".exe", ".dll", ".so", ".js", ".jsp", ".php", ".asp", ".aspx", ".cgi", ".sh", ".bat", ".cmd", ".ps1", ".py", ".com", ".msi"}
        _, ext = os.path.splitext(name_lower)
        ext_no_dot = ext.lstrip(".")
        if ext in dangerous_ext or ext_no_dot not in ALLOWED_EXTENSIONS:
            return Response({"error": "This file type is not allowed"}, status=status.HTTP_400_BAD_REQUEST)

        detected_mime = None
        try:

            head = uploaded_file.read(2048)
            try:
                uploaded_file.seek(0)
            except Exception:
                pass
            if _MAGIC_AVAILABLE and head is not None:
                try:
                    detected_mime = magic.from_buffer(head, mime=True)  # type: ignore
                except Exception:
                    detected_mime = None
        except Exception:
            detected_mime = None

        if not detected_mime:
            detected_mime = getattr(uploaded_file, "content_type", None)

        if not detected_mime or detected_mime not in ALLOWED_MIMES:
            return Response({"error": "MIME type is not allowed"}, status=status.HTTP_400_BAD_REQUEST)


        comment = request.data.get("comment", "")
        file_obj = File(owner=request.user, original_name=original_name, name=original_name, comment=comment)
        file_obj.file.save(original_name, uploaded_file, save=False)
        file_obj.size = getattr(uploaded_file, "size", 0)
        file_obj.save()

        return Response(
            {
                "id": file_obj.id,
                "name": file_obj.name,
                "comment": file_obj.comment,
                "file": request.build_absolute_uri(file_obj.file.url),
                "size": file_obj.size,
            },
            status=status.HTTP_201_CREATED,
        )


class FileDownloadView(APIView):
    """Скачивание файла"""

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        file_obj = get_object_or_404(File, id=pk)
        if file_obj.owner != request.user and not request.user.is_admin:
            return Response({"error": "Permission denied"}, status=403)

        file_obj.last_downloaded_at = timezone.now()
        file_obj.save(update_fields=["last_downloaded_at"])

        # Безопасный путь через FileField
        file_path = file_obj.file.path
        real_media = os.path.realpath(settings.MEDIA_ROOT)
        real_path = os.path.realpath(file_path)
        if not real_path.startswith(real_media + os.sep):
            return Response({"error": "Invalid file path"}, status=400)
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

        file_path = file_obj.file.path
        real_media = os.path.realpath(settings.MEDIA_ROOT)
        real_path = os.path.realpath(file_path)
        if real_path.startswith(real_media + os.sep) and os.path.exists(file_path):
            os.remove(file_path)
        file_obj.delete()
        logger.info("%s deleted file %s", request.user.username, pk)
        return Response(status=status.HTTP_204_NO_CONTENT)


class FileDetailView(APIView):
    """REST детали файла: PATCH (name/comment), DELETE."""

    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        file_obj = get_object_or_404(File, id=pk)
        if file_obj.owner != request.user and not request.user.is_admin:
            return Response({"error": "Permission denied"}, status=403)
        name = request.data.get("name")
        comment = request.data.get("comment")
        updated = []
        if name is not None and name != "":
            file_obj.name = name
            updated.append("name")
        if comment is not None:
            file_obj.comment = comment
            updated.append("comment")
        if not updated:
            return Response({"error": "No fields to update"}, status=400)
        file_obj.save(update_fields=updated)
        return Response({"id": file_obj.id, "name": file_obj.name, "comment": file_obj.comment}, status=200)

    def delete(self, request, pk):
        return FileDeleteView().delete(request, pk)


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
        file_path = file_obj.file.path
        real_media = os.path.realpath(settings.MEDIA_ROOT)
        real_path = os.path.realpath(file_path)
        if not real_path.startswith(real_media + os.sep):
            return Response({"error": "Invalid file path"}, status=400)
        if not os.path.exists(file_path):
            return Response({"error": "File not found"}, status=404)

        response = FileResponse(open(file_path, "rb"), as_attachment=True, filename=file_obj.original_name)
        logger.info("Shared file downloaded: %s", file_obj.id)
        return response
    

class FileContentView(APIView):
    """Возвращает содержимое файла для предпросмотра."""

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        file_obj = get_object_or_404(File, id=pk)

        if file_obj.owner != request.user and not getattr(request.user, "is_admin", False):
            return HttpResponse("Permission denied", status=403)

        if not os.path.exists(file_obj.file.path):
            return HttpResponse("File not found", status=404)

        _, ext = os.path.splitext(file_obj.name.lower())

        if ext == ".txt":
            with open(file_obj.file.path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            return HttpResponse(content, content_type="text/plain; charset=utf-8")

        mime_map = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".pdf": "application/pdf",
        }
        content_type = mime_map.get(ext, "application/octet-stream")
        return FileResponse(file_obj.file, content_type=content_type, filename=file_obj.name)
    