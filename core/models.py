from django.db import models


class InstagramPost(models.Model):
    instagram_id = models.CharField(max_length=100, unique=True)
    permalink = models.URLField()
    caption = models.TextField(blank=True)
    published_at = models.DateTimeField()

    class Meta:
        ordering = ['-published_at', '-pk']

    def __str__(self):
        return self.caption[:80] or self.instagram_id


class Sender(models.Model):
    name = models.CharField(max_length=120)
    email = models.EmailField(unique=True)

    class Meta:
        ordering = ['name', 'email']

    def save(self, *args, **kwargs):
        self.email = self.email.strip().lower()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.name} <{self.email}>'


class Idea(models.Model):
    sender = models.ForeignKey(Sender, null=True, blank=True, on_delete=models.PROTECT, related_name='ideas')
    title = models.CharField(max_length=120)
    song = models.CharField(max_length=200)
    description = models.TextField(max_length=3000)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=12, default='new', choices=[('new', 'New'), ('reviewed', 'Reviewed'), ('inspired', 'Inspired a post')])

    class Meta:
        ordering = ['sender__name', 'sender__email', '-created_at']

    def __str__(self):
        return self.title


class IdeaImage(models.Model):
    idea = models.ForeignKey(Idea, on_delete=models.CASCADE, related_name='images')
    # Small private references live in the database, surviving Render redeploys.
    data = models.BinaryField()
