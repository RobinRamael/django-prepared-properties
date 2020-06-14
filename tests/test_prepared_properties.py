import warnings

import factory
from django.test import TestCase as DjangoTestCase

from test_project.models import Group, Person

warnings.filterwarnings("error", "Getting property")


class GroupFactory(factory.DjangoModelFactory):
    @factory.post_generation
    def with_people_ages(self, create, ages, **kwargs):
        if not create or ages is None:
            return

        for age in ages:
            p = Person(age=age)
            p.save()
            self.people.add(p)

    @factory.post_generation
    def of_size(self, create, size, **kwargs):
        if not create or size is None:
            return

        for _ in range(size):
            p = Person()
            p.save()
            self.people.add(p)

    class Meta:
        model = Group


class ModelAnnotatedPropertyTestCase(DjangoTestCase):
    def test_simple(self):

        group = GroupFactory.create(of_size=3)

        group = Group.objects.annotate_properties(Group.people_count).get()

        self.assertEqual(group.people_count, 3)

    def test_two(self):

        group1 = GroupFactory.create(of_size=3)
        group2 = GroupFactory.create(of_size=5)

        group1, group2 = Group.objects.annotate_properties(Group.people_count).all()

        self.assertEqual(group1.people_count, 3)
        self.assertEqual(group2.people_count, 5)

    def test_dependent(self):

        group = GroupFactory.create(of_size=3)

        group = Group.objects.annotate_properties(Group.is_empty).get()

        self.assertEqual(group.is_empty, False)

    def test_shared_descendant(self):

        group = GroupFactory.create(of_size=3)

        group = Group.objects.annotate_properties(Group.count_times_three).get()

        self.assertEqual(group.count_times_three, 9)

    def test_no_getter(self):

        group = GroupFactory.create(of_size=3)

        group = Group.objects.get()

        with self.assertRaises(AttributeError):
            group.is_empty

    def test_not_annotated(self):

        group = GroupFactory.create(of_size=3)

        with self.assertWarns(UserWarning):
            self.assertEqual(group.people_count, 3)


class PrefetchedPropertyTestCase(DjangoTestCase):
    def test_simple(self):
        group = GroupFactory.create(with_people_ages=[5, 17, 45, 19])

        group = Group.objects.prefetch_properties(Group.children).get()

        self.assertCountEqual([c.age for c in group.children], [5, 17])


class CombinedTestCase(DjangoTestCase):
    def test_simple(self):
        group = GroupFactory.create(with_people_ages=[5, 17, 45, 19])
        group = Group.objects.prepare(Group.children, Group.count_times_three).get()

        self.assertCountEqual([c.age for c in group.children], [5, 17])
        self.assertEqual(group.count_times_three, 3 * 4)

    def test_two(self):
        group1 = GroupFactory.create(with_people_ages=[5, 17, 45, 19])
        group2 = GroupFactory.create(with_people_ages=[5, 17, 9, 45, 19, 31, 35])

        group1 = Group.objects.prepare(Group.children, Group.count_times_three).get(pk=group1.pk)

        group2 = Group.objects.prepare(Group.children, Group.count_times_three).get(pk=group2.pk)

        self.assertCountEqual([c.age for c in group1.children], [5, 17])
        self.assertEqual(group1.count_times_three, 3 * 4)

        self.assertCountEqual([c.age for c in group2.children], [5, 17, 9])
        self.assertEqual(group2.count_times_three, 3 * 7)
