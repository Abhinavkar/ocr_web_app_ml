from django.db import models

class Document(models.Model):
    pdf = models.FileField(upload_to='pdfs/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

class Image(models.Model):
    image = models.ImageField(upload_to='images/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

class Class(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


class Subject(models.Model):
    name = models.CharField(max_length=255, unique=True)
    associated_class = models.ForeignKey(Class, on_delete=models.CASCADE, related_name="subjects")

    def __str__(self):
        return f"{self.name} ({self.associated_class.name})"
