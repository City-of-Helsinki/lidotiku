from rest_framework_csv.renderers import PaginatedCSVRenderer


class FeaturesPaginatedCSVRenderer(PaginatedCSVRenderer):
    def render(self, data, media_type=None, renderer_context=None):
        try:
            data = data["results"]["features"]
        except (KeyError, TypeError):
            pass
        return super().render(data, media_type, renderer_context)
