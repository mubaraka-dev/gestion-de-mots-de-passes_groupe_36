from django.conf import settings
from django.db import models


class PasswordEntry(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="password_entries",
    )
    service_name = models.CharField(max_length=150)
    username = models.CharField(max_length=150)
    encrypted_password = models.TextField()
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["service_name", "-updated_at"]
        verbose_name = "Entree de mot de passe"
        verbose_name_plural = "Entrees de mots de passe"

    def __str__(self):
        return f"{self.service_name} - {self.username}"
