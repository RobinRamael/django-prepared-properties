from django.db import models
from django.db.models import BooleanField, Case, Count, F, OuterRef, Q, Subquery, Value, When

from prepared_properties import (
    AnnotatedProperty,
    PrefetchedProperty,
    PropertiedQueryset,
    annotated_property,
)


class Person(models.Model):
    groups = models.ManyToManyField("test_project.Group", related_name="people")

    age = models.PositiveIntegerField(default=0)


class Group(models.Model):
    objects = models.Manager.from_queryset(PropertiedQueryset)()

    @annotated_property(
        lambda: Subquery(
            Person.groups.through.objects.filter(group=OuterRef("pk"))
            .values("group")
            .annotate(count=Count("person"))
            .values("count")
        )
    )
    def people_count(self):
        return self.people.count()

    @annotated_property(F("people_count") * Value(2))
    def count_times_two(self):
        return self.people.count() * 2

    is_empty = AnnotatedProperty(
        Case(
            When(people_count=0, then=Value(True)),
            default=Value(False),
            output_field=BooleanField(),
        ),
        depends_on=["people_count"],
    )

    count_times_three = AnnotatedProperty(
        F("people_count") + F("count_times_two"), depends_on=["people_count", "count_times_two"],
    )

    children = PrefetchedProperty("people", Person.objects.filter(age__lte=18))
