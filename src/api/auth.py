from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    Security,
    BackgroundTasks,
    Request,
)
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from src.schemas.contacts import UserCreate, Token, User, RequestEmail
from src.services.auth import (
    create_access_token,
    Hash,
    get_email_from_token,
    get_current_moderator_user,
    get_current_admin_user,
)
from src.services.users import UserService
from src.db.connection import get_db
from src.services.email import send_email

router = APIRouter(prefix="/auth", tags=["auth"])


# Реєстрація користувача
@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    background_tasks: BackgroundTasks,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Реєстрація нового користувача.

    Якщо користувач з таким email або іменем вже існує, то буде викидано помилка з кодом 409.

    Після успішної реєстрації відправляється електронне повідомлення на вказану електронну адресу з підтвердженням реєстрації.

    :param user_data: дані користувача
    :param background_tasks: задачі, що виконуються у фоновому тлі
    :param request: запит на реєстрацію
    :param db: сесія до бази даних
    :return: новий користувач
    :raises HTTPException: якщо користувач з таким email або іменем вже існує
    """
    user_service = UserService(db)

    email_user = await user_service.get_user_by_email(user_data.email)
    if email_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Користувач з таким email вже існує",
        )

    username_user = await user_service.get_user_by_username(user_data.username)
    if username_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Користувач з таким іменем вже існує",
        )
    user_data.password = Hash().get_password_hash(user_data.password)
    new_user = await user_service.create_user(user_data)
    background_tasks.add_task(
        send_email, new_user.email, new_user.username, request.base_url, new_user.role
    )

    return new_user


# Логін користувача
@router.post("/login", response_model=Token)
async def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    """
    Логін користувача.

    Якщо логін або пароль не вірні, то буде викидано помилка з кодом 401.

    Якщо електронна адреса не підтверджена, то буде викидано помилка з кодом 401.

    :param form_data: дані форми логіна
    :param db: сесія до бази даних
    :return: токен доступу
    :raises HTTPException: якщо логін або пароль не вірні або електронна адреса не підтверджена
    """
    user_service = UserService(db)
    user = await user_service.get_user_by_username(form_data.username)
    if not user or not Hash().verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неправильний логін або пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.confirmed:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Електронна адреса не підтверджена",
        )

    access_token = await create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/confirmed_email/{token}")
async def confirmed_email(token: str, db: Session = Depends(get_db)):
    """
    Confirmation of email address.

    :param token: confirmation token
    :param db: session to the database
    :return: message about the confirmation result
    :raises HTTPException: if the verification token is invalid or the user is not found
    """
    email = await get_email_from_token(token)
    user_service = UserService(db)
    user = await user_service.get_user_by_email(email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Verification error"
        )
    if user.confirmed:
        return {"message": "Ваша електронна пошта вже підтверджена"}
    await user_service.confirmed_email(email)
    return {"message": "Електронну пошту підтверджено"}


@router.post("/request_email")
async def request_email(
    body: RequestEmail,
    background_tasks: BackgroundTasks,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Request to send a confirmation email to the user.

    If the user is not found or the email address is not confirmed, the function will send a confirmation email to the user.

    If the user is found and the email address is confirmed, the function will return a message indicating that the email address is already confirmed.

    :param body: data of the request
    :param background_tasks: task queue to run tasks in the background
    :param request: request object
    :param db: session to the database
    :return: message about the confirmation result
    :raises HTTPException: if the verification token is invalid or the user is not found
    """
    user_service = UserService(db)
    user = await user_service.get_user_by_email(body.email)
    if not user:
        raise HTTPException(status_code=404, detail="User with this email not found")

    if user.confirmed:
        return {"message": "Ваша електронна пошта вже підтверджена"}
    if user:
        background_tasks.add_task(
            send_email, user.email, user.username, request.base_url
        )
    return {"message": "Перевірте свою електронну пошту для підтвердження"}


# Перший маршрут - доступний для всіх
@router.get("/public")
def read_public():
    """
    Public route, available for all users.

    :return: a message indicating that this is a public route
    :rtype: dict
    """
    return {"message": "Це публічний маршрут, доступний для всіх"}


# Другий маршрут - для модераторів та адміністраторів
@router.get("/moderator")
def read_moderator(
    current_user: User = Depends(get_current_moderator_user),
):
    """
    Маршрут для модераторів та адміністраторів.

    Оповідає, що цей маршрут доступний лише для модераторів та адміністраторів.

    :param current_user: поточний користувач, отриманий завдяки залежності get_current_moderator_user
    :return: повідомлення з привітанням для модераторів та адміністраторів
    :rtype: dict
    """
    return {
        "message": f"Вітаємо, {current_user.username}! Це маршрут для модераторів та адміністраторів"
    }


# Третій маршрут - тільки для адміністраторів
@router.get("/admin")
def read_admin(current_user: User = Depends(get_current_admin_user)):
    """
    Маршрут для адміністраторів.

    Оповідає, що цей маршрут доступний лише для адміністраторів.

    :param current_user: поточний користувач, отриманий завдяки залежності get_current_admin_user
    :return: повідомлення з привітанням для адміністраторів
    :rtype: dict
    """
    return {"message": f"Вітаємо, {current_user.username}! Це адміністративний маршрут"}
