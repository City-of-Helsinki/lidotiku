import operator
from functools import reduce

from django.db.models.query import Q
from rest_framework.pagination import CursorPagination, PageNumberPagination
from rest_framework.utils import json
from rest_framework.utils.urls import remove_query_param, replace_query_param
from rest_framework.views import APIView

from .utils import counter_alias_map


class LargeResultsSetPagination(PageNumberPagination):
    page_size = 1000
    page_size_query_param = "page_size"
    max_page_size = 10000

    def get_previous_link(self) -> str | None:
        previous_link = super().get_previous_link()
        if not self.page.has_previous():
            return None
        if self.page.previous_page_number() == 1:
            previous_link = replace_query_param(previous_link, self.page_query_param, 1)
        if "page" in self.request.query_params:
            previous_link = remove_query_param(previous_link, "cursor")
        return previous_link

    def get_next_link(self) -> str | None:
        if not self.page.has_next():
            return None
        if "page" in self.request.query_params:
            return remove_query_param(super().get_next_link(), "cursor")
        return super().get_next_link()


class SmallResultsSetPagination(PageNumberPagination):
    page_size = 100
    page_size_query_param = "page_size"
    max_page_size = 1000


## Code from https://github.com/sonthonaxrk/django-rest-framework/blob/29d8796b1d96cbe77ecd81663ee7afbace0229e0/rest_framework/pagination.py
## Utilizes all ordering fields to determine position instead of just the first field in the ordering list.
class CompoundCursorPagination(CursorPagination):
    def paginate_queryset(self, queryset, request, view=None):
        self.page_size = self.get_page_size(request)
        if not self.page_size:
            return None

        self.base_url = request.build_absolute_uri()
        self.ordering = self.get_ordering(request, queryset, view)

        self.cursor = self.decode_cursor(request)
        if self.cursor is None:
            (offset, reverse, current_position) = (0, False, None)
        else:
            (offset, reverse, current_position) = self.cursor

        # Cursor pagination always enforces an ordering.
        if reverse:
            queryset = queryset.order_by(*self._reverse_ordering(self.ordering))
        else:
            queryset = queryset.order_by(*self.ordering)

        # If we have a cursor with a fixed position then filter by that.
        if current_position is not None:
            current_position_list = json.loads(current_position)
            print(f"List defining the position {current_position_list}")

            q_objects_equals = {}
            q_objects_compare = {}

            for order, position in zip(self.ordering, current_position_list):
                is_reversed = order.startswith("-")
                order_attr = order.lstrip("-")

                q_objects_equals[order] = Q(**{order_attr: position})

                # Test for: (cursor reversed) XOR (queryset reversed)
                if self.cursor.reverse != is_reversed:
                    q_objects_compare[order] = Q(**{(order_attr + "__lt"): position})
                else:
                    q_objects_compare[order] = Q(**{(order_attr + "__gt"): position})

            filter_list = [q_objects_compare[self.ordering[0]]]

            ordering = self.ordering

            # starting with the second field
            for i in range(len(ordering)):
                # The first operands need to be equals
                # the last operands need to be gt
                equals = list(ordering[: i + 2])
                greater_than_q = q_objects_compare[equals.pop()]
                sub_filters = [q_objects_equals[e] for e in equals]
                sub_filters.append(greater_than_q)
                filter_list.append(reduce(operator.and_, sub_filters))

            q_object = reduce(operator.or_, filter_list)
            queryset = queryset.filter(q_object)

        # If we have an offset cursor then offset the entire page by that amount.
        # We also always fetch an extra item in order to determine if there is a
        # page following on from this one.
        results = list(queryset[offset : offset + self.page_size + 1])
        self.page = list(results[: self.page_size])

        # Determine the position of the final item following the page.
        if len(results) > len(self.page):
            has_following_position = True
            following_position = self._get_position_from_instance(
                results[-1], self.ordering
            )
        else:
            has_following_position = False
            following_position = None

        if reverse:
            # If we have a reverse queryset, then the query ordering was in reverse
            # so we need to reverse the items again before returning them to the user.
            self.page = list(reversed(self.page))

            # Determine next and previous positions for reverse cursors.
            self.has_next = (current_position is not None) or (offset > 0)
            self.has_previous = has_following_position
            if self.has_next:
                self.next_position = current_position
            if self.has_previous:
                self.previous_position = following_position
        else:
            # Determine next and previous positions for forward cursors.
            self.has_next = has_following_position
            self.has_previous = (current_position is not None) or (offset > 0)
            if self.has_next:
                self.next_position = following_position
            if self.has_previous:
                self.previous_position = current_position

        # Display page controls in the browsable API if there is more
        # than one page.
        if (self.has_previous or self.has_next) and self.template is not None:
            self.display_page_controls = True

        return self.page

    def get_ordering(self, request, queryset, view):
        """
        Return a tuple of strings, that may be used in an `order_by` method.
        """
        ordering_filters = [
            filter_cls
            for filter_cls in getattr(view, "filter_backends", [])
            if hasattr(filter_cls, "get_ordering")
        ]

        if ordering_filters:
            # If a filter exists on the view that implements `get_ordering`
            # then we defer to that filter to determine the ordering.
            filter_cls = ordering_filters[0]
            filter_instance = filter_cls()
            ordering = filter_instance.get_ordering(request, queryset, view)
            assert ordering is not None, (
                "Using cursor pagination, but filter class {filter_cls} "
                "returned a `None` ordering.".format(filter_cls=filter_cls.__name__)
            )
        else:
            # The default case is to check for an `ordering` attribute
            # on this pagination instance.
            ordering = self.ordering
            assert ordering is not None, (
                "Using cursor pagination, but no ordering attribute was declared "
                "on the pagination class."
            )
            assert "__" not in ordering, (
                "Cursor pagination does not support double underscore lookups "
                "for orderings. Orderings should be an unchanging, unique or "
                'nearly-unique field on the model, such as "-created" or "pk".'
            )

        assert isinstance(
            ordering, (str, list, tuple)
        ), "Invalid ordering. Expected string or tuple, but got {type}".format(
            type=type(ordering).__name__
        )

        if isinstance(ordering, str):
            ordering = (ordering,)

        pk_name = queryset.model._meta.pk.name

        # Always include a unique key to order by
        if not {"-{}".format(pk_name), pk_name, "pk", "-pk"} & set(ordering):
            ordering = tuple(ordering) + (pk_name,)

        return tuple(ordering)

    def _get_position_from_instance(self, instance, ordering):
        fields = []

        for o in ordering:
            field_name = o.lstrip("-")
            if isinstance(instance, dict):
                attr = instance[field_name]
            else:
                attr = getattr(instance, field_name)

            fields.append(str(attr))

        return json.dumps(fields)


class ObservationsCursorPagination(CompoundCursorPagination):
    page_size = 1000
    page_size_query_param = "page_size"
    ordering = [
        "-datetime",
        "counter_id",
        "typeofmeasurement",
        "direction",
        "vehicletype",
    ]
    max_page_size = 10000

    def get_schema_operation_parameters(self, view: APIView) -> list:
        parameters = super().get_schema_operation_parameters(view)

        page_parameter = {
            "name": "page",
            "required": False,
            "in": "query",
            "description": "A page number within the paginated result set. If this parameter is set, it supercedes the cursor parameter and results will be returned as numbered pages.",
            "schema": {"type": "integer"},
        }

        parameters.append(page_parameter)
        return parameters

    def get_ordering(self, request, queryset, view):
        ordering = super().get_ordering(request, queryset, view)
        if "order" in request.query_params:
            fixed_orderings = ["typeofmeasurement", "direction", "vehicletype"]

            order_params = request.query_params.get("order").split(",")
            order_params = [
                counter_alias_map.get(param) if "counter" in param else param
                for param in order_params
            ]

            secondary_ordering = []
            if "counter" in order_params[0] and len(order_params) == 1:
                secondary_ordering = ["-datetime"]
            elif "datetime" in order_params[0] and len(order_params) == 1:
                secondary_ordering = ["counter_id"]
            ordering = order_params + secondary_ordering + fixed_orderings
        return ordering


class ObservationAggregateCursorPagination(CompoundCursorPagination):
    page_size = 1000
    page_size_query_param = "page_size"
    ordering = ["-start_time", "counter_id", "direction"]
    max_page_size = 10000

    def get_schema_operation_parameters(self, view: APIView) -> list:
        parameters = super().get_schema_operation_parameters(view)

        page_parameter = {
            "name": "page",
            "required": False,
            "in": "query",
            "description": "A page number within the paginated result set. If this parameter is set, it supercedes the cursor parameter and results will be returned as numbered pages.",
            "schema": {"type": "integer"},
        }

        parameters.append(page_parameter)
        return parameters
