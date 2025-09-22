from django.urls import path
from .views import (
    FileListView,
    FileUploadView,
    FileDownloadView,
    FileRenameView,
    FileCommentView,
    FileDeleteView,
    FileSharedView,
    FileDownloadSharedView,
)

urlpatterns = [
    path("", FileListView.as_view(), name="file_list"),
    path("upload/", FileUploadView.as_view(), name="file_upload"),
    path("<int:pk>/download/", FileDownloadView.as_view(), name="file_download"),
    path("<int:pk>/rename/", FileRenameView.as_view(), name="file_rename"),
    path("<int:pk>/comment/", FileCommentView.as_view(), name="file_comment"),
    path("<int:pk>/", FileDeleteView.as_view(), name="file_delete"),
    path("shared/<int:pk>/", FileSharedView.as_view(), name="file_shared"),
    path("shared/<str:token>/", FileDownloadSharedView.as_view(), name="file_shared_download"),
]
