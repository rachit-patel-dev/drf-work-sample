## Authentication

We are using three types of Authentications:

1. **SimpleJwtAuth:**([def success(self)](./SimpleJwtAuth/views.py#L50))
   - login with token API ([def login(self)](./SimpleJwtAuth/views.py#L95))
   - verify_user with token API ([def verify_user(self)](./SimpleJwtAuth/views.py#L189))
   - sign_up with user details API ([def sign_up(self)](./SimpleJwtAuth/views.py#L243))
   - forgot_password  API ([def forgot_password(self)](./SimpleJwtAuth/views.py#L312))
   - forgot_password  API ([def reset_password(self)](./SimpleJwtAuth/views.py#L371))

2. **TokenAuth:**([def fail(self)](./TokenAuth/views.py#L26))
   - login with token API ([def login(self)](./TokenAuth/views.py#L72))
   - sign_up with user details API ([def sign_up(self)](./TokenAuth/views.py#L46))

3. **SocialAuth:**([def fail(self)](./SocialAuth))
   - Apple authentication API ([def login(self)](./SocialAuth/apple_auth.py#L16))
   - Google authentication API ([def sign_up(self)](./SocialAuth/google_auth.py#L21))
