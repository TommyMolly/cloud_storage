from django.urls import path
from .views import RegisterView, LoginView, UserDeleteView, UserListView, ToggleAdminView, UserDetailView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("users/", UserListView.as_view(), name="user_list"),
    path("<int:user_id>/delete/", UserDeleteView.as_view(), name="user_delete"),
    path('<int:user_id>/update_admin/', ToggleAdminView.as_view(), name='update_admin'),
    path('users/<int:user_id>/', UserDetailView.as_view(), name='user_detail'),
]
