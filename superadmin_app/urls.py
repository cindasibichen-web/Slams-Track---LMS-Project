from django.urls import path
from .views import *
urlpatterns = [
   

   path('login/', LoginAPIView.as_view()),
   path('list-categories/', ListCategoryAPIView.as_view()),
   path('forgot-password/', ForgotPasswordAPIView.as_view()),
   path('verify-otp/', VerifyOTPAPIView.as_view()),
   path( "forgot-password/resend-otp/",ResendForgotPasswordOTPAPIView.as_view()),
   path('reset-password/', ResetPasswordAPIView.as_view()),
   path('token-refresh/', TokenRefreshAPIView.as_view()),
   path('logout/', LogoutAPIView.as_view()),
   
   # path('check-login/', CheckLoginStateAPIView.as_view()),

   # path('assign-category/', AssignCategoryAPIView.as_view()),
  
   
]