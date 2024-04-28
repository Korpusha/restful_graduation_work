from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


class Customer(AbstractUser):
    purse = models.IntegerField(default=10000)


class CinemaHallModel(models.Model):
    name = models.CharField(max_length=120, unique=True)
    size = models.PositiveIntegerField(validators=[MinValueValidator(20)])

    def __str__(self):
        return self.name


class SessionModel(models.Model):
    halls = models.ForeignKey(CinemaHallModel, on_delete=models.CASCADE, null=True)
    ticket_price = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    start_date = models.TimeField(blank=True, null=True)
    end_date = models.TimeField(blank=True, null=True)
    date = models.DateField(blank=True, null=True)
    available_seats = models.PositiveIntegerField(null=True)

    def __str__(self):
        return f'{self.halls} ({self.ticket_price})'


class TicketModel(models.Model):
    customers = models.ForeignKey(Customer, on_delete=models.CASCADE, null=True)
    sessions = models.ForeignKey(SessionModel, on_delete=models.CASCADE, null=True)
    amount = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(1000000)])
    bought_at = models.DateTimeField(auto_now_add=True, null=True)
