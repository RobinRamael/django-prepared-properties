Django Prepared Properties
==========================

Declarative annotations and prefetches for Django models.

We often find ourselves writing a lot of quite complex annotations and
prefetches. While these are used across the project, the logic that defines them
is kind of hidden in a queryset method (or more of them, if the annotations
rely on eachother). If there's a default/naive implementation as a property,
that logic is held in a completely different place. Using these annotations
requires you to call each of those queryset methods, which quickly becomes a bit
of a mess.

This package attempts to solve this by allowing you to define annotations and
prefetches as 'prepared' properties, so you can add them to you querysets by
referencing the class attribute. The queryset `prepare` method resolves
annotation dependencies and builds the correct queryset for you.

Requires python 3.6 and django 2.2. It probably works on django 3, but I haven't
tried it (PRs welcome <3)

Installation
------------

```
pip install prepared-properties
```

Annotated Properties
--------------------

To add an annotated property, you simply need to pass in the
annotation into either the `AnnotatedProperty` class or `annotated_property`
decorator. You can then prepare it by calling `prepare(Model.propery_name)`
on the queryset.

To avoid cyclic references to models in the annotation (eg. by referring to the
model the property is on in the annotation), you can also pass  the annoation as
a lambda, which will be evaluated when the queryset is annotated.

When you use the decorator, the body of the method you decorate  will be used
when the annotation is not present. Using it will emit a warning advising you
to use the `prepare` querset method.


```python

from django.db.models import Model, Sum, OuterRef, Manager
from prepared_properties import annotated_property, AnnotatedProperty, PropertiedQuerySet

class Book(Model):
    page_number = models.PositiveIntegerField()

class Author(Model):
    objects = Manager.from_queryset(PropertiedQuerySet)()

    pages_written = AnnotatedProperty(
        Subquery(
            Book.objects.filter(author=OuterRef("pk"))
            .values("author")
            .annotate(pages_written=Sum("page_number"))
            .values("page_number")
        )
    )

    # ... or with a default getter:

    @annotated_property(
        Subquery(
            Book.objects.filter(author=OuterRef("pk"))
            .values("author")
            .annotate(pages_written=Sum("page_number"))
            .values("page_number")
        )
    )
    def pages_written(self):
        # a warning is emitted before this is run.
        return self.book_set.aggregate(pages_written=Sum("page_number"))[
            "pages_written"
        ]

for author in Author.objects.prepare(Author.pages_written):
    print(author.pages_written)

```

Dependent Annotated  Properties
---------------------

Often, annotations might depend on other annotations being present. If you pass
an array of property names into the property constructor or decorator, all
dependent annotatations will also be added to the queryset when you prepare the
property using the other one:

```python

class Author(Model):
    objects = Manager.from_queryset(PropertiedQuerySet)()

    pages_written = AnnotatedProperty(
        Subquery(
            Book.objects.filter(author=OuterRef("pk"))
            .values("author")
            .annotate(pages_written=Sum("page_number"))
            .values("page_number")
        )
    )

    twice_the_pages_written = AnnotatedProperty(
        F("pages_written") * Value(2), depends_on=["pages_written"]
    )

```

Calling `Book.objects.prepare(Author.twice_the_pages_written)` will now also
annotate `Book.pages_written`. This allows you to change the underlying
implementation of the annotations without changing queryset definitions
everywhere. Neato.


Prefetched properties
---------------------

A similar, yet less feature-complete thing can be done for prefetches:

```python

class Author(Model):
    objects = Manager.from_queryset(PropertiedQuerySet)()
    short_books = PrefetchedProperty(
        "book_set", Book.objects.filter(page_number__lt=100)
    )


for author in Author.objects.prepare(Author.pages_written):
    print(author.short_books)

```

Since prefetches can't depend on eachother the `depends_on` kwarg is not
supported for prefetches. The default getter is also not supported for now
(django checks wether the attribute is present using `hasattr` before doing the
prefetch, which would always execute the naive getter.)

As you can see, the prepare method doesn't care wether you pass it prefetches or
annotations, so a property can change from annotation to prefetch or vice versa
without changing the queryset definition or the model interface!


