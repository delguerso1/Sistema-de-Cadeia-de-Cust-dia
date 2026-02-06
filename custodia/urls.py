from django.urls import path
from . import views

app_name = 'custodia'

urlpatterns = [
    path('', views.index, name='index'),
    path('processar/', views.processar_custodia, name='processar'),
    path('resultado/<int:custodia_id>/', views.resultado, name='resultado'),
    path('pdf/<int:custodia_id>/', views.download_pdf, name='download_pdf'),
    path('lista/', views.lista_custodias, name='lista'),
    path('detalhes/<int:custodia_id>/', views.detalhes_custodia, name='detalhes'),
]
