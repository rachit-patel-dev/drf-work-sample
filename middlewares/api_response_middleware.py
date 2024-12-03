from focus_power.infrastructure.translator.services import CustomTranslator


class CustomResponseMiddleware:
    """
    CustomResponseMiddleware class is responsible for processing the response returned by the view function. It applies custom translation to the response data based on the request headers.

    Attributes:
    - get_response (function): The view function that will be called to handle the request.
    - custom_translator (CustomTranslator): An instance of the CustomTranslator class used for translating the response data.

    Methods:
    - __call__(self, request): Handles the request and returns the response.
    - process_template_response(self, request, response): Processes the template response and applies custom translation to the response data.

    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.custom_translator = CustomTranslator()

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_template_response(self, request, response):
        """
        Processes the template response and applies custom translation to the response data.

        Parameters:
        - request (HttpRequest): The HTTP request object.
        - response (HttpResponse): The HTTP response object.

        Returns:
        - HttpResponse: The processed HTTP response object.

        Description:
        This method is responsible for processing the template response returned by the view function. It first checks if the request path contains "superadmin" or "custom_admin". If it does, the method returns the response as is without any modifications. Otherwise, it retrieves the language from the request headers, with a default value of "en" if not provided. It then uses the custom_translator instance to translate the response data, specifically the "message" key, to the target language. The translated data is then assigned back to the response object and returned.

        Note:
        - The custom_translator instance is initialized in the constructor of the CustomResponseMiddleware class.

        Example:
        middleware = CustomResponseMiddleware(get_response) response = middleware.process_template_response(request, response)

        """
        if "superadmin" in request.path:
            return response
        if "custom_admin" in request.path:
            return response
        language = request.headers.get("Language", "en").lower()
        response.data = self.custom_translator.translate_response(
            translating_data=response.data,
            translation_keys=["message"],
            target_language=language,
        )
        return response
