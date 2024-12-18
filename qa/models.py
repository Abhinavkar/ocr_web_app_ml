from djongo import models

class Class(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name

class Document(models.Model):
    pdf = models.FileField(upload_to='pdfs/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'document_collection'
        indexes = [
            models.Index(fields=['pdf'])
        ]
    

    def __str__(self):
        return self.pdf.name

class Image(models.Model):
    image = models.ImageField(upload_to='images/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'image_collection'
        indexes = [
            models.Index(fields= ['uploaded_at']),
            models.Index(fields=['image']), 
        ]

    def __str__(self):
        return self.image.name



class Subject(models.Model):
    name = models.CharField(max_length=255,)
    associated_class = models.ForeignKey(Class, on_delete=models.CASCADE, related_name="subjects")
    class Meta:
        unique_together = ('name', 'associated_class')
        indexes = [
            models.Index(fields=['associated_class', 'name']),  
        ]

    def __str__(self):
        return f"{self.name} ({self.associated_class.name})"
    

class EmbeddingType(models.TextChoices):
    QUESTION = 'question', 'Question'
    ANSWER = 'answer', 'Answer'
class DocumentEmbedding(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    embedding = models.JSONField() 

    class Meta:
        indexes = [
            models.Index(fields=['document'])
        ]
    
class ImageEmbedding(models.Model):
    """
    Store embeddings for questions or answers related to a specific image.
    """
    image = models.ForeignKey(Image, on_delete=models.CASCADE, related_name="embeddings")
    embedding = models.JSONField()
    type = models.CharField(
        max_length=14, 
        choices=EmbeddingType.choices, 
        default=EmbeddingType.QUESTION
    )  

    class Meta:
        indexes = [
            models.Index(fields=['image' , 'type'])
        ]

    def __str__(self):
        return f"{self.type.capitalize()} Embedding for {self.image}"


    
class QuestionAnswerResult(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    question_label = models.CharField(max_length=255)
    question_text = models.TextField()
    best_match_sentence = models.TextField()
    similarity_score = models.FloatField()
    answer_relevance = models.CharField(max_length=255)
    answer_text = models.TextField(null=True, blank=True) 
    embeddings = models.JSONField(null = True,blank=True) 

    def __str__(self):
        return f"Result for {self.question_label} ({self.similarity_score:.2f}%)"

    class Meta:
        verbose_name = "Question-Answer Result"
        verbose_name_plural = "Question-Answer Results"

        indexes = [
            models.Index(fields=['document', 'question_label']), 
            models.Index(fields=['similarity_score']),  
        ]
