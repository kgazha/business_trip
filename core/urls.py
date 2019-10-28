from django.urls import path
from core import views
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.contrib.auth.decorators import login_required, permission_required
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('', views.BusinessTripView.as_view(), name='index'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('business_trips/', login_required(views.BusinessTripManagementView.as_view(), login_url='/login/'),
         name='business_trip_management'),
    path('business_trips/purchasing_department/<int:pk>/', views.PurchasingDepartmentView.as_view(),
         name='purchasing_department'),
    path('business_trips/head_of_department/<int:pk>/',
         permission_required('core.HEAD_OF_DEPARTMENT',
                             login_url='/login/',
                             raise_exception=True)(views.HeadOfDepartmentView.as_view()),
         name='head_of_department'),
    path('business_trips/deputy_governor/<int:pk>/',
         permission_required('core.DEPUTY_GOVERNOR',
                             login_url='/login/',
                             raise_exception=True)(views.DeputyGovernorView.as_view()),
         name='deputy_governor'),
    path('business_trips/personnel_department/<int:pk>/',
         permission_required('core.PERSONNEL_DEPARTMENT',
                             login_url='/login/',
                             raise_exception=True)(views.PersonnelDepartmentView.as_view()),
         name='personnel_department'),
    path('business_trips/bookkeeping/<int:pk>/',
         permission_required('core.BOOKKEEPING',
                             login_url='/login/',
                             raise_exception=True)(views.BookkeepingView.as_view()),
         name='bookkeeping'),
    path('business_trips/<int:pk>/', views.BusinessTripDetailedView.as_view(), name='business_trip_detailed'),
    path('download/<int:pk>/<str:document_type>/', views.download_link),
]

urlpatterns += staticfiles_urlpatterns()
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
