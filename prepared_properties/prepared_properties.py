import warnings
from abc import ABC
from collections import deque

from django.db.models import Prefetch, QuerySet


class NamedDescriptor(ABC):
    def __init__(self, field_name=None):
        # the field name can be set explicitly using the constructor, but by
        # default we use the name of the attr this descriptor is set on, as
        # seen in __set_name__ below.
        self.field_name = field_name
        self._never_used = True
        self._was_prepared = False

    def __set_name__(self, owner, field_name):
        # called when the property is bound to the class. using
        # this method we can derive a field name for a property without a getter
        # if needed
        if not self.field_name:
            self.field_name = field_name

        self.owner = owner

    def __get__(self, instance, owner):
        #  if we refer to this class with Model.field_name, we mean this actual
        #  descriptor object:
        if not instance:
            return self

        try:
            return getattr(instance, "_properties_cache", {})[self.field_name]
        except KeyError:
            if not self.getter:
                raise AttributeError(
                    f"Property {self} was not bound to {instance} and no getter was provided."
                )

            warnings.warn(
                f"Getting property {self}. "
                "Use qs.prepare to make this more efficient."
            )
            return self.getter.__call__(instance)

    # called when ModelIterable setattrs the annotations onto the model
    def __set__(self, instance, value):
        if not hasattr(instance, "_properties_cache"):
            instance._properties_cache = {}

        instance._properties_cache[self.field_name] = value
        self._was_prepared = True

    def __str__(self):
        return f"<{self.__class__.__name__}({self.owner.__name__}.{self.field_name})>"


class AnnotatedProperty(NamedDescriptor):
    def __init__(
        self, annotation, getter=None, field_name=None, depends_on=None
    ):
        super().__init__(
            field_name=field_name or getattr(getter, "__name__", None),
        )
        self.getter = getter

        self._annotation = annotation
        self._depends_on = depends_on or []

    @property
    def annotation(self):
        # we allow the annotation to be callable to be able to avoid cyclic
        # references (you can't refer to the same model as the one you're
        # annotating as the decorator is called before the class is created.)
        if callable(self._annotation):
            return self._annotation()

        return self._annotation

    @property
    def depends_on(self):
        return (
            getattr(self.owner, prop_name) for prop_name in self._depends_on
        )


class _AnnotatedPropertyFactory:
    """
    decorator that produces an annotated_property with a default getter
    """

    def __init__(self, subquery, depends_on=None):
        self.subquery = subquery
        self.depends_on = depends_on

    def __call__(self, getter):
        return AnnotatedProperty(self.subquery, getter, self.depends_on)


annotated_property = _AnnotatedPropertyFactory


class PrefetchedProperty(NamedDescriptor):
    def __init__(self, m2m_name, queryset, getter=None, field_name=None):
        super().__init__(field_name=field_name)
        self.m2m_name = m2m_name
        self.queryset = queryset
        self.getter = getter


def resolution_order(properties):
    props_to_annotate = []
    property_st = deque(properties)

    # we walk through the tree breadth first and
    # add all encountered props to a list if they weren't
    # already in there.
    while len(property_st) > 0:
        prop = property_st.popleft()

        if prop not in props_to_annotate:
            props_to_annotate.append(prop)

        for dependent_prop in prop.depends_on:
            property_st.appendleft(dependent_prop)

    # since a prop higher up in the tree will be encountered first,
    # and the deepest dependencies will be encountered last,
    # reversing this list will give us the correct resolution order.
    # neat.
    return reversed(props_to_annotate)


class PropertiedQueryset(QuerySet):
    def prepare(self, *properties):
        return self.annotate_properties(
            *[p for p in properties if isinstance(p, AnnotatedProperty)]
        ).prefetch_properties(
            *[p for p in properties if isinstance(p, PrefetchedProperty)]
        )

    def annotate_properties(self, *properties):
        qs = self
        # annotations can depend on eachother and get checked immediately when
        # `.annotate` is called, so we need to sort them correctly.
        for prop in resolution_order(properties):
            qs = qs.annotate(**{prop.field_name: prop.annotation})

        return qs

    def prefetch_properties(self, *properties):
        qs = self
        for prop in properties:
            qs = qs.prefetch_related(
                Prefetch(prop.m2m_name, prop.queryset, to_attr=prop.field_name)
            )

        return qs
